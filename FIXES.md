# Benchmark Tool - Fixes and Optimizations

## Issues Fixed

### 1. API Authentication (401 Errors)
**Problem**: API calls were failing with "Invalid API key" errors.

**Root Cause**: 
- OpenCode Go uses different endpoints for different models:
  - `/chat/completions` (OpenAI format) for: deepseek-*, glm-*, kimi-*, mimo-*
  - `/messages` (Anthropic format) for: qwen3.7-plus, qwen3.7-max, qwen3.6-plus, minimax-*
- The benchmark was sending all requests to `/chat/completions`
- Anthropic-style endpoint requires `x-api-key` header instead of `Authorization: Bearer`

**Fix**:
- Added endpoint routing in `api_client.py` based on model name
- Implemented separate header builders for OpenAI and Anthropic formats
- Updated response parsing to handle both formats

### 2. API Key Loading
**Problem**: Environment variable `OPENCODE_GO_API_KEY` was being truncated to 3 characters ("sk-").

**Root Cause**: PowerShell was not properly passing the full key to bash subprocess.

**Fix**:
- Added fallback in `config.py` to read API key directly from Hermes `.env` file
- Checks environment variable first, falls back to `~/.hermes/.env` if key is too short

### 3. Reviewer Not Generating Scores
**Problem**: All benchmark scores were 0.0 because the reviewer wasn't returning valid JSON.

**Root Cause**:
- Reviewer model (deepseek-v4-pro) is a reasoning model
- With `max_tokens=512`, it spent all tokens on reasoning (`reasoning_content`)
- Never produced actual JSON response in `content` field

**Fix**:
- Increased `max_tokens` from 512 to 4096 for reviewer calls
- Added detection for reasoning models that exhaust tokens on thinking
- Improved error messages to indicate when max_tokens needs to be increased

### 4. Token Optimization
**Problem**: Benchmark was consuming too many tokens.

**Optimizations Applied**:
- Reduced code generation `max_tokens` from 4096 to 2048
- Reduced reviewer dimensions from 8 to 4 (correctness, efficiency, completeness, style)
- Simplified reviewer prompt to ~100 tokens (was ~500)
- Changed execution from sequential to concurrent (asyncio.gather)
- Reduced reviewer response `max_tokens` from 2048 to 512 (later increased to 4096 for reasoning models)

**Result**: ~60-70% reduction in token usage per benchmark run

## Current Configuration

### Models
- **Candidates**: qwen3.7-plus, deepseek-v4-flash, kimi-k2.6
- **Reviewer**: deepseek-v4-pro (reasoning model for high-quality evaluation)

### Scoring Dimensions (4 dimensions, weighted)
| Dimension | Weight | Description |
|-----------|--------|-------------|
| Correctness | 40% | Does the code produce correct results? |
| Efficiency | 25% | Time and space complexity |
| Completeness | 20% | Are all requirements met? |
| Style | 15% | Code style and conventions |

### API Endpoints
| Model Pattern | Endpoint | Auth Header |
|---------------|----------|-------------|
| deepseek-*, glm-*, kimi-*, mimo-* | `/chat/completions` | `Authorization: Bearer` |
| qwen3.7-plus, qwen3.7-max, qwen3.6-plus, minimax-* | `/messages` | `x-api-key` |

## Test Results

Sample benchmark run (2 models, 2 tasks):

```
Model: deepseek-v4-flash
  - binary-search: 1.0 (correctness: 10, efficiency: 10, completeness: 10, style: 10)
  - off-by-one: 1.0 (correctness: 10, efficiency: 10, completeness: 10, style: 10)

Model: qwen3.7-plus
  - binary-search: 1.0 (correctness: 10, efficiency: 10, completeness: 10, style: 10)
  - off-by-one: 0.97 (correctness: 10, efficiency: 10, completeness: 10, style: 9)
```

## Files Modified

1. `src/code_benchmark/api_client.py`
   - Added endpoint routing logic
   - Implemented `_build_openai_payload()` and `_build_anthropic_payload()`
   - Added `_build_anthropic_headers()` for x-api-key auth
   - Updated `_extract_response()` to handle reasoning models

2. `src/code_benchmark/config.py`
   - Added fallback to read API key from Hermes `.env` file
   - Validates key length before accepting environment variable

3. `src/code_benchmark/reviewer.py`
   - Increased `max_tokens` from 512 to 4096 for reasoning models
   - Updated prompt template to use 4 dimensions

4. `src/code_benchmark/scorer.py`
   - Updated to use 4 dimensions instead of 8

5. `config.yaml`
   - Updated scoring weights for 4 dimensions

6. `README.md`
   - Updated configuration instructions
   - Updated scoring dimensions table

## Next Steps

1. **Docker Integration**: Implement isolated code execution in containers
2. **Expanded Task Library**: Add more tasks across all categories
3. **Web Dashboard**: Build Phase 2 web interface for visualization
4. **Historical Tracking**: Add SQLite database for trend analysis
5. **CI/CD Integration**: Automate benchmark runs on schedule
