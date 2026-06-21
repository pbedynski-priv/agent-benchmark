# Hermes Agent Model Optimization Benchmark

## Overview

This benchmark evaluates AI models across specific Hermes agent use cases to determine the optimal model assignment for each role.

## Benchmark Categories

### 1. Tool Use & Function Calling (Weight: 25%)
**Purpose**: Evaluate ability to correctly use Hermes tools

**Test Cases**:
- **Terminal Commands**: Generate correct bash/PowerShell commands
- **File Operations**: Read/write/patch files with correct syntax
- **Browser Actions**: Navigate, click, type in web pages
- **API Calls**: Format HTTP requests correctly
- **Tool Chaining**: Use multiple tools in sequence

**Scoring**:
- Correct tool selection (30%)
- Proper parameter formatting (30%)
- Successful execution (30%)
- Error handling (10%)

**Example Tasks**:
```yaml
- id: tool-terminal-basic
  category: hermes-tool-use
  task: "List all Python files in the current directory"
  expected_tool: terminal
  expected_command: "find . -name '*.py' -type f"
  
- id: tool-file-patch
  category: hermes-tool-use
  task: "Replace 'old_function' with 'new_function' in main.py"
  expected_tool: patch
  expected_format: "mode: replace, path: main.py, old_string: old_function, new_string: new_function"
```

### 2. Instruction Following (Weight: 20%)
**Purpose**: Evaluate ability to follow complex, multi-step instructions

