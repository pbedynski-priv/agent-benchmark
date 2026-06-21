# Model Code Quality Benchmark Tool — Comprehensive Plan

## 1. Overview & Goals

### Purpose
A systematic tool for comparing code generation quality across AI models available through the OpenCode Go API. Enables data-driven decisions about model selection for coding tasks.

### Key Objectives
- **Fair comparison**: Same prompts, same conditions, multiple models
- **Multi-dimensional scoring**: Not just "does it run?" but correctness, efficiency, style, completeness
- **Reproducible**: Deterministic task library, versioned results
- **Actionable output**: Clear reports showing which model excels at what

### Available Models (via OpenCode Go API)
| Model | Role |
|-------|------|
| deepseek-v4-pro | Candidate + Reviewer |
| deepseek-v4-flash | Candidate (fast/cheap) |
| kimi-k2.5 | Candidate |
| kimi-k2.6 | Candidate + Reviewer |
| qwen3.6-plus | Candidate |
| qwen3.7-plus | Candidate (current main) |
| qwen3.7-max | Candidate |
| minimax-m2.5 | Candidate |
| minimax-m2.7 | Candidate |
| minimax-m3 | Candidate |
| glm-5 | Candidate |
| glm-5.1 | Candidate |
| mimo-v2.5 | Candidate |
| mimo-v2.5-pro | Candidate |

---

## 2. Architecture

### Design Decision: CLI Tool (Phase 1) → Web Dashboard (Phase 2)

**Rationale**: CLI is faster to build, easier to automate (cron, CI), works in WSL2/terminal, and produces machine-readable output. A web dashboard can be added later consuming the same JSON reports.

### Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.11 | Available, rich ecosystem |
| HTTP Client | `httpx` (async) | Async support, modern API |
| CLI Framework | `click` or `typer` | Clean CLI interface |
| Configuration | YAML (`pyyaml`) | Human-readable config |
| Data Storage | JSON files + SQLite | Simple, no external DB needed |
| Terminal Output | `rich` | Beautiful tables and progress bars |
| Report Generation | `jinja2` + Markdown | Flexible templates |
| Testing | `pytest` + `pytest-asyncio` | Async test support |
| **Execution** | **Docker** | **Isolated, reproducible code execution** |

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Interface (typer)                     │
├─────────────────────────────────────────────────────────────┤
│  benchmark run    │  benchmark report  │  benchmark compare  │
└────────┬──────────────────┬──────────────────┬──────────────┘
         │                  │                  │
    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
    │ Task    │       │ Runner  │       │ Reviewer│
    │ Library │       │ Engine  │       │ Engine  │
    └────┬────┘       └────┬────┘       └────┬────┘
         │                  │                  │
    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
    │ YAML    │       │ OpenCode│       │ OpenCode│
    │ Tasks   │       │ Go API  │       │ Go API  │
    └─────────┘       └─────────┘       └─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Results Store     │
                    │ (JSON + SQLite)   │
                    └───────────────────┘
