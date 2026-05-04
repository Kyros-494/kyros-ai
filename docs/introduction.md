# Introduction to Kyros

## Overview

Kyros is a persistent memory operating system designed specifically for AI agents. It provides a comprehensive solution for storing, retrieving, and managing memories across multiple dimensions, enabling AI agents to maintain context, learn from past interactions, and make informed decisions based on historical data.

## What is Kyros?

Kyros is an open-source memory management system that acts as a persistent memory layer for AI agents. Unlike traditional databases or vector stores, Kyros is purpose-built for AI applications with features specifically designed to handle the unique requirements of agent memory:

- **Multi-dimensional Memory**: Support for episodic (conversations), semantic (facts), and procedural (workflows) memory types
- **Temporal Awareness**: Built-in memory decay based on Ebbinghaus forgetting curves
- **Integrity Verification**: Cryptographic proofs using SHA-256 and Merkle trees
- **Causal Reasoning**: Track cause-effect relationships between memories
- **Belief Propagation**: Automatic confidence updates across related facts
- **Framework Integration**: Native support for LangChain, LlamaIndex, AutoGen, and CrewAI

## Why Use Kyros?

### The Problem

Modern AI agents face several challenges when managing memory:

1. **Context Loss**: Agents forget previous interactions when context windows are exceeded
2. **No Temporal Awareness**: Traditional storage doesn't account for memory decay over time
3. **Lack of Structure**: Unstructured memory makes it difficult to reason about relationships
4. **No Integrity Guarantees**: No way to verify that memories haven't been tampered with
5. **Framework Lock-in**: Memory solutions are often tied to specific frameworks

### The Solution

Kyros addresses these challenges through:

**Structured Memory Types**
- Episodic memory for conversations and actions
- Semantic memory for facts and knowledge
- Procedural memory for workflows and skills

**Temporal Intelligence**
- Ebbinghaus decay curves model natural forgetting
- Freshness scores indicate memory staleness
- Category-specific decay rates

**Integrity and Trust**
- SHA-256 content hashing
- Merkle tree proofs for batch verification
- Immutable audit logs

**Advanced Reasoning**
- Causal graph tracking
- Belief propagation for confidence updates
- Semantic edge relationships

**Framework Agnostic**
- REST API accessible from any language
- Official SDKs for Python and TypeScript
- Pre-built integrations for popular frameworks

## Key Concepts

### Memory Types

**Episodic Memory**
Stores sequential experiences, conversations, and actions. Each episodic memory includes:
- Content (text, action, observation)
- Timestamp
- Importance score
- Session grouping
- Metadata

**Semantic Memory**
Stores facts as subject-predicate-object triples with confidence scores:
- Subject: The entity
- Predicate: The relationship
- Object: The value
- Confidence: Belief strength (0.0 to 1.0)

**Procedural Memory**
Stores workflows, procedures, and skills:
- Name and description
- Task type classification
- Step-by-step instructions
- Success rate tracking
- Execution statistics

### Memory Decay

Kyros implements Ebbinghaus forgetting curves to model natural memory decay:

```
freshness = base_retention * e^(-decay_rate * time_elapsed)
```

Different memory categories have different decay rates:
- Conversations: Faster decay
- Facts: Slower decay
- Skills: Minimal decay

### Integrity Proofs

Every memory includes cryptographic integrity proofs:

**Content Hash**
- SHA-256 hash of memory content
- Detects any tampering

**Merkle Tree**
- Batch verification of multiple memories
- Efficient integrity checking

**Audit Log**
- Immutable record of all changes
- Cryptographic chain of custody

### Causal Reasoning

Kyros tracks cause-effect relationships:
- Memory A caused Memory B
- Causal chains for explanation
- Counterfactual reasoning support

### Belief Propagation

When facts are updated, confidence propagates:
- Related facts are updated automatically
- Contradiction detection
- Confidence decay over semantic edges

## Architecture Overview

### Components

**API Server (FastAPI)**
- RESTful API endpoints
- Authentication and authorization
- Request validation
- Background task processing

**Storage Layer**
- PostgreSQL with pgvector extension
- Redis for caching
- S3 for archival (optional)

**Intelligence Layer**
- Decay engine
- Integrity verification
- Belief propagation
- Causal reasoning
- Memory compression

**ML Layer**
- Embedding generation (sentence-transformers)
- Dual embedding support
- Cross-language translation

### Data Flow

1. **Storage**: Client sends memory to API
2. **Embedding**: Content is embedded using ML models
3. **Storage**: Memory stored in PostgreSQL with vector
4. **Indexing**: Vector indexed for similarity search
5. **Caching**: Hot data cached in Redis
6. **Intelligence**: Background tasks process decay, integrity, etc.

### Deployment Architecture

**Single Instance**
- API server
- PostgreSQL database
- Redis cache
- Suitable for development and small deployments

**Scaled Deployment**
- Multiple API servers (load balanced)
- PostgreSQL with read replicas
- Redis cluster
- Suitable for production

**Cloud Native**
- Kubernetes deployment
- Managed databases (RDS, Cloud SQL)
- Managed Redis (ElastiCache, Redis Cloud)
- Auto-scaling
- Suitable for enterprise

## Use Cases

### Conversational AI

**Problem**: Chatbots lose context between sessions

