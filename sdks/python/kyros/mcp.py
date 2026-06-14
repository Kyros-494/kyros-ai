"""Model Context Protocol (MCP) server implementation for Kyros AI.

Allows Agentic IDEs (like Cursor, Windsurf, or Cline) to consume Kyros memory as tools.
"""

from __future__ import annotations

import json
import sys
import traceback
from typing import Any

from kyros.client import KyrosClient
from kyros.exceptions import KyrosError


def log_error(msg: str) -> None:
    """Log an error message to stderr (since stdout is reserved for JSON-RPC)."""
    sys.stderr.write(f"[Kyros MCP] {msg}\n")
    sys.stderr.flush()


def handle_initialize(params: dict[str, Any]) -> dict[str, Any]:
    """Handle the initialize request."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "kyros-mcp",
            "version": "0.1.1"
        }
    }


def handle_tools_list() -> dict[str, Any]:
    """Expose available Kyros memory tools to the agentic client."""
    return {
        "tools": [
            {
                "name": "remember",
                "description": "Store an episodic memory/experience in the long-term memory store.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "Unique identifier of the agent or project namespace."
                        },
                        "content": {
                            "type": "string",
                            "description": "The exact message, experience, or observation to commit to memory."
                        },
                        "role": {
                            "type": "string",
                            "description": "Optional role (e.g. user, assistant, system) indicating who generated the content."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Optional session ID to group multiple memories."
                        }
                    },
                    "required": ["agent_id", "content"]
                }
            },
            {
                "name": "recall",
                "description": "Recall past experiences, conversations, or facts semantically from Kyros memory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "Unique identifier of the agent or project namespace."
                        },
                        "query": {
                            "type": "string",
                            "description": "Semantic query or question indicating what memories to retrieve."
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of relevant memory records to return (default: 5)."
                        }
                    },
                    "required": ["agent_id", "query"]
                }
            },
            {
                "name": "store_fact",
                "description": "Store a structured semantic fact triple (subject, predicate, object value).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "Unique identifier of the agent or project namespace."
                        },
                        "subject": {
                            "type": "string",
                            "description": "The subject of the fact (e.g., 'user', 'system')."
                        },
                        "predicate": {
                            "type": "string",
                            "description": "The relationship predicate (e.g., 'prefers', 'hates', 'knows')."
                        },
                        "value": {
                            "type": "string",
                            "description": "The object value of the relationship."
                        }
                    },
                    "required": ["agent_id", "subject", "predicate", "value"]
                }
            }
        ]
    }


def handle_tools_call(params: dict[str, Any], client: KyrosClient) -> dict[str, Any]:
    """Execute the memory tools requested by the Agentic IDE."""
    name = params.get("name")
    arguments = params.get("arguments", {})

    if name == "remember":
        agent_id = arguments.get("agent_id")
        content = arguments.get("content")
        role = arguments.get("role")
        session_id = arguments.get("session_id")
        res = client.remember(
            agent_id=agent_id,
            content=content,
            role=role,
            session_id=session_id
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Successfully stored memory in Kyros. Memory ID: {res.memory_id}"
                }
            ]
        }

    elif name == "recall":
        agent_id = arguments.get("agent_id")
        query = arguments.get("query")
        k = int(arguments.get("k", 5))
        res = client.recall(agent_id=agent_id, query=query, k=k)
        if not res.results:
            text = "No relevant memories found in Kyros."
        else:
            text = "\n".join(
                f"- {item.content} (Relevance: {item.relevance_score:.2f})"
                for item in res.results
            )
        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }

    elif name == "store_fact":
        agent_id = arguments.get("agent_id")
        subject = arguments.get("subject")
        predicate = arguments.get("predicate")
        value = arguments.get("value")
        res = client.store_fact(
            agent_id=agent_id,
            subject=subject,
            predicate=predicate,
            value=value
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Successfully stored semantic fact triple. Fact ID: {res.fact_id}"
                }
            ]
        }

    else:
        raise ValueError(f"Unknown tool name: {name}")


def run_server() -> None:
    """Run the stdio JSON-RPC loop for Model Context Protocol (MCP)."""
    log_error("Starting Kyros MCP server...")

    import os
    base_url = os.getenv("KYROS_BASE_URL") or "http://localhost:8000"
    api_key = os.getenv("KYROS_API_KEY") or "mk_live_default_dev_key_123456"

    try:
        client = KyrosClient(api_key=api_key, base_url=base_url)
        log_error(f"Connected to Kyros server at {base_url}")
    except Exception as e:
        log_error(f"Initialization failed: {e}. Verify Kyros server is running at {base_url}.")
        sys.exit(1)

    for line in sys.stdin:
        if not line.strip():
            continue

        req_id = None
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            # Skip notifications (no message id)
            if req_id is None:
                log_error(f"Received notification: {method}")
                continue

            result = None
            if method == "initialize":
                result = handle_initialize(params)
            elif method == "tools/list":
                result = handle_tools_list()
            elif method == "tools/call":
                result = handle_tools_call(params, client)
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
                continue

            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        except Exception as e:
            log_error(f"Exception processing request: {e}\n{traceback.format_exc()}")
            if req_id is not None:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {e}"
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    run_server()