```

### Core Components

1. **Task Library** — Versioned YAML files defining benchmark tasks
2. **Runner Engine** — Sends tasks to models, collects responses
3. **Reviewer Engine** — Evaluates code using a judge model
4. **Results Store** — Persists and queries benchmark results
5. **Report Generator** — Produces tables, JSON, and markdown reports
6. **CLI Interface** — User-facing commands

### Execution Environment (Isolated Docker Containers)

All generated code executes in **isolated Docker containers** to ensure:
- **Fair comparison**: Every model runs in identical environment
- **Safety**: Code can't affect host system or other benchmarks
- **Reproducibility**: Same base image, dependencies, resource limits every time

```
┌─────────────────────────────────────────────────────────┐
│  Docker Container (per model response)                  │
│  ─────────────────────────────────────────────────────  │
│  Base Image: python:3.11-slim                           │
│  Dependencies: Pre-installed (numpy, requests, pytest)  │
│  Network: Disabled (security)                           │
│  Resources: 1 CPU, 512MB RAM, 30s timeout               │
│  Filesystem: Temp directory, auto-cleanup after run     │
│  Working Dir: /benchmark (read-only task files)         │
└─────────────────────────────────────────────────────────┘
```

**Container Configuration:**
```yaml
# docker-compose.benchmark.yml (or programmatic docker-py)
services:
  benchmark-runner:
    image: python:3.11-slim
    command: python /benchmark/run_task.py
    volumes:
      - ./tasks:/benchmark:ro
      - ./results:/results:rw
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
    networks: []  # No network access
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:size=100M
```

**Benefits:**
- ✅ Identical environment for all models (no "works on my machine" bias)
- ✅ Safe execution of untrusted AI-generated code
- ✅ Resource limits prevent runaway processes
- ✅ Network isolation prevents external dependencies
- ✅ Automatic cleanup after each run
- ✅ Easy to reproduce results on any machine with Docker

---

## 3. Benchmark Task Library

### Task Categories

| Category | Count | Description |
|----------|-------|-------------|
| algorithms | 10 | Sorting, searching, graph traversal, DP |
| data-structures | 8 | Implement/extend data structures |
| debugging | 8 | Find and fix bugs in provided code |
| refactoring | 8 | Improve code quality without changing behavior |
| api-design | 6 | Design REST/GraphQL endpoints |
| system-design | 5 | Design components (rate limiter, cache, etc.) |
| testing | 6 | Write tests for given code |
| string-manipulation | 8 | Parsing, transformation, validation |
| concurrency | 5 | Async patterns, thread safety |
| code-generation | 10 | Generate code from specifications |
| sql-queries | 6 | Complex SQL queries and optimizations |
| error-handling | 5 | Robust error handling patterns |
| **Total** | **~85** | |

### Task YAML Schema

```yaml
id: "algo-001"
category: "algorithms"
difficulty: "medium"
title: "Implement LRU Cache"
description: |
  Implement a Least Recently Used (LRU) cache with O(1) get and put operations.
  
  Requirements:
  - get(key) -> value or -1 if not found
  - put(key, value) -> insert or update
  - When capacity is exceeded, evict the least recently used item
  - Both operations must be O(1) time complexity

language: "python"  # or "any" to let model choose
constraints:
  max_tokens: 2000
  timeout_seconds: 30
  allowed_imports: ["collections"]
  
test_cases:
  - name: "basic_operations"
    input: |
      cache = LRUCache(2)
      cache.put(1, 1)
      cache.put(2, 2)
      result1 = cache.get(1)
      cache.put(3, 3)  # evicts key 2
      result2 = cache.get(2)
    expected: "result1=1, result2=-1"
    
  - name: "update_existing"
    input: |
      cache = LRUCache(2)
      cache.put(1, 1)
      cache.put(1, 10)  # update
      result = cache.get(1)
    expected: "result=10"

  - name: "capacity_one"
    input: |
      cache = LRUCache(1)
      cache.put(1, 1)
      cache.put(2, 2)
      result = cache.get(1)
    expected: "result=-1"

evaluation_focus:
  - correctness
  - efficiency
  - edge_cases
  - code_style

reference_solution: |
  from collections import OrderedDict
  
  class LRUCache:
      def __init__(self, capacity: int):
          self.cache = OrderedDict()
          self.capacity = capacity
      
      def get(self, key: int) -> int:
          if key not in self.cache:
              return -1
          self.cache.move_to_end(key)
          return self.cache[key]
      
      def put(self, key: int, value: int) -> None:
          if key in self.cache:
              self.cache.move_to_end(key)
          self.cache[key] = value
          if len(self.cache) > self.capacity:
              self.cache.popitem(last=False)
