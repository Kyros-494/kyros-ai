# Kyros AI Enterprise Setup and Integration Guide

This guide describes the complete procedure for initializing the Kyros AI Persistent Memory server, configuring the environment, and integrating the engine with agent frameworks and Model Context Protocol (MCP) clients.

---

## 1. Prerequisites and System Requirements

Ensure the deployment environment satisfies the following baseline specifications:
*   **Operating System:** Windows 10/11, macOS, or Linux.
*   **Containerization:** Docker Engine 20.10+ and Docker Compose v2.0+.
*   **Runtime Environments:** Python 3.10+ (specifically required for SDK and CLI tools) and Node.js 18+ (for TypeScript installations).
*   **Network Access:** Outbound HTTPS connectivity for model API providers (OpenAI, Gemini, Mistral) and port 8000 exposure for local REST API routing.

---

## 2. Directory Navigation and Initial Configuration

1. Open a terminal or PowerShell session and navigate to the project directory:
   ```bash
   cd "C:\Users\jayas\OneDrive\Documents\Desktop\hi\kyros-ai"
   ```
2. Replicate the example configuration file to establish local environment variables:
   ```bash
   cp .env.example .env
   ```
3. Edit the `.env` file to supply target LLM API keys:
   *   `OPENAI_API_KEY`
   *   `GEMINI_API_KEY`
   *   `MISTRAL_API_KEY`

---

## 3. Virtual Environment Initialization

Isolate project dependencies by activating the provided Python virtual environment:

### PowerShell (Windows)
```powershell
.\kyros-server\Scripts\Activate.ps1
```

### Bash (macOS/Linux)
```bash
source kyros-server/bin/activate
```

Upon activation, your shell prompt will display the `(kyros-server)` prefix.

---

## 4. Dependency Installation

Install required packages, including the Kyros SDK, model libraries, and agent frameworks:
```bash
pip install crewai crewai-tools litellm httpx pydantic
pip install -e sdks/python
```

Verify the installation of the CLI executable:
```bash
kyros status
```

---

## 5. Execution of Framework Demonstrations

### CrewAI Demonstration
The `crewai_demo.py` script illustrates persistent episodic memory storage and semantic recall. Launch the script:
```bash
python crewai_demo.py
```
When prompted:
1. Select the target LLM provider (OpenAI, Gemini, or Mistral).
2. Input the associated API key.
3. Observe how the agent commits conversational facts to Kyros and retrieves context during subsequent turns.

---

## 6. Configuring Model Context Protocol (MCP) for AI IDEs

Kyros contains a built-in Model Context Protocol (MCP) server, allowing IDE clients (such as Cursor, Windsurf, or VS Code Cline) to interact with memory stores natively.

### Launching the MCP Server
Start the server listening on stdio:
```bash
kyros mcp start
```

### Cline / Roo Code Settings Configuration
Add the configuration block below to your global MCP settings file:
```json
{
  "mcpServers": {
    "kyros-memory": {
      "command": "python",
      "args": ["-m", "kyros.mcp"],
      "env": {
        "KYROS_API_KEY": "mk_live_default_dev_key_123456",
        "KYROS_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

---

## 7. Administrative APIs (Tenant & Key Management)

Kyros exposes developer endpoints to automate workspace provisioning and configuration.

### Programmatic Agent Registration
Create a new agent profile (project namespace) explicitly:
```bash
curl -X POST http://localhost:8000/v1/admin/agents \
  -H "Authorization: Bearer mk_live_default_dev_key_123456" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "production-finance-agent",
    "display_name": "Finance Assistant",
    "metadata": {"department": "operations"}
  }'
```

### Programmatic API Key Rotation
Rotate the API key for an existing tenant workspace:
```bash
curl -X POST http://localhost:8000/v1/admin/tenants/target-tenant-uuid/rotate-key \
  -H "Authorization: Bearer admin-secret-token" \
  -H "Content-Type: application/json"
```

---

## 8. Troubleshooting and Diagnostics

*   **ImportError: No module named 'crewai':** Ensure the virtual environment is active before starting scripts. Re-run `pip install crewai`.
*   **Database Connection Refused:** Verify that the Postgres and Redis Docker containers are fully healthy by running `docker compose ps`. Check if the Postgres database port is mapped correctly (default development mapping is 5433).
*   **API Authentication Failures:** Confirm that the headers `X-API-Key` or `Authorization: Bearer <key>` match the API key hash recorded in the database.
