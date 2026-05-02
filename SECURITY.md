# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes    |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Email **security@kyros.ai** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations

You will receive a response within **48 hours**. We aim to release a patch within **7 days** for critical issues.

## Scope

In scope:
- Authentication bypass or API key exposure
- Tenant isolation failures (one tenant reading another's data)
- Memory poisoning via the API
- SQL injection or RCE in the server
- Cryptographic weaknesses in the Merkle integrity system

Out of scope:
- Vulnerabilities in self-hosted infrastructure you control
- Social engineering
- Denial of service via resource exhaustion (configure rate limiting at your reverse proxy)

## Disclosure Policy

We follow coordinated disclosure. Once a fix is released, we will publish a security advisory on GitHub.