```

### Difficulty Levels

| Level | Description | Expected Complexity |
|-------|-------------|-------------------|
| easy | Basic implementation, clear spec | 10-30 lines |
| medium | Multiple requirements, edge cases | 30-80 lines |
| hard | Complex algorithms, optimization needed | 80-200 lines |
| expert | System design, trade-offs, production-quality | 200+ lines |

---

## 4. Evaluation Criteria & Scoring Rubric

### Scoring Dimensions (each 1-10)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Correctness** | 30% | Code produces correct output for all test cases |
| **Efficiency** | 20% | Time/space complexity, algorithmic optimality |
| **Completeness** | 15% | Handles all requirements and edge cases |
| **Code Style** | 10% | Readability, naming, structure, PEP 8 compliance |
| **Error Handling** | 10% | Input validation, graceful failure modes |
| **Documentation** | 5% | Comments, docstrings, clarity of intent |
| **Innovation** | 5% | Creative solutions, clever optimizations |
| **Security** | 5% | No obvious vulnerabilities, safe patterns |

### Scoring Rubric (per dimension)

#### Correctness (30%)
| Score | Criteria |
|-------|----------|
| 9-10 | All test cases pass, handles all edge cases correctly |
| 7-8 | Most test cases pass, minor edge case failures |
| 5-6 | Core logic correct but misses some cases |
| 3-4 | Partially correct, significant logic errors |
| 1-2 | Fundamentally broken, doesn't solve the problem |

#### Efficiency (20%)
| Score | Criteria |
|-------|----------|
| 9-10 | Optimal complexity, best-known algorithm for the problem |
| 7-8 | Near-optimal, minor inefficiencies acceptable |
| 5-6 | Acceptable but clearly suboptimal approach |
| 3-4 | Poor complexity (e.g., O(n²) when O(n) exists) |
| 1-2 | Extremely inefficient, would fail on large inputs |

#### Completeness (15%)
| Score | Criteria |
|-------|----------|
| 9-10 | All requirements met, all edge cases handled |
| 7-8 | Most requirements met, some edge cases missed |
| 5-6 | Core functionality present, missing features |
| 3-4 | Significant portions of spec unimplemented |
| 1-2 | Barely addresses the problem |

#### Code Style (10%)
| Score | Criteria |
|-------|----------|
| 9-10 | Clean, idiomatic, well-structured, excellent naming |
| 7-8 | Good style with minor issues |
| 5-6 | Readable but inconsistent or non-idiomatic |
| 3-4 | Poor naming, messy structure |
| 1-2 | Unreadable, no structure |

#### Error Handling (10%)
| Score | Criteria |
|-------|----------|
| 9-10 | Comprehensive validation, clear error messages |
| 7-8 | Good handling of common errors |
| 5-6 | Basic error handling present |
| 3-4 | Minimal error handling |
| 1-2 | No error handling, crashes on bad input |

#### Documentation (5%)
| Score | Criteria |
|-------|----------|
| 9-10 | Excellent docstrings, inline comments where needed |
| 7-8 | Good documentation, some gaps |
| 5-6 | Basic comments present |
| 3-4 | Minimal documentation |
| 1-2 | No documentation |

#### Innovation (5%)
| Score | Criteria |
|-------|----------|
| 9-10 | Novel approach, clever optimization, elegant solution |
| 7-8 | Some creative elements |
| 5-6 | Standard approach, well-executed |
| 3-4 | Very basic/naive approach |
| 1-2 | Copy-paste or trivially wrong |

#### Security (5%)
| Score | Criteria |
|-------|----------|
| 9-10 | No vulnerabilities, follows security best practices |
| 7-8 | Generally safe, minor concerns |
| 5-6 | Acceptable for the context |
| 3-4 | Some security concerns (e.g., no input validation) |
| 1-2 | Obvious vulnerabilities (injection, etc.) |

### Composite Score Calculation

```
composite = (correctness * 0.30) + (efficiency * 0.20) + (completeness * 0.15) +
            (style * 0.10) + (error_handling * 0.10) + (documentation * 0.05) +
            (innovation * 0.05) + (security * 0.05)
```

Score range: 1.0 - 10.0

### Reviewer Prompt Template

```
You are an expert code reviewer evaluating AI-generated code.

## Task
{task_description}

## Requirements
{task_requirements}

## Submitted Code
```{language}
{submitted_code}
```

## Test Cases
{test_cases}

## Evaluation Instructions
Score the code on each dimension (1-10) and provide brief justification.

