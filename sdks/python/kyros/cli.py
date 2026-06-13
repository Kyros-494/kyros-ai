import argparse
import os
import sys

import httpx

from kyros.client import KyrosClient
from kyros.exceptions import KyrosError


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Kyros AI CLI — command line interface for persistent agent memory"
    )
    parser.add_argument("--api-key", help="Kyros API key (default: KYROS_API_KEY env var)")
    parser.add_argument("--base-url", help="Kyros API base URL (default: KYROS_BASE_URL env var)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # status command
    subparsers.add_parser("status", help="Check server liveness and dependency status")

    # remember command
    remember_parser = subparsers.add_parser("remember", help="Store a new episodic memory")
    remember_parser.add_argument("--agent", required=True, help="Agent ID")
    remember_parser.add_argument("--content", required=True, help="Text to remember")
    remember_parser.add_argument(
        "--role", default="user", help="Message role (user/assistant/system)"
    )
    remember_parser.add_argument("--session", help="Session ID for grouping")

    # recall command
    recall_parser = subparsers.add_parser("recall", help="Recall memories using semantic search")
    recall_parser.add_argument("--agent", required=True, help="Agent ID")
    recall_parser.add_argument("--query", required=True, help="Search query")
    recall_parser.add_argument("-k", type=int, default=5, help="Number of results to retrieve")

    # tenant-create command
    tenant_parser = subparsers.add_parser(
        "tenant-create", help="Create a new tenant (requires master admin token)"
    )
    tenant_parser.add_argument("--name", required=True, help="Tenant name")
    tenant_parser.add_argument("--email", required=True, help="Contact email")
    tenant_parser.add_argument(
        "--admin-token", help="Master admin token (default: KYROS_ADMIN_TOKEN env var)"
    )

    # audit command
    audit_parser = subparsers.add_parser(
        "audit", help="Verify cryptographic integrity of an agent's memory"
    )
    audit_parser.add_argument("--agent", required=True, help="Agent ID")

    # summarize command
    summarize_parser = subparsers.add_parser(
        "summarize", help="Get a compressed summary/history card for an agent"
    )
    summarize_parser.add_argument("--agent", required=True, help="Agent ID")

    # mcp command
    mcp_parser = subparsers.add_parser("mcp", help="Start the Model Context Protocol (MCP) server")
    mcp_parser.add_argument("action", choices=["start"], default="start", nargs="?", help="Action to perform")

    args = parser.parse_args()

    api_key = args.api_key or os.getenv("KYROS_API_KEY")
    base_url = args.base_url or os.getenv("KYROS_BASE_URL")

    if args.command not in ("tenant-create", "mcp") and not api_key:
        print(
            "Error: No API key provided. Set KYROS_API_KEY environment variable or pass --api-key.",
            file=sys.stderr
        )
        sys.exit(1)

    try:
        if args.command == "status":
            try:
                r = httpx.get(f"{base_url}/health/ready")
                if r.status_code == 200:
                    status_data = r.json()
                    print("Status: ONLINE")
                    print(f"Environment: {status_data.get('environment', 'unknown')}")
                    print("Checks:")
                    for service, state in status_data.get("checks", {}).items():
                        print(f"  - {service}: {state.upper()}")
                else:
                    print(f"Status: DEGRADED (HTTP {r.status_code})")
                    print(r.text)
            except Exception as e:
                print(f"Status: OFFLINE (Cannot connect to {base_url})", file=sys.stderr)
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        elif args.command == "remember":
            client = KyrosClient(api_key=api_key, base_url=base_url)
            remember_res = client.remember(
                agent_id=args.agent,
                content=args.content,
                role=args.role,
                session_id=args.session
            )
            print("Memory stored successfully.")
            print(f"ID: {remember_res.memory_id}")

        elif args.command == "recall":
            client = KyrosClient(api_key=api_key, base_url=base_url)
            recall_res = client.recall(agent_id=args.agent, query=args.query, k=args.k)
            if not recall_res.results:
                print("No matching memories found.")
            else:
                for idx, item in enumerate(recall_res.results, 1):
                    fresh = getattr(item, "freshness", 1.0)
                    print(f"\n[{idx}] Content: {item.content}")
                    print(f"    Relevance: {item.relevance_score:.2f} | Freshness: {fresh:.2f}")

        elif args.command == "tenant-create":
            admin_token = (
                args.admin_token
                or os.getenv("KYROS_ADMIN_TOKEN")
                or os.getenv("KYROS_JWT_SECRET_KEY")
            )
            if not admin_token:
                print(
                    "Error: No admin token provided. Pass --admin-token "
                    "or set KYROS_ADMIN_TOKEN env var.",
                    file=sys.stderr
                )
                sys.exit(1)

            headers = {
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
            payload = {"name": args.name, "email": args.email}

            r = httpx.post(f"{base_url}/v1/admin/tenants", json=payload, headers=headers)
            if r.status_code == 200:
                data = r.json()
                print("Tenant created successfully!")
                print(f"Tenant ID: {data['tenant_id']}")
                print(f"Name: {data['name']}")
                print(f"Plan: {data['plan'].upper()}")
                print("="*60)
                print(f"API KEY: {data['api_key']}")
                print("="*60)
                print(
                    "WARNING: Copy this API key now. It will never be "
                    "displayed in plaintext again."
                )
            else:
                print(f"Failed to create tenant (HTTP {r.status_code}):", file=sys.stderr)
                print(r.text, file=sys.stderr)
                sys.exit(1)

        elif args.command == "audit":
            client = KyrosClient(api_key=api_key, base_url=base_url)
            audit_res = client.audit_integrity(agent_id=args.agent)
            if audit_res.get("is_intact"):
                print(" Cryptographic Integrity Scan: INTACT (No tampering detected)")
            else:
                print(" Cryptographic Integrity Scan: CORRUPTED")
                print(f"Tampered records: {audit_res.get('tampered_count')}")
                for record in audit_res.get("tampered_memories", []):
                    print(f"  - ID: {record}")

        elif args.command == "summarize":
            client = KyrosClient(api_key=api_key, base_url=base_url)
            summarize_res = client.summarise(agent_id=args.agent)
            print("="*60)
            print(f"Agent Memory Summary: {args.agent}")
            print("="*60)
            print(summarize_res.summary)
            print("-"*60)
            print(
                f"Memories compressed: {summarize_res.memory_count} | "
                f"Ratio: {summarize_res.compression_ratio:.2%}"
            )

        elif args.command == "mcp":
            if args.action == "start" or not args.action:
                from kyros.mcp import run_server
                run_server()

    except KyrosError as e:
        print(f"Kyros API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
