# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-21

### 🎉 Initial Release

First public release of agent-benchmark - a comprehensive framework for evaluating AI model performance on Hermes Agent tasks.

### ✨ Features

**Benchmark Framework**
- Complete benchmark runner for comparing AI models on coding and agent tasks
- Support for all 13 OpenCode Go models (DeepSeek, Qwen, Kimi, GLM, MiMo, MiniMax)
- AI-powered code review using DeepSeek V4 Pro as reviewer
- 4-dimensional scoring system (correctness, efficiency, completeness, style)
- Rate limiting and retry logic for API calls
- Async execution with httpx

**Task Library (70 tasks)**
- 10 classic coding tasks (algorithms, data structures, debugging)
- 60 Hermes-specific agent tasks across 6 categories:
  - Tool Use (10 tasks): terminal, file ops, browser, API calls
  - Instruction Following (10 tasks): multi-step, constraints, formatting
  - Memory Management (10 tasks): extraction, summarization, updates
  - Planning (10 tasks): decomposition, estimation, strategy
  - Error Recovery (10 tasks): debugging, handling failures
  - Code Review (10 tasks): finding bugs, security, performance

**Testing & Quality**
- 26 unit tests with pytest (all passing)
- Test coverage for core modules: scorer, task_loader, config, api_client
- Ruff linting and formatting
- Type hints throughout codebase
- Google-style docstrings

**Security & Governance**
- MIT License
- CODE_OF_CONDUCT.md (Contributor Covenant 2.0)
- CONTRIBUTING.md (comprehensive guidelines)
- SECURITY.md (vulnerability reporting policy)
- No hardcoded secrets (all via environment variables)
- Secret scanning and push protection enabled
- Dependabot for automated dependency updates

**CI/CD**
- GitHub Actions CI pipeline (Python 3.11 & 3.12)
- Automated testing, linting, and security scanning
- Dependabot auto-merge for patch updates
- Branch protection rules enforced

### 🔧 Technical Details

**Requirements**
- Python 3.11+
- httpx >= 0.25.0
- typer >= 0.9.0
- rich >= 13.0.0
- pyyaml >= 6.0
- jinja2 >= 3.1.0

**API Integration**
- OpenCode Go API (https://opencode.ai/zen/go/v1)
- Supports both OpenAI-style (/chat/completions) and Anthropic-style (/messages) endpoints
- Automatic endpoint routing based on model

**Configuration**
- YAML-based configuration (config.yaml)
- Environment variable support for API keys
- Flexible scoring weights

### 📊 What's Next

- Run full benchmark across all 13 models
- Generate model performance rankings
- Optimize Hermes Agent model configuration
- Add more task categories
- Web dashboard for visualization

### 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](https://github.com/pbedynski-priv/agent-benchmark/blob/main/CONTRIBUTING.md) for guidelines.

### 📝 License

MIT License - see [LICENSE](https://github.com/pbedynski-priv/agent-benchmark/blob/main/LICENSE) file for details.

[0.1.0]: https://github.com/pbedynski-priv/agent-benchmark/releases/tag/v0.1.0