Respond in this exact JSON format:
{
  "scores": {
    "correctness": {"score": N, "justification": "..."},
    "efficiency": {"score": N, "justification": "..."},
    "completeness": {"score": N, "justification": "..."},
    "code_style": {"score": N, "justification": "..."},
    "error_handling": {"score": N, "justification": "..."},
    "documentation": {"score": N, "justification": "..."},
    "innovation": {"score": N, "justification": "..."},
    "security": {"score": N, "justification": "..."}
  },
  "composite_score": N.N,
  "summary": "...",
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "suggested_improvements": ["...", "..."]
}
```

### Reviewer Model Selection

| Reviewer | Why | Cost |
|----------|-----|------|
| **deepseek-v4-pro** (primary) | Strong reasoning, excellent at code analysis, cache-friendly | $1.74/$3.48, cache read $0.0145 |
| **kimi-k2.6** (secondary) | Cross-validate scores, reduce bias | $0.95/$4.00, cache read $0.16 |

**Why DeepSeek V4 Pro as Primary Reviewer:**
- **Highest reasoning quality** for accurate code evaluation
- **Cache-optimized**: Reviewer uses same prompt template repeatedly — cache read at $0.0145 (120x cheaper than fresh input)
- **Cost-effective**: Only reviews code, doesn't generate it, so total cost stays low
- **Consistent scoring**: Same model = consistent evaluation criteria across all benchmark runs

**Strategy**: Use deepseek-v4-pro as primary reviewer for all tasks. Optionally run kimi-k2.6 as a second reviewer on a subset (10-20%) to calibrate and detect reviewer bias.

---

## 5. API Integration Approach

### OpenCode Go API Details

- **Base URL**: `https://opencode.ai/zen/go/v1`
- **Protocol**: OpenAI-compatible Chat Completions API
- **Endpoint**: `POST /chat/completions`
- **Authentication**: Bearer token (API key)

### API Request Format

```python
import httpx

async def call_model(model: str, prompt: str, system: str = None) -> str:
    """Send a prompt to a model via OpenCode Go API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,  # Low temp for consistent coding output
        "max_tokens": 4096,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://opencode.ai/zen/go/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
```

### Rate Limiting & Retry Strategy

```python
# Configuration
RATE_LIMITS = {
    "requests_per_minute": 20,
    "requests_per_hour": 200,
    "concurrent_requests": 3,  # Max parallel model calls
}

RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 2.0,  # 1s, 2s, 4s
    "retry_on": [429, 500, 502, 503, 504],
}
```

### Model Call Configuration

| Parameter | Code Generation | Review/Evaluation |
|-----------|----------------|-------------------|
| temperature | 0.2 | 0.1 |
| max_tokens | 4096 | 2048 |
| top_p | 0.9 | 0.9 |
| timeout | 120s | 60s |

### Authentication

```yaml
# ~/.config/benchmark-tool/config.yaml
api:
  base_url: "https://opencode.ai/zen/go/v1"
  api_key_env: "OPENCODE_API_KEY"  # Read from environment variable
  
# Or use keyring for secure storage
```

---

## 6. Output Formats

### 6.1 Terminal Output (Rich)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              MODEL CODE QUALITY BENCHMARK RESULTS                     ┃
┃              Run: 2026-06-18 14:30:00 UTC                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌─────────────────┬───────────┬───────────┬───────────┬───────────┬──────────┐
│ Model           │ Correct.  │ Efficiency│ Complete  │ Style     │ Composite│
├─────────────────┼───────────┼───────────┼───────────┼───────────┼──────────┤
│ deepseek-v4-pro │    9.2    │    8.8    │    9.0    │    8.5    │   8.94   │
│ kimi-k2.6       │    8.8    │    8.5    │    8.7    │    8.9    │   8.69   │
│ qwen3.7-plus    │    8.5    │    8.2    │    8.8    │    8.7    │   8.51   │
│ qwen3.7-max     │    8.9    │    8.6    │    8.5    │    8.3    │   8.57   │
│ glm-5.1         │    8.1    │    7.9    │    8.3    │    8.1    │   8.11   │
│ minimax-m3      │    7.8    │    7.5    │    8.0    │    7.9    │   7.81   │
└─────────────────┴───────────┴───────────┴───────────┴───────────┴──────────┘

