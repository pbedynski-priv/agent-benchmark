# Agent Benchmark — Hermes Model Optimization

A benchmark framework for evaluating AI model performance on **Hermes Agent** tasks. Compare all 13 OpenCode Go models across 70 benchmark tasks to find the optimal model configuration for Hermes Agent roles (main, delegation, auxiliary).

## Purpose

Hermes Agent uses multiple AI models for different roles — conversations, delegation, code review, vision, etc. This tool answers:

> **Which model performs best for each Hermes role at the lowest cost?**

By running standardized tasks through all available models and using DeepSeek V4 Pro as an AI reviewer, we get data-driven model selection instead of guesswork.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Benchmark Runner                       │
├──────────┬──────────────┬──────────────┬────────────────┤
│  Task    │   API        │   Reviewer   │   Scorer       │
│  Loader  │   Client     │   Engine     │   Engine       │
│  (YAML)  │   (httpx)    │   (V4 Pro)   │   (4 dims)    │
└──────────┴──────────────┴──────────────┴────────────────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
  70 tasks    13 models     JSON scores    Rankings +
  (6 hermes     via OpenCode   per model    recommendations
   categories)  Go API         per task
```

## Task Library — 70 Tasks

### Coding Tasks (10)
Classic software engineering challenges:
- **Algorithms** (4): LRU Cache, Binary Search, Dijkstra, Merge Sort
- **Data Structures** (2): Hash Map, Priority Queue
- **Debugging** (4): Off-by-one, Null Pointer, Race Condition, Memory Leak

### Hermes-Specific Tasks (60)
Tasks designed to evaluate capabilities critical for Hermes Agent:

| Category | Tasks | What It Tests |
|----------|-------|---------------|
| **Tool Use** | 10 | Terminal commands, file ops, browser actions, API calls |
| **Instruction Following** | 10 | Multi-step workflows, constraints, formatting rules |
| **Memory Management** | 10 | Fact extraction, summarization, preference detection |
| **Planning** | 10 | Task decomposition, estimation, deployment strategy |
| **Error Recovery** | 10 | Debugging failures, handling timeouts, permission errors |
| **Code Review** | 10 | Finding bugs, security issues, performance problems |

## Models — All 13 OpenCode Go

| Tier | Models | Input/Output Cost |
|------|--------|-------------------|
| **Reasoning** | deepseek-v4-pro, mimo-v2.5-pro, qwen3.7-max | $1.74-2.50 / $3.48-7.50 |
| **Balanced** | qwen3.7-plus, qwen3.6-plus, kimi-k2.6, kimi-k2.7, glm-5.1, glm-5.2 | $0.40-1.40 / $1.60-4.40 |
| **Fast/Cheap** | deepseek-v4-flash, mimo-v2.5, minimax-m2.7, minimax-m3 | $0.14-0.30 / $0.28-1.20 |

## Scoring

Reviewer model (**DeepSeek V4 Pro**) evaluates each response on 4 dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Correctness | 40% | Does it produce correct results? |
| Efficiency | 25% | Time and space complexity |
| Completeness | 20% | Are all requirements met? |
| Style | 15% | Code conventions and readability |

Each dimension scored 0-10, weighted to produce final score (max 1.0).

## Quick Start

```bash
# Clone
git clone https://github.com/pbedynski-priv/agent-benchmark.git
cd agent-benchmark

# Install
pip install -e .

# Set API key (or it reads from Hermes ~/.hermes/.env automatically)
export OPENCODE_GO_API_KEY="your-key"

# Quick validation test (3 models × 5 tasks, ~5 min)
python quick_test.py

# Full benchmark (13 models × 70 tasks, ~2-4 hours)
python run_hermes_benchmark.py
```

## Project Structure

```
agent-benchmark/
├── src/code_benchmark/          # Core framework
│   ├── api_client.py            # OpenCode Go API (OpenAI + Anthropic routing)
│   ├── task_loader.py           # YAML task parser
│   ├── reviewer.py              # AI reviewer (DeepSeek V4 Pro)
│   ├── scorer.py                # Weighted scoring engine
│   ├── runner.py                # Benchmark orchestration
│   ├── reporter.py              # JSON/Markdown/terminal output
│   ├── cli.py                   # CLI interface (typer)
│   └── config.py                # Configuration loader
├── tasks/                       # 70 benchmark tasks
│   ├── algorithms/              # 4 coding tasks
│   ├── data-structures/         # 2 coding tasks
│   ├── debugging/               # 4 coding tasks
│   ├── hermes/                  # 60 Hermes-specific tasks
│   │   ├── tool-use/            # Terminal, file, browser, API
│   │   ├── instruction/         # Multi-step, constraints, formatting
│   │   ├── memory/              # Extraction, summarization, updates
│   │   ├── planning/            # Decomposition, estimation, strategy
│   │   ├── error-recovery/      # Debugging, failure handling
│   │   ├── code-review/         # Bug finding, security, performance
│   │   └── index.yaml           # Task registry
│   └── index.yaml               # Top-level task index
├── docs/
│   └── benchmark-tool-plan.md   # Comprehensive design doc (1,073 lines)
├── config.yaml                  # Benchmark configuration
├── quick_test.py                # Quick validation script
├── run_hermes_benchmark.py      # Full benchmark runner
├── generate_hermes_tasks.py     # Task generation script
├── HERMES_BENCHMARK.md          # Hermes-specific design doc
├── BENCHMARK_STATUS.md          # Implementation summary
├── FIXES.md                     # Known issues and solutions
└── pyproject.toml               # Project metadata
```

## Expected Outcomes

After running the full benchmark, you get:

1. **Model rankings** per task category
2. **Optimal model assignments** for each Hermes role:
   - Main model (conversations) — best instruction following + memory
   - Delegation model (subagents) — best planning + tool use at lowest cost
   - Auxiliary models — right model for each specific task type
3. **Cost analysis** — current vs optimized configuration
4. **Performance baseline** for future model comparisons

**Expected savings**: 20-40% cost reduction with equal or better quality.

## Configuration

Edit `config.yaml`:
```yaml
api:
  base_url: https://opencode.ai/zen/go/v1
  api_key_env: OPENCODE_GO_API_KEY

models:
  candidates:
    - qwen3.7-plus
    - deepseek-v4-flash
    - kimi-k2.6
  reviewer: deepseek-v4-pro

scoring:
  weights:
    correctness: 0.40
    efficiency: 0.25
    completeness: 0.20
    style: 0.15
```

## Tech Stack

- **Python 3.11** + httpx (async HTTP)
- **YAML** task definitions
- **Rich** terminal output
- **OpenCode Go API** (OpenAI-compatible)
- **DeepSeek V4 Pro** as reviewer model

## Links

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — The AI agent this benchmarks
- [OpenCode Go](https://opencode.ai) — API provider for all 13 models
- [Comprehensive Design Plan](docs/benchmark-tool-plan.md) — Full architecture doc

## License

MIT
