# Kyros Python SDK

Python client library for the Kyros AI Memory System.

## Installation

```bash
pip install kyros-sdk
```

## Quick Start

```python
from kyros import KyrosClient

# Initialize client
client = KyrosClient(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)

# Store a memory
memory = client.remember(
    agent_id="my-agent",
    content="User prefers dark mode",
    importance=0.8
)

# Recall memories
results = client.recall(
    agent_id="my-agent",
    query="What are the user's preferences?",
    k=5
)

for result in results:
    print(f"Memory: {result.content}")
```

## Features

- **Episodic Memory**: Store and recall experiences
- **Semantic Memory**: Store facts and knowledge
- **Procedural Memory**: Store procedures and workflows
- **Type-safe**: Full type hints and Pydantic models
- **Async Support**: Async/await compatible

## Documentation

For full documentation, visit [docs.kyros.ai](https://docs.kyros.ai)

## License

Apache 2.0