🏆 Top Performer: deepseek-v4-pro (8.94)
📊 Tasks evaluated: 85 | Models compared: 6 | Reviewer: deepseek-v4-pro
```

### 6.2 JSON Report

```json
{
  "metadata": {
    "run_id": "bench-2026-06-18-143000",
    "timestamp": "2026-06-18T14:30:00Z",
    "reviewer_model": "deepseek-v4-pro",
    "task_library_version": "1.0.0",
    "total_tasks": 85,
    "models_tested": 6
  },
  "summary": {
    "rankings": [
      {"rank": 1, "model": "deepseek-v4-pro", "composite": 8.94, "best_category": "algorithms"},
      {"rank": 2, "model": "kimi-k2.6", "composite": 8.69, "best_category": "code-generation"},
      {"rank": 3, "model": "qwen3.7-max", "composite": 8.57, "best_category": "api-design"}
    ],
    "category_winners": {
      "algorithms": "deepseek-v4-pro",
      "data-structures": "deepseek-v4-pro",
      "debugging": "kimi-k2.6",
      "api-design": "qwen3.7-max",
      "system-design": "kimi-k2.6",
      "testing": "qwen3.7-plus",
      "concurrency": "deepseek-v4-pro"
    }
  },
  "results": [
    {
      "task_id": "algo-001",
      "task_title": "Implement LRU Cache",
      "category": "algorithms",
      "difficulty": "medium",
      "model_results": {
        "deepseek-v4-pro": {
          "code": "...",
          "scores": {
            "correctness": {"score": 10, "justification": "..."},
            "efficiency": {"score": 10, "justification": "..."},
            "completeness": {"score": 9, "justification": "..."},
            "code_style": {"score": 9, "justification": "..."},
            "error_handling": {"score": 8, "justification": "..."},
            "documentation": {"score": 8, "justification": "..."},
            "innovation": {"score": 7, "justification": "..."},
            "security": {"score": 9, "justification": "..."}
          },
          "composite_score": 9.15,
          "response_time_ms": 4200,
          "tokens_used": 850
        }
      }
    }
  ]
}
```

### 6.3 Markdown Report

```markdown
# Benchmark Results — 2026-06-18

## Overall Rankings

| Rank | Model | Composite | Best Category |
|------|-------|-----------|---------------|
| 1 | deepseek-v4-pro | 8.94 | algorithms |
| 2 | kimi-k2.6 | 8.69 | code-generation |
| 3 | qwen3.7-max | 8.57 | api-design |

## Category Breakdown

### Algorithms (10 tasks)
| Model | Avg Score | Pass Rate |
|-------|-----------|-----------|
| deepseek-v4-pro | 9.2 | 100% |
| kimi-k2.6 | 8.6 | 90% |
| qwen3.7-plus | 8.1 | 80% |

## Recommendations
- **Best overall**: deepseek-v4-pro for complex algorithmic tasks
- **Best value**: deepseek-v4-flash for simple tasks (7.8 composite, 5x faster)
- **Best for API design**: qwen3.7-max
- **Best for debugging**: kimi-k2.6
```

### 6.4 Visualization (Optional Phase 2)

Using `matplotlib` or `plotly` for:
- Radar charts (multi-dimensional comparison per model)
- Bar charts (category-wise performance)
- Heatmaps (task × model score matrix)
- Box plots (score distribution per model)

---

## 7. File Structure

```
benchmark-tool/
├── README.md
├── pyproject.toml              # Project metadata, dependencies
├── config/
│   ├── default.yaml            # Default configuration
│   └── models.yaml             # Model definitions & endpoints
├── src/
│   └── benchmark/
│       ├── __init__.py
│       ├── cli.py              # CLI entry point (typer)
│       ├── config.py           # Configuration loading
│       ├── api/
│       │   ├── __init__.py
│       │   ├── client.py       # OpenCode Go API client
│       │   ├── rate_limiter.py # Rate limiting
│       │   └── retry.py        # Retry logic
│       ├── tasks/
│       │   ├── __init__.py
│       │   ├── loader.py       # Load tasks from YAML
│       │   ├── runner.py       # Execute tasks against models
│       │   └── validator.py    # Validate task responses
│       ├── evaluation/
│       │   ├── __init__.py
│       │   ├── reviewer.py     # Reviewer model orchestration
│       │   ├── scorer.py       # Score calculation
│       │   └── prompts.py      # Review prompt templates
│       ├── results/
│       │   ├── __init__.py
│       │   ├── store.py        # Results persistence (JSON/SQLite)
│       │   ├── query.py        # Query/filter results
│       │   └── comparator.py   # Cross-model comparison logic
│       └── reports/
│           ├── __init__.py
│           ├── terminal.py     # Rich terminal output
│           ├── json_report.py  # JSON report generation
│           ├── markdown.py     # Markdown report generation
│           └── templates/
│               ├── comparison.md.j2
│               ├── detailed.md.j2
│               └── summary.md.j2
├── tasks/
│   ├── algorithms/
│   │   ├── lru-cache.yaml
│   │   ├── binary-search-tree.yaml
│   │   ├── dijkstra.yaml
│   │   └── ...
│   ├── data-structures/
│   │   ├── hash-map.yaml
│   │   ├── priority-queue.yaml
│   │   └── ...
│   ├── debugging/
│   │   ├── off-by-one.yaml
│   │   ├── race-condition.yaml
│   │   └── ...
│   ├── refactoring/
│   │   ├── god-class.yaml
│   │   ├── long-method.yaml
│   │   └── ...
│   ├── api-design/
│   │   ├── rest-endpoints.yaml
│   │   └── ...
│   ├── system-design/
│   │   ├── rate-limiter.yaml
│   │   ├── url-shortener.yaml
│   │   └── ...
│   ├── testing/
│   │   ├── unit-tests.yaml
│   │   └── ...
│   ├── concurrency/
│   │   ├── producer-consumer.yaml
│   │   └── ...
│   └── index.yaml              # Task registry
├── results/                    # Output directory
│   ├── runs/
│   │   └── 2026-06-18-143000/
│   │       ├── results.json
│   │       ├── report.md
│   │       └── report.html
│   └── history.db              # SQLite for trend analysis
├── tests/
│   ├── test_api_client.py
│   ├── test_task_loader.py
│   ├── test_scorer.py
│   ├── test_reviewer.py
│   └── fixtures/
│       └── sample_task.yaml
└── scripts/
    ├── run_benchmark.sh        # Quick-run script
    └── generate_tasks.py       # Helper to scaffold new tasks