**Solution**: Store conversation history in episodic memory
- Recall relevant past conversations
- Maintain user preferences
- Track conversation topics
- Session-based grouping

### Knowledge Management

**Problem**: AI agents can't maintain a knowledge base

**Solution**: Store facts in semantic memory
- Subject-predicate-object triples
- Confidence scores
- Automatic contradiction detection
- Belief propagation

### Workflow Automation

**Problem**: Agents can't learn from past executions

**Solution**: Store procedures in procedural memory
- Match tasks to procedures
- Track success rates
- Learn from outcomes
- Optimize over time

### Multi-Agent Systems

**Problem**: Agents can't share knowledge

**Solution**: Shared memory with tenant isolation
- Multiple agents per tenant
- Shared knowledge base
- Individual episodic memories
- Collaborative learning

### Personal AI Assistants

**Problem**: Assistants forget user preferences

**Solution**: Long-term memory storage
- User preferences
- Past interactions
- Learned behaviors
- Personalization



## Getting Started Roadmap

### Step 1: Installation (5 minutes)

Choose your deployment method:
- Docker Compose (recommended for testing)
- Kubernetes (recommended for production)
- Manual installation

### Step 2: SDK Setup (5 minutes)

Install the SDK for your language:
- Python: `pip install kyros-sdk`
- TypeScript: `npm install kyros-sdk`

### Step 3: First Memory (10 minutes)

Store and recall your first memory:
- Initialize client
- Store episodic memory
- Recall memories
- Verify results

### Step 4: Explore Features (30 minutes)

Try different memory types:
- Episodic memory (conversations)
- Semantic memory (facts)
- Procedural memory (workflows)

### Step 5: Framework Integration (30 minutes)

Integrate with your framework:
- LangChain
- LlamaIndex
- AutoGen
- CrewAI

### Step 6: Production Deployment (varies)

Deploy to production:
- Configure environment variables
- Set up monitoring
- Configure backups
- Scale as needed

## Core Principles

### 1. Simplicity

Kyros provides a simple, intuitive API that abstracts complex memory management:
- RESTful API design
- Type-safe SDKs
- Clear documentation
- Minimal configuration

### 2. Reliability

Built for production use with enterprise-grade reliability:
- Comprehensive testing
- Error handling
- Health checks
- Graceful degradation

### 3. Performance

Optimized for low latency and high throughput:
- Connection pooling
- Redis caching
- Async operations
- Batch processing

### 4. Security

Security-first design with multiple layers of protection:
- API key authentication
- Row-level security
- Integrity proofs
- Audit logging

### 5. Extensibility

Designed to grow with your needs:
- Plugin architecture
- Custom embeddings
- Framework integrations
- API extensibility

## Technical Specifications

### Supported Platforms

- **Operating Systems**: Linux, macOS, Windows
- **Databases**: PostgreSQL 16+ with pgvector
- **Cache**: Redis 7+
- **Languages**: Python 3.11+, TypeScript 5+
- **Frameworks**: LangChain, LlamaIndex, AutoGen, CrewAI

### Performance Characteristics

- **Latency**: <50ms p95 for memory operations
- **Throughput**: 1000+ requests/second (single instance)
- **Concurrency**: 100+ concurrent connections
- **Vector Search**: <100ms for 10k+ memories
- **Scalability**: Horizontal scaling supported

### Resource Requirements

**Minimum (Development)**
- CPU: 2 cores
- RAM: 4 GB
- Storage: 10 GB

**Recommended (Production)**
- CPU: 4+ cores
- RAM: 8+ GB
- Storage: 50+ GB SSD

**Enterprise (High Scale)**
- CPU: 8+ cores
- RAM: 16+ GB
- Storage: 100+ GB SSD
- Load balancer
- Database replicas

## Community and Support

### Documentation

- **Quickstart Guide**: Get started in 5 minutes
- **Concepts**: Understand core concepts
- **API Reference**: Complete API documentation
- **SDK Guides**: Language-specific guides
- **Deployment**: Self-hosting instructions

### Community Resources

- **GitHub**: Source code and issue tracking
- **Discussions**: Community Q&A
- **Examples**: Sample applications
- **Blog**: Technical articles and updates

### Contributing

Kyros is open source and welcomes contributions:
- Bug reports
- Feature requests
- Pull requests
- Documentation improvements
- Community support

### License

- **Server**: Apache License 2.0
- **SDKs**: MIT License
- **Documentation**: CC BY 4.0

## Next Steps

1. **Read the Quickstart**: Get up and running in 5 minutes
2. **Understand Concepts**: Learn about memory types and features
3. **Choose Your SDK**: Python or TypeScript
4. **Deploy**: Self-host or use managed service
5. **Integrate**: Connect with your framework
6. **Build**: Create your AI application

## Conclusion

Kyros provides a comprehensive, production-ready solution for AI agent memory management. With support for multiple memory types, temporal awareness, integrity verification, and advanced reasoning capabilities, Kyros enables AI agents to maintain context, learn from experience, and make informed decisions.

Whether you're building a chatbot, knowledge management system, workflow automation, or multi-agent system, Kyros provides the memory infrastructure you need to succeed.

Get started today with the quickstart guide and join the growing community of developers building the next generation of AI applications with Kyros.
