# Code Benchmark - Model Code Quality Benchmark Tool

A comprehensive tool for comparing AI code generation models across multiple dimensions including correctness, efficiency, style, and security.

## Overview

Code Benchmark evaluates AI code generation models by:
- Sending standardized coding tasks to multiple models
- Collecting and executing generated code in sandboxed Docker containers
- Reviewing code quality using a dedicated reviewer model (DeepSeek V4 Pro)
- Scoring across 8 dimensions: correctness, efficiency, completeness, style, error handling, documentation, innovation, and security
- Generating detailed comparison reports

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd code-benchmark

# Install dependencies
pip install -e .

# Or with uv
uv pip install -e .
```

## Configuration

1. Set your API key (optional - will fallback to Hermes .env file):
```bash
export OPENCODE_GO_API_KEY="your-api-key-here"
```

Note: If the environment variable is not set or truncated, the tool will automatically read the API key from your Hermes installation at `~/.hermes/.env`.

2. Edit `config.yaml` to customize models, scoring weights, and execution settings.

## Quick Start

```bash
# List available tasks
code-benchmark tasks list

# Run a benchmark
code-benchmark run --models qwen3.7-plus,deepseek-v4-flash --tasks algorithms

# Generate a report
code-benchmark report --run-id <run-id>

# Compare models
code-benchmark compare --run-ids <run-id-1>,<run-id-2>
```

## Available Commands

| Command | Description |
|---------|-------------|
| `run` | Execute a benchmark run with specified models and tasks |
| `report` | Generate a report from a previous benchmark run |
| `compare` | Compare results across multiple benchmark runs |
| `tasks list` | List all available benchmark tasks |

## Task Categories

- **algorithms/** - Classic algorithm implementation tasks (LRU Cache, Binary Search, Dijkstra, Merge Sort)
- **debugging/** - Bug identification and fixing tasks (Off-by-one, Null Pointer, Race Condition, Memory Leak)
- **data-structures/** - Data structure implementation tasks (Hash Map, Priority Queue)

## Scoring Dimensions

The reviewer model (DeepSeek V4 Pro) evaluates code across 4 core dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Correctness | 40% | Does the code produce correct results? |
| Efficiency | 25% | Time and space complexity |
| Completeness | 20% | Are all requirements met? |
| Style | 15% | Code style and conventions |

Each dimension is scored 0-10 by the reviewer, then weighted to produce a final score out of 1.0.

## Project Structure

```
code-benchmark/
├── src/code_benchmark/   # Main package
├── tasks/                # Benchmark task definitions
├── results/              # Benchmark run outputs
├── config.yaml           # Configuration file
└── pyproject.toml        # Project metadata
```

## License

MIT