```

---

## 8. Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Project scaffolding (pyproject.toml, package structure)
- [ ] Configuration system (YAML loading, env vars)
- [ ] OpenCode Go API client with retry/rate-limiting
- [ ] Task YAML schema and loader
- [ ] Basic CLI skeleton (typer)
- [ ] 10 sample tasks across 3 categories

### Phase 2: Execution Engine (Week 2)
- [ ] Task runner (send to models, collect responses)
- [ ] Code extraction from model responses (markdown code blocks)
- [ ] Response validation (syntax check, basic execution)
- [ ] Concurrent model execution (asyncio)
- [ ] Progress tracking (rich progress bars)
- [ ] Error handling and graceful degradation

### Phase 3: Evaluation Engine (Week 2-3)
- [ ] Reviewer prompt templates
- [ ] Score extraction from reviewer responses (JSON parsing)
- [ ] Composite score calculation
- [ ] Multi-reviewer support (optional cross-validation)
- [ ] Score normalization and calibration

### Phase 4: Reporting (Week 3)
- [ ] Rich terminal tables
- [ ] JSON report output
- [ ] Markdown report generation
- [ ] Comparison views (head-to-head, category breakdown)
- [ ] Historical trend tracking (SQLite)

### Phase 5: Task Library Expansion (Week 4)
- [ ] Complete all 85 tasks across 12 categories
- [ ] Reference solutions for all tasks
- [ ] Test case validation
- [ ] Difficulty calibration
- [ ] Task metadata (tags, skills tested)

### Phase 6: Polish & Automation (Week 4-5)
- [ ] Full test suite
- [ ] CI/CD integration (GitHub Actions)
- [ ] Scheduled benchmark runs (cron)
- [ ] Notification on completion
- [ ] Documentation (README, usage guide)

### Phase 7: Advanced Features (Future)
- [ ] Web dashboard (FastAPI + React)
- [ ] Radar charts and visualizations
- [ ] Custom task creation wizard
- [ ] A/B testing mode (two models, same task)
- [ ] Regression detection (alert on score drops)
- [ ] Cost tracking (tokens × price per model)

---

## 9. Example Benchmark Tasks

### Task 1: LRU Cache (algorithms/medium)

```yaml
id: "algo-001"
category: "algorithms"
difficulty: "medium"
title: "Implement LRU Cache"
description: |
  Implement a Least Recently Used (LRU) cache with O(1) get and put.
  When capacity is exceeded, evict the least recently used item.
language: "python"
constraints:
  max_tokens: 2000
test_cases:
  - name: "basic"
    input: "cache = LRUCache(2); cache.put(1,1); cache.put(2,2); print(cache.get(1)); cache.put(3,3); print(cache.get(2))"
    expected: "1\n-1"
  - name: "update"
    input: "cache = LRUCache(2); cache.put(1,1); cache.put(1,10); print(cache.get(1))"
    expected: "10"