**Test Cases**:
- Multi-step workflows
- Constraint adherence (format, length, style)
- Conditional logic (if X then Y)
- Negative constraints (don't do X)

**Scoring**:
- Completeness (40%)
- Constraint adherence (30%)
- Correctness (20%)
- Format compliance (10%)

**Example Tasks**:
```yaml
- id: instruction-multistep
  category: hermes-instruction
  task: |
    1. Create a file called test.py
    2. Write a function that calculates factorial
    3. Add docstrings to the function
    4. Include 3 test cases at the bottom
  constraints:
    - must_use_type_hints: true
    - max_lines: 50
    - must_include_docstrings: true
    
- id: instruction-constraints
  category: hermes-instruction
  task: "Explain how git rebase works"
  constraints:
    - max_words: 100
    - must_include_example: true
    - no_technical_jargon: true
```

### 3. Context Understanding & Memory (Weight: 15%)
**Purpose**: Evaluate ability to extract and manage information

**Test Cases**:
- Summarize long conversations
- Extract key facts and preferences
- Identify contradictions
- Update memory entries correctly

**Scoring**:
- Accuracy of extraction (40%)
- Completeness (30%)
- Conciseness (20%)
- Format compliance (10%)

**Example Tasks**:
```yaml
- id: memory-extract-facts
  category: hermes-memory
  context: |
    User: I'm using Python 3.11 on Windows 10
    User: My project uses pytest for testing
    User: I prefer type hints in all functions
  task: "Extract user environment and preferences"
  expected_output:
    - "Python version: 3.11"
    - "OS: Windows 10"
    - "Testing framework: pytest"
    - "Preference: type hints required"
    
- id: memory-update
  category: hermes-memory
  current_memory: "User prefers dark mode"
  new_info: "User now prefers light mode"
  task: "Update memory with new preference"
  expected_output: "User prefers light mode"
```

### 4. Planning & Task Decomposition (Weight: 15%)
**Purpose**: Evaluate ability to break down complex goals

**Test Cases**:
- Break down vague goals into actionable steps
- Identify dependencies between tasks
- Estimate effort/time
- Prioritize tasks

**Scoring**:
- Completeness of plan (30%)
- Logical ordering (25%)
- Feasibility (25%)
- Clarity (20%)

**Example Tasks**:
```yaml
- id: planning-webapp
  category: hermes-planning
  task: "Build a todo web application"
  expected_steps:
    - "Set up project structure"
    - "Design database schema"
    - "Implement backend API"
    - "Create frontend UI"
    - "Add authentication"
    - "Write tests"
    - "Deploy application"
    
- id: planning-debug
  category: hermes-planning
  task: "Debug why the API is returning 500 errors"
  expected_steps:
    - "Check server logs"
    - "Reproduce the error locally"
    - "Identify failing endpoint"
    - "Check database connections"
    - "Test with different inputs"
    - "Fix root cause"
    - "Add error handling"
```

### 5. Error Recovery & Debugging (Weight: 10%)
**Purpose**: Evaluate ability to handle failures gracefully

**Test Cases**:
- Command fails → suggest alternatives
- Syntax errors → fix them
- API errors → retry with different approach
- Infinite loops → detect and break

**Scoring**:
- Error identification (30%)
- Solution correctness (30%)
- Recovery strategy (25%)
- Prevention suggestions (15%)

**Example Tasks**:
```yaml
- id: error-command-fail
  category: hermes-error-recovery
  scenario: |
    Command: pip install nonexistent-package
    Error: ERROR: Could not find a version that satisfies the requirement
  task: "Suggest how to proceed"
  expected_output:
    - "Check package name spelling"
    - "Search for similar packages"
    - "Check if package is available for your Python version"
    
- id: error-infinite-loop
  category: hermes-error-recovery
  code: |
    while True:
        data = fetch_data()
        process(data)
  task: "Identify and fix the issue"
  expected_output: "Add exit condition or timeout"
```

### 6. Code Review & Evaluation (Weight: 10%)
**Purpose**: Evaluate ability to assess code quality

**Test Cases**:
- Identify bugs in code
- Suggest improvements
- Catch security issues
- Evaluate code style

**Scoring**:
- Bug detection accuracy (35%)
- Improvement suggestions quality (25%)
- Security issue identification (25%)
- Style feedback (15%)

**Example Tasks**:
```yaml
- id: review-find-bugs
  category: hermes-code-review
  code: |
    def divide(a, b):
        return a / b
  task: "Review this code for issues"
  expected_issues:
    - "No zero division check"
    - "No type hints"
    - "No docstring"
    
- id: review-security
  category: hermes-code-review
  code: |
    def get_user(user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        return db.execute(query)
  task: "Identify security issues"
  expected_issues:
    - "SQL injection vulnerability"
    - "Should use parameterized queries"
```

### 7. Speed & Efficiency (Weight: 5%)
**Purpose**: Evaluate performance metrics

**Metrics**:
- Response latency (time to first token)
- Total tokens used
- Cost per task
- Tokens per second

**Scoring**:
- Latency (40%)
- Token efficiency (30%)
- Cost efficiency (30%)

## Model Role Optimization

Based on benchmark results, we'll assign models to Hermes roles:

| Hermes Role | Current Model | Benchmark Category | Optimization Goal |
|-------------|---------------|-------------------|-------------------|
| Main (conversations) | qwen3.7-plus | Instruction Following, Context | Best overall quality |
| Delegation (subagents) | deepseek-v4-flash | Planning, Tool Use | Fast + accurate |
| Auxiliary: Vision | deepseek-v4-flash | Context Understanding | Image analysis |
| Auxiliary: Compression | deepseek-v4-flash | Context Understanding | Summarization |
| Auxiliary: Skills | deepseek-v4-flash | Instruction Following | Skill execution |
| Auxiliary: Reviewer | deepseek-v4-pro | Code Review | High-quality evaluation |
| Auxiliary: Triage | deepseek-v4-flash | Planning | Task routing |
| Auxiliary: Titles | deepseek-v4-flash | Context Understanding | Quick summaries |

## Benchmark Execution

### Phase 1: Create Task Library
- [ ] Define 10 tasks per category (70 total)
- [ ] Create expected outputs/reference solutions
- [ ] Validate task difficulty distribution

### Phase 2: Run Benchmarks
- [ ] Test all candidate models on all tasks
- [ ] Collect scores, latency, token usage
- [ ] Calculate cost per task

### Phase 3: Analyze Results
- [ ] Rank models per category
- [ ] Identify best model for each Hermes role
- [ ] Calculate potential cost savings

### Phase 4: Optimize Configuration
- [ ] Update config.yaml with optimal models
- [ ] Document rationale for each assignment
- [ ] Monitor real-world performance

## Expected Outcomes

1. **Data-driven model selection** instead of guesswork
2. **Cost optimization** by using cheaper models where appropriate
3. **Quality improvement** by using best models for critical tasks
4. **Performance baseline** for future model comparisons
5. **Automated testing** for new model releases

## Example Output

```
=== Hermes Model Optimization Report ===

Category: Tool Use & Function Calling
  1. qwen3.7-plus: 9.2/10 (avg 2.1s, $0.003/task)
  2. kimi-k2.6: 8.8/10 (avg 1.8s, $0.002/task)
  3. deepseek-v4-flash: 7.5/10 (avg 0.9s, $0.001/task)
  → Recommendation: qwen3.7-plus (best accuracy)

Category: Instruction Following
  1. qwen3.7-plus: 9.5/10 (avg 2.3s, $0.004/task)
  2. deepseek-v4-pro: 9.3/10 (avg 3.1s, $0.006/task)
  3. kimi-k2.6: 8.9/10 (avg 2.0s, $0.003/task)
  → Recommendation: qwen3.7-plus (best balance)

Category: Planning & Decomposition
  1. deepseek-v4-pro: 9.4/10 (avg 3.5s, $0.007/task)
  2. qwen3.7-plus: 8.7/10 (avg 2.4s, $0.004/task)
  3. kimi-k2.6: 8.5/10 (avg 2.2s, $0.003/task)
  → Recommendation: deepseek-v4-pro for complex planning, qwen3.7-plus for simple

...

=== Optimal Configuration ===
Main model: qwen3.7-plus (best overall)
Delegation: deepseek-v4-flash (fast + cheap + good enough)
Reviewer: deepseek-v4-pro (highest quality evaluation)
Planning tasks: deepseek-v4-pro (when complexity > threshold)
Simple tasks: deepseek-v4-flash (cost optimization)

Estimated monthly savings: $2.50 (25% reduction)
Quality improvement: +0.3 points average
```
