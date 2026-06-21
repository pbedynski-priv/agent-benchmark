# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please use one of these methods:

1. **GitHub Security Advisories** (preferred): Use the [GitHub Security Advisories feature](https://github.com/pbedynski-priv/agent-benchmark/security/advisories/new) to privately report the vulnerability.

2. **Email**: Contact the maintainer directly through their GitHub profile.

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix timeline**: Depends on severity
  - Critical: Immediate fix
  - High: Within 1 week
  - Medium: Within 1 month
  - Low: Next release

### Security Best Practices for Users

1. **API Keys**: Never commit API keys to the repository. Use environment variables or `.env` files (already in `.gitignore`).

2. **Dependencies**: Keep dependencies updated. We use Dependabot for automated updates.

3. **Isolated Execution**: When running benchmarks that execute generated code, always use isolated environments (Docker containers, VMs, or sandboxes).

4. **Rate Limiting**: The tool includes rate limiting to prevent API abuse. Don't disable it in production.

5. **Input Validation**: All task definitions are validated on load. Don't modify YAML task files from untrusted sources.

## Security Features

- ✅ No hardcoded secrets (all via environment variables)
- ✅ `.env` files excluded via `.gitignore`
- ✅ Rate limiting on API calls
- ✅ Input validation on task loading
- ✅ No execution of untrusted code by default (review-only mode)
- ✅ Dependency scanning via Dependabot

## Security Updates

Security updates will be released as patch versions and announced via GitHub Security Advisories.