```

### Task 2: Bug Finder (debugging/medium)

```yaml
id: "debug-001"
category: "debugging"
difficulty: "medium"
title: "Fix the Binary Search"
description: |
  The following binary search implementation has 3 bugs.
  Find and fix all of them. Explain each bug.
  
  ```python
  def binary_search(arr, target):
      left = 0
      right = len(arr)
      while left < right:
          mid = (left + right) // 2
          if arr[mid] == target:
              return mid
          elif arr[mid] < target:
              left = mid
          else:
              right = mid - 1
      return -1
  ```
  
  Bugs to find:
  1. Initial right boundary
  2. Left update (infinite loop risk)
  3. Potential integer overflow in mid calculation (for large arrays)
language: "python"
evaluation_focus:
  - correctness
  - completeness
  - code_style
```

### Task 3: Rate Limiter (system-design/hard)

```yaml
id: "sys-001"
category: "system-design"
difficulty: "hard"
title: "Token Bucket Rate Limiter"
description: |
  Implement a thread-safe token bucket rate limiter.
  
  Requirements:
  - Configurable bucket capacity and refill rate (tokens/second)
  - Thread-safe for concurrent access
  - try_acquire(tokens=1) -> bool: non-blocking check
  - acquire(tokens=1, timeout=None) -> bool: blocking with optional timeout
  - get_available_tokens() -> float
  - Support burst allowance up to capacity
  
  Consider:
  - Precision of time tracking
  - Memory efficiency
  - Lock contention minimization
language: "python"
constraints:
  max_tokens: 4096
evaluation_focus:
  - correctness
  - efficiency
  - concurrency
  - error_handling
```

### Task 4: SQL Query Optimization (sql/medium)

```yaml
id: "sql-001"
category: "sql-queries"
difficulty: "medium"
title: "Optimize Slow Query"
description: |
  Given this schema and slow query, optimize it:
  
  Schema:
  - orders (id, user_id, product_id, quantity, price, created_at)  -- 10M rows
  - users (id, name, email, created_at)  -- 500K rows
  - products (id, name, category, price)  -- 50K rows
  
  Slow query (takes 45 seconds):
  ```sql
  SELECT u.name, 
         COUNT(DISTINCT o.product_id) as unique_products,
         SUM(o.quantity * o.price) as total_spent
  FROM users u
  JOIN orders o ON u.id = o.user_id
  WHERE o.created_at >= '2025-01-01'
  GROUP BY u.id, u.name
  HAVING SUM(o.quantity * o.price) > 1000
  ORDER BY total_spent DESC
  LIMIT 100;
  ```
  
  Provide:
  1. Optimized query
  2. Recommended indexes
  3. Explanation of why it's faster
language: "sql"
evaluation_focus:
  - correctness
  - efficiency
  - completeness
```

### Task 5: Write Unit Tests (testing/medium)

```yaml
id: "test-001"
category: "testing"
difficulty: "medium"
title: "Write Tests for Auth Service"
description: |
  Write comprehensive unit tests for this authentication service:
  
  ```python
  import hashlib
  import secrets
  from datetime import datetime, timedelta
  
  class AuthService:
      def __init__(self):
          self.users = {}  # username -> {password_hash, salt, locked_until}
          self.sessions = {}  # token -> {username, expires_at}
      
      def register(self, username: str, password: str) -> bool:
          if username in self.users:
              return False
          if len(password) < 8:
              raise ValueError("Password too short")
          salt = secrets.token_hex(16)
          password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
          self.users[username] = {
              "password_hash": password_hash,
              "salt": salt,
              "locked_until": None
          }
          return True
      
      def login(self, username: str, password: str) -> str | None:
          if username not in self.users:
              return None
          user = self.users[username]
          if user["locked_until"] and datetime.now() < user["locked_until"]:
              return None
          password_hash = hashlib.sha256(
              (password + user["salt"]).encode()
          ).hexdigest()
          if password_hash != user["password_hash"]:
              user["locked_until"] = datetime.now() + timedelta(minutes=15)
              return None
          token = secrets.token_urlsafe(32)
          self.sessions[token] = {
              "username": username,
              "expires_at": datetime.now() + timedelta(hours=24)
          }
          return token
      
      def validate_session(self, token: str) -> str | None:
          if token not in self.sessions:
              return None
          session = self.sessions[token]
          if datetime.now() > session["expires_at"]:
              del self.sessions[token]
              return None
          return session["username"]
  ```
  
  Write tests covering:
  - Happy paths
  - Edge cases
  - Error conditions
  - Security considerations
