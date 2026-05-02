# Contributing to Kyros

Thank you for your interest in contributing to Kyros! We welcome contributions from everyone and are grateful for even the smallest of improvements.

This guide will help you get started with contributing to the project. Please take a moment to review this document to make the contribution process easy and effective for everyone involved.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit Message Convention](#commit-message-convention)
- [Branch Naming Convention](#branch-naming-convention)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Code Review Process](#code-review-process)
- [Testing Requirements](#testing-requirements)
- [Documentation Requirements](#documentation-requirements)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)
- [License](#license)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [conduct@kyros.ai](mailto:conduct@kyros.ai).

## Getting Started

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher (for TypeScript SDK)
- **Docker**: Latest version
- **Docker Compose**: Latest version
- **Git**: Latest version

### Initial Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/kyros-ai.git
   cd kyros-ai
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/Kyros-494/kyros-ai.git
   ```
4. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```
5. **Fill in required values** in `.env`
6. **Start the development stack**:
   ```bash
   make dev
   ```
7. **Run the test suite** to verify setup:
   ```bash
   make test
   ```

### Keeping Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Merge upstream changes into your main branch
git checkout main
git merge upstream/main

# Push updates to your fork
git push origin main
```

## Development Workflow

### Server Development

```bash
# Install server dependencies
cd server && uv sync

# Run linting and type checks
make lint

# Run tests with coverage
make test

# Format code
make format

# Run specific test file
cd server && uv run pytest tests/integration/test_semantic_memory.py -v

# Run tests with specific marker
cd server && uv run pytest -m "not slow" -v
```

### Python SDK Development

```bash
# Install SDK dependencies
cd sdks/python && uv sync

# Run SDK tests
make sdk-test-python

# Build SDK
cd sdks/python && uv build
```

### TypeScript SDK Development

```bash
# Install SDK dependencies
cd sdks/typescript && npm install

# Run SDK tests
make sdk-test-ts

# Build SDK
cd sdks/typescript && npm run build

# Lint SDK
cd sdks/typescript && npm run lint
```

### Website Development

```bash
# Install website dependencies
cd website && npm install

# Run development server
cd website && npm run dev

# Build for production
make website-build

# Lint website
make website-lint
```

### Database Migrations

```bash
# Create a new migration
make migrate-new msg="add new feature"

# Apply migrations
make migrate

# Rollback last migration
make migrate-down
```

## Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This leads to more readable messages that are easy to follow when looking through the project history.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries
- **ci**: Changes to CI configuration files and scripts
- **build**: Changes that affect the build system or external dependencies

### Scope

The scope should be the name of the component affected:
- `server`: Server-side changes
- `sdk-python`: Python SDK changes
- `sdk-ts`: TypeScript SDK changes
- `website`: Website changes
- `docs`: Documentation changes
- `api`: API changes
- `db`: Database changes
- `proxy`: Proxy server changes

### Subject

- Use the imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize the first letter
- No period (.) at the end
- Limit to 72 characters or less

### Body (Optional)

- Use the imperative, present tense
- Include motivation for the change and contrast with previous behavior
- Wrap at 72 characters

### Footer (Optional)

- Reference issues: `Fixes #123`, `Closes #456`, `Refs #789`
- Breaking changes: `BREAKING CHANGE: description`

### Examples

```
feat(server): add memory compression endpoint

Implement LLM-based memory compression with support for
multiple providers (OpenAI, Anthropic, Gemini).

Closes #234
```

```
fix(sdk-python): handle connection timeout gracefully

Add retry logic with exponential backoff for network errors.

Fixes #567
```

```
docs(readme): update installation instructions

Add troubleshooting section for common setup issues.
```

## Branch Naming Convention

Use descriptive branch names that follow this pattern:

```
<type>/<short-description>
```

### Types

- `feature/`: New features
- `fix/`: Bug fixes
- `docs/`: Documentation changes
- `refactor/`: Code refactoring
- `test/`: Test additions or modifications
- `chore/`: Maintenance tasks

### Examples

```
feature/add-memory-compression
fix/connection-timeout-handling
docs/update-api-reference
refactor/simplify-auth-logic
test/add-integration-tests
chore/update-dependencies
```

### Rules

- Use lowercase letters
- Use hyphens to separate words
- Keep it short but descriptive
- Avoid special characters

## Pull Request Guidelines

### Before Submitting

1. **Create an issue first** for significant changes to discuss the approach
2. **Keep PRs focused** — one feature or fix per PR
3. **Update your branch** with the latest main branch
4. **Run the full test suite** and ensure all tests pass
5. **Run linting and formatting** to ensure code quality
6. **Update documentation** if you're changing functionality
7. **Add tests** for any new behavior

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] Documentation updated (if applicable)
- [ ] Tests added/updated (if applicable)
- [ ] All tests pass locally (`make ci`)
- [ ] No new warnings introduced
- [ ] Commit messages follow convention
- [ ] PR title follows convention
- [ ] PR description is clear and complete

### PR Title Format

Follow the same convention as commit messages:

```
<type>(<scope>): <description>
```

Examples:
- `feat(server): add memory compression endpoint`
- `fix(sdk-python): handle connection timeout`
- `docs(readme): update installation guide`

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Motivation and Context
Why is this change required? What problem does it solve?

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran and how to reproduce them.

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Related Issues
Fixes #(issue number)
```

### PR Size Guidelines

- **Small PRs** (< 200 lines): Preferred, easier to review
- **Medium PRs** (200-500 lines): Acceptable, may take longer to review
- **Large PRs** (> 500 lines): Should be split into smaller PRs when possible

If your PR is large, consider:
1. Breaking it into multiple smaller PRs
2. Providing extra context in the description
3. Adding inline comments to guide reviewers

### Draft PRs

Use draft PRs for:
- Work in progress that you want feedback on
- Changes that are not ready for review
- Experimental features

Convert to a regular PR when ready for review.

## Code Review Process

### For Contributors

1. **Be responsive** to review comments
2. **Address all feedback** or explain why you disagree
3. **Request re-review** after making changes
4. **Be patient** — reviewers are volunteers
5. **Be respectful** in all interactions

### Review Timeline

- **Initial response**: Within 48 hours
- **Full review**: Within 5 business days
- **Follow-up reviews**: Within 2 business days

### Approval Requirements

- **1 approval** required for minor changes (docs, tests, small fixes)
- **2 approvals** required for major changes (new features, breaking changes)
- **Maintainer approval** required for security-related changes

### After Approval

- PRs will be merged by maintainers
- Squash and merge is the default strategy
- Your commits will be combined into a single commit
- The PR title becomes the commit message

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 80% for new code
- **Preferred coverage**: 90%+ for critical paths
- **Required coverage**: 100% for security-related code

### Test Types

#### Unit Tests

- Test individual functions and classes
- Mock external dependencies
- Fast execution (< 1 second per test)
- Located in `tests/unit/`

Example:
```python
def test_memory_creation():
    memory = Memory(content="test", agent_id="agent-1")
    assert memory.content == "test"
    assert memory.agent_id == "agent-1"
```

#### Integration Tests

- Test multiple components together
- Use real database (test database)
- May be slower (< 5 seconds per test)
- Located in `tests/integration/`

Example:
```python
async def test_memory_roundtrip(client):
    # Create memory
    response = await client.post("/api/v1/memory/semantic", json={
        "agent_id": "agent-1",
        "content": "test memory"
    })
    assert response.status_code == 201
    
    # Retrieve memory
    memory_id = response.json()["id"]
    response = await client.get(f"/api/v1/memory/{memory_id}")
    assert response.status_code == 200
    assert response.json()["content"] == "test memory"
```

#### End-to-End Tests

- Test complete user workflows
- Use real services (database, Redis, etc.)
- Slower execution (< 30 seconds per test)
- Located in `tests/e2e/`

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
cd server && uv run pytest tests/integration/test_semantic_memory.py -v

# Run tests with coverage report
cd server && uv run pytest --cov=kyros --cov-report=html

# Run tests matching a pattern
cd server && uv run pytest -k "test_memory" -v

# Run tests with specific marker
cd server && uv run pytest -m "not slow" -v
```

### Test Markers

- `@pytest.mark.slow`: Tests that take > 5 seconds
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.security`: Security-related tests

### Writing Good Tests

1. **Use descriptive names**: `test_memory_creation_with_valid_data`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Test one thing**: Each test should verify one behavior
4. **Use fixtures**: Reuse common setup code
5. **Mock external services**: Don't depend on external APIs
6. **Clean up**: Ensure tests don't leave side effects

## Documentation Requirements

### Code Documentation

#### Python Docstrings

Use Google-style docstrings:

```python
def create_memory(content: str, agent_id: str) -> Memory:
    """Create a new memory for an agent.
    
    Args:
        content: The memory content to store.
        agent_id: The unique identifier of the agent.
        
    Returns:
        The created Memory object with generated ID.
        
    Raises:
        ValueError: If content is empty or agent_id is invalid.
        
    Example:
        >>> memory = create_memory("User prefers Python", "agent-1")
        >>> print(memory.id)
        'mem_abc123'
    """
    if not content:
        raise ValueError("Content cannot be empty")
    return Memory(content=content, agent_id=agent_id)
```

#### TypeScript JSDoc

```typescript
/**
 * Create a new memory for an agent.
 * 
 * @param content - The memory content to store
 * @param agentId - The unique identifier of the agent
 * @returns Promise resolving to the created Memory object
 * @throws {ValidationError} If content is empty or agentId is invalid
 * 
 * @example
 * ```typescript
 * const memory = await createMemory("User prefers Python", "agent-1");
 * console.log(memory.id); // 'mem_abc123'
 * ```
 */
async function createMemory(content: string, agentId: string): Promise<Memory> {
  if (!content) {
    throw new ValidationError("Content cannot be empty");
  }
  return await api.post("/memory", { content, agentId });
}
```

### Documentation Files

Update these files when making changes:

- **README.md**: For user-facing changes
- **API Documentation**: For API changes
- **SDK Documentation**: For SDK changes
- **CHANGELOG.md**: For all changes (maintainers will help)

### Documentation Checklist

- [ ] Public functions have docstrings
- [ ] Complex logic has inline comments
- [ ] README updated (if user-facing change)
- [ ] API docs updated (if API change)
- [ ] Examples added (if new feature)
- [ ] Migration guide added (if breaking change)

## Reporting Bugs

We use GitHub Issues to track bugs. Before creating a bug report, please check if the issue already exists.

### Before Submitting a Bug Report

1. **Check the documentation** — the answer might be there
2. **Search existing issues** — someone might have reported it already
3. **Try the latest version** — the bug might be fixed
4. **Verify it's reproducible** — can you consistently reproduce it?

### How to Submit a Bug Report

Open an issue using the [bug report template](https://github.com/Kyros-494/kyros-ai/issues/new?template=bug_report.md).

Include:

- **Clear title**: Summarize the issue in one line
- **Description**: Detailed description of the bug
- **Steps to reproduce**: Numbered steps to reproduce the behavior
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Screenshots**: If applicable, add screenshots
- **Environment**:
  - OS: [e.g., Ubuntu 22.04, macOS 13.0, Windows 11]
  - Python version: [e.g., 3.11.5]
  - Kyros version: [e.g., 0.1.0]
  - Docker version: [e.g., 24.0.5]
- **Additional context**: Any other relevant information
- **Logs**: Relevant log output (use code blocks)

### Bug Report Example

```markdown
**Title**: Memory retrieval fails with large result sets

**Description**
When querying memories with more than 1000 results, the API returns a 500 error.

**Steps to Reproduce**
1. Create 1500 memories for agent-1
2. Query all memories: `GET /api/v1/memory/agent-1/semantic`
3. Observe 500 error

**Expected Behavior**
API should return paginated results or handle large result sets gracefully.

**Actual Behavior**
API returns 500 Internal Server Error with message "Database connection timeout"

**Environment**
- OS: Ubuntu 22.04
- Python: 3.11.5
- Kyros: 0.1.0
- Docker: 24.0.5

**Logs**
```
ERROR: Database query timeout after 30s
Traceback (most recent call last):
  ...
```
```

## Feature Requests

We welcome feature requests! Before submitting, please:

1. **Check existing issues** — someone might have requested it already
2. **Consider if it fits** — does it align with project goals?
3. **Think about implementation** — how might it work?

### How to Submit a Feature Request

Open an issue using the [feature request template](https://github.com/Kyros-494/kyros-ai/issues/new?template=feature_request.md).

Include:

- **Clear title**: Summarize the feature in one line
- **Problem statement**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives considered**: What other approaches did you consider?
- **Use cases**: Real-world scenarios where this would be useful
- **Additional context**: Mockups, examples, references

### Feature Request Example

```markdown
**Title**: Add support for image embeddings

**Problem Statement**
Currently, Kyros only supports text memories. Users want to store and retrieve memories based on images (screenshots, diagrams, photos).

**Proposed Solution**
Add a new memory type `visual` that:
1. Accepts image uploads (PNG, JPEG, WebP)
2. Generates embeddings using CLIP or similar model
3. Enables semantic search across images
4. Supports multimodal queries (text + image)

**Alternatives Considered**
1. Store images as base64 in text memories (inefficient)
2. Use external image storage service (adds complexity)

**Use Cases**
1. AI assistant remembers user's screenshots
2. Design tool recalls similar visual patterns
3. Support bot finds relevant diagrams

**Additional Context**
- OpenAI's CLIP model: https://github.com/openai/CLIP
- Similar feature in Mem0: https://docs.mem0.ai/features/images
```

## Community

### Getting Help

- **Documentation**: [docs.kyros.ai](https://docs.kyros.ai)
- **GitHub Discussions**: [Ask questions](https://github.com/Kyros-494/kyros-ai/discussions)
- **GitHub Issues**: [Report bugs](https://github.com/Kyros-494/kyros-ai/issues)
- **Email**: [support@kyros.ai](mailto:support@kyros.ai)

### Stay Updated

- **Watch the repository** for notifications
- **Star the repository** to show support
- **Follow releases** for new versions

## Recognition

Contributors will be recognized in:

- **CHANGELOG.md**: Listed in release notes
- **README.md**: Contributors section
- **GitHub**: Contributor graph and statistics

Significant contributors may be invited to join the core team.

## License

By contributing to Kyros, you agree that your contributions will be licensed under the Apache 2.0 License for the server core and MIT License for the SDKs.

### Contributor License Agreement (CLA)

You retain copyright to your contributions, but you grant Kyros-494 the right to use, modify, and distribute your contributions under the project's licenses. You represent that you have the legal authority to grant this license.

For enterprise inquiries or custom licensing, please contact us at [license@kyros.ai](mailto:license@kyros.ai).

### Open Core Model

- **Server Core**: Apache 2.0 (free to self-host and modify)
- **SDKs & Integrations**: MIT (free to use in any project)
- **Enterprise Modules**: Commercial License (contact for details)

*See individual `LICENSE` files in the repository for full license text.*