language: "python"
evaluation_focus:
  - completeness
  - correctness
  - code_style
  - security
```

---

## 10. CLI Interface Design

### Commands

```bash
# Run a full benchmark
benchmark run --models deepseek-v4-pro,kimi-k2.6,qwen3.7-plus --categories algorithms,debugging

# Run specific tasks
benchmark run --tasks algo-001,debug-001,sys-001 --models all

# Run with specific reviewer
benchmark run --reviewer kimi-k2.6 --models all

# View results
benchmark report --run latest
benchmark report --run 2026-06-18-143000 --format markdown

# Compare two runs
benchmark compare --run-a 2026-06-01 --run-b 2026-06-18

# List available tasks
benchmark tasks list --category algorithms --difficulty medium

# Add a custom task
benchmark tasks add --file my-task.yaml

# Export results
benchmark export --format json --output results.json
benchmark export --format csv --output results.csv
```

### Configuration

```yaml
# ~/.config/benchmark-tool/config.yaml
api:
  base_url: "https://opencode.ai/zen/go/v1"
  api_key_env: "OPENCODE_API_KEY"

defaults:
  reviewer: "deepseek-v4-pro"
  temperature: 0.2
  max_tokens: 4096
  timeout: 120

rate_limits:
  requests_per_minute: 20
  concurrent_requests: 3

output:
  results_dir: "./results"
  default_format: "terminal"  # terminal, json, markdown, all

models:
  candidates:
    - deepseek-v4-pro
    - deepseek-v4-flash
    - kimi-k2.5
    - kimi-k2.6
    - qwen3.6-plus
    - qwen3.7-plus
    - qwen3.7-max
    - minimax-m2.5
    - minimax-m2.7
    - minimax-m3
    - glm-5
    - glm-5.1
    - mimo-v2.5
    - mimo-v2.5-pro
  reviewers:
    - deepseek-v4-pro
    - kimi-k2.6
```

---

## 11. Key Design Decisions

### Why CLI over Web App (Phase 1)
1. Faster to build and iterate
2. Easy to automate (cron, CI pipelines)
3. Works in WSL2/terminal natively
4. JSON output can feed any frontend later
5. No server infrastructure needed

### Why YAML for Tasks
1. Human-readable and editable
2. Easy to version control (git)
3. Supports complex nested structures (test cases, constraints)
4. Non-programmers can add tasks

### Why Multi-Dimensional Scoring
1. "Best model" depends on use case
2. A model great at algorithms might be weak at API design
3. Helps users pick the right model for their specific needs
4. More actionable than a single number

### Why Use AI as Reviewer
1. Scales to 85+ tasks × 14 models = 1190 evaluations
2. Consistent scoring criteria
3. Can evaluate subjective qualities (style, documentation)
4. Cross-validation with multiple reviewers reduces bias

### Temperature = 0.2 for Code Generation
1. Lower temperature = more deterministic output
2. Fairer comparison (less variance between runs)
3. Code quality should come from model capability, not randomness
4. Could experiment with temperature sweeps as advanced feature

---

## 12. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| API rate limits | Exponential backoff, request queuing, configurable limits |
| Reviewer bias | Multi-reviewer cross-validation, rubric calibration |
| Model downtime | Fallback models, graceful skip with logging |
| Task difficulty skew | Balanced categories, difficulty normalization |
| Cost explosion | Token tracking, budget limits, use flash models for simple tasks |
| Response parsing failures | Multiple extraction strategies, manual review queue |
| Test case insufficiency | Reference solutions, manual verification of scoring |

---

## 13. Success Metrics

The benchmark tool is successful if it:
1. Completes a full run (85 tasks × 14 models) in < 4 hours
2. Produces consistent scores (±0.5 on re-run of same model/task)
3. Generates actionable recommendations for model selection
4. Takes < 5 minutes to add a new benchmark task
5. Costs < $10 per full benchmark run

---

## 14. Quick Start (After Implementation)

```bash
# Install
cd benchmark-tool
pip install -e .

# Configure
export OPENCODE_API_KEY="your-key-here"
cp config/default.yaml ~/.config/benchmark-tool/config.yaml

# Quick test (3 tasks, 2 models)
benchmark run --tasks algo-001,debug-001,sql-001 --models deepseek-v4-pro,kimi-k2.6

# Full benchmark
benchmark run --models all --categories all --output all

# View results
benchmark report --run latest
```
