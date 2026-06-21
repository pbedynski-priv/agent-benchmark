#!/usr/bin/env python3
"""Generate Hermes benchmark tasks programmatically."""

import os
import yaml
from pathlib import Path

TASKS_DIR = Path("tasks/hermes")

# Task templates for each category
TASK_TEMPLATES = {
    "tool-use": [
        {
            "id": "tool-terminal-basic",
            "difficulty": "easy",
            "description": "Generate basic terminal command",
            "prompt": "List all Python files in the current directory",
            "expected_tool": "terminal",
            "expected_output": "find . -name '*.py' -type f",
            "test_cases": [
                {"input": "List Python files", "expected": "find . -name '*.py'", "description": "Basic file search"}
            ],
            "tags": ["terminal", "file-search"]
        },
        {
            "id": "tool-terminal-pipe",
            "difficulty": "medium",
            "description": "Chain commands with pipes",
            "prompt": "Find all Python files containing 'import' and count them",
            "expected_tool": "terminal",
            "expected_output": "find . -name '*.py' -exec grep -l 'import' {} \\; | wc -l",
            "test_cases": [
                {"input": "Count Python files with imports", "expected": "find.*grep.*wc", "description": "Pipe chain"}
            ],
            "tags": ["terminal", "pipes"]
        },
        {
            "id": "tool-file-read",
            "difficulty": "easy",
            "description": "Read file content",
            "prompt": "Read the contents of config.yaml",
            "expected_tool": "read_file",
            "expected_output": "read_file(path='config.yaml')",
            "test_cases": [
                {"input": "Read config file", "expected": "read_file.*config.yaml", "description": "File read operation"}
            ],
            "tags": ["file", "read"]
        },
        {
            "id": "tool-file-write",
            "difficulty": "easy",
            "description": "Create new file",
            "prompt": "Create a new file called test.py with a hello world function",
            "expected_tool": "write_file",
            "expected_output": "write_file(path='test.py', content='def hello():\\n    print(\"Hello\")')",
            "test_cases": [
                {"input": "Create test file", "expected": "write_file.*test.py", "description": "File write operation"}
            ],
            "tags": ["file", "write"]
        },
        {
            "id": "tool-file-patch",
            "difficulty": "medium",
            "description": "Edit specific lines in file",
            "prompt": "Replace 'old_function' with 'new_function' in main.py",
            "expected_tool": "patch",
            "expected_output": "patch(path='main.py', old_string='old_function', new_string='new_function')",
            "test_cases": [
                {"input": "Replace function name", "expected": "patch.*main.py.*old_function.*new_function", "description": "File patch operation"}
            ],
            "tags": ["file", "patch"]
        },
        {
            "id": "tool-browser-navigate",
            "difficulty": "easy",
            "description": "Navigate to URL",
            "prompt": "Go to https://github.com",
            "expected_tool": "browser_navigate",
            "expected_output": "browser_navigate(url='https://github.com')",
            "test_cases": [
                {"input": "Navigate to GitHub", "expected": "browser_navigate.*github.com", "description": "Browser navigation"}
            ],
            "tags": ["browser", "navigate"]
        },
        {
            "id": "tool-browser-click",
            "difficulty": "medium",
            "description": "Click element on page",
            "prompt": "Click the 'Sign in' button",
            "expected_tool": "browser_click",
            "expected_output": "browser_click(ref='@e5')",
            "test_cases": [
                {"input": "Click sign in", "expected": "browser_click.*ref", "description": "Element click"}
            ],
            "tags": ["browser", "click"]
        },
        {
            "id": "tool-browser-type",
            "difficulty": "medium",
            "description": "Type text in form field",
            "prompt": "Type 'admin' in the username field",
            "expected_tool": "browser_type",
            "expected_output": "browser_type(ref='@e3', text='admin')",
            "test_cases": [
                {"input": "Type username", "expected": "browser_type.*text.*admin", "description": "Form input"}
            ],
            "tags": ["browser", "type"]
        },
        {
            "id": "tool-api-get",
            "difficulty": "medium",
            "description": "Make GET request",
            "prompt": "Fetch data from https://api.example.com/users",
            "expected_tool": "terminal",
            "expected_output": "curl https://api.example.com/users",
            "test_cases": [
                {"input": "GET request", "expected": "curl.*api.example.com/users", "description": "API GET"}
            ],
            "tags": ["api", "get"]
        },
        {
            "id": "tool-api-post",
            "difficulty": "hard",
            "description": "Make POST request with data",
            "prompt": "Send a POST request to https://api.example.com/users with JSON data {\"name\": \"John\"}",
            "expected_tool": "terminal",
            "expected_output": "curl -X POST -H 'Content-Type: application/json' -d '{\"name\": \"John\"}' https://api.example.com/users",
            "test_cases": [
                {"input": "POST with JSON", "expected": "curl.*POST.*application/json", "description": "API POST"}
            ],
            "tags": ["api", "post"]
        }
    ],
    
    "instruction": [
        {
            "id": "instruction-multistep",
            "difficulty": "hard",
            "description": "Follow multi-step workflow",
            "prompt": "1. Create a file called calculator.py\n2. Write an add function\n3. Add type hints\n4. Include docstrings\n5. Add 3 test cases",
            "expected_output": "create file, write function, add type hints, add docstrings, add tests",
            "test_cases": [
                {"input": "Multi-step task", "expected": "calculator.py.*add.*def.*->.*int", "description": "Complete workflow"}
            ],
            "tags": ["multistep", "workflow"]
        },
        {
            "id": "instruction-format-constraint",
            "difficulty": "medium",
            "description": "Follow format constraints",
            "prompt": "Explain what a decorator is in Python in exactly 100 words",
            "constraints": {"max_words": 100, "exact_words": 100},
            "test_cases": [
                {"input": "Word count constraint", "expected": "\\b\\w+\\b.*100", "description": "Exact word count"}
            ],
            "tags": ["constraint", "format"]
        },
        {
            "id": "instruction-conditional",
            "difficulty": "medium",
            "description": "Follow conditional logic",
            "prompt": "If the user is on Windows, use PowerShell. If on Linux, use bash. If on macOS, use zsh.",
            "test_cases": [
                {"input": "Windows", "expected": "PowerShell", "description": "Windows branch"},
                {"input": "Linux", "expected": "bash", "description": "Linux branch"},
                {"input": "macOS", "expected": "zsh", "description": "macOS branch"}
            ],
            "tags": ["conditional", "logic"]
        },
        {
            "id": "instruction-negative",
            "difficulty": "medium",
            "description": "Follow negative constraints",
            "prompt": "Write a Python function to sort a list, but don't use the built-in sort() or sorted() methods",
            "constraints": {"forbidden": ["sort()", "sorted()"]},
            "test_cases": [
                {"input": "No built-in sort", "expected": "def.*sort", "not_expected": "sort\\(\\)|sorted\\(", "description": "Custom sort implementation"}
            ],
            "tags": ["constraint", "negative"]
        },
        {
            "id": "instruction-sequential",
            "difficulty": "hard",
            "description": "Follow sequential steps",
            "prompt": "First, create a directory called 'project'. Then, create __init__.py inside it. Finally, create main.py with a main function.",
            "test_cases": [
                {"input": "Sequential creation", "expected": "mkdir.*project.*__init__.py.*main.py", "description": "Ordered operations"}
            ],
            "tags": ["sequential", "steps"]
        },
        {
            "id": "instruction-json-format",
            "difficulty": "medium",
            "description": "Output valid JSON",
            "prompt": "Return a JSON object with keys: name (string), age (number), active (boolean)",
            "expected_format": "json",
            "test_cases": [
                {"input": "JSON output", "expected": "\\{.*name.*age.*active.*\\}", "description": "Valid JSON structure"}
            ],
            "tags": ["format", "json"]
        },
        {
            "id": "instruction-markdown-format",
            "difficulty": "easy",
            "description": "Output valid markdown",
            "prompt": "Create a markdown document with a title, 2 sections, and a code block",
            "expected_format": "markdown",
            "test_cases": [
                {"input": "Markdown structure", "expected": "#.*##.*```", "description": "Valid markdown"}
            ],
            "tags": ["format", "markdown"]
        },
        {
            "id": "instruction-length",
            "difficulty": "medium",
            "description": "Respect length constraints",
            "prompt": "Write a Python function that calculates fibonacci numbers. Maximum 50 lines of code.",
            "constraints": {"max_lines": 50},
            "test_cases": [
                {"input": "Line limit", "expected": "def.*fibonacci", "max_lines": 50, "description": "Concise implementation"}
            ],
            "tags": ["constraint", "length"]
        },
        {
            "id": "instruction-style",
            "difficulty": "medium",
            "description": "Follow style requirements",
            "prompt": "Write a Python class with 3 methods. All methods must have type hints and docstrings.",
            "constraints": {"require_type_hints": True, "require_docstrings": True},
            "test_cases": [
                {"input": "Type hints required", "expected": "def.*\\(.*:.*\\).*->", "description": "Type hints present"},
                {"input": "Docstrings required", "expected": "\"\"\".*\"\"\"", "description": "Docstrings present"}
            ],
            "tags": ["constraint", "style"]
        },
        {
            "id": "instruction-priority",
            "difficulty": "hard",
            "description": "Prioritize information",
            "prompt": "List the 5 most important Python best practices, ordered from most to least important",
            "test_cases": [
                {"input": "Priority ordering", "expected": "1\\..*2\\..*3\\..*4\\..*5\\.", "description": "Numbered priority list"}
            ],
            "tags": ["priority", "ordering"]
        }
    ],
    
    "memory": [
        {
            "id": "memory-extract-facts",
            "difficulty": "medium",
            "description": "Extract facts from conversation",
            "prompt": "Extract key facts from this conversation:\nUser: I'm using Python 3.11 on Windows 10\nUser: My project uses pytest\nUser: I prefer type hints",
            "context": "User: I'm using Python 3.11 on Windows 10\nUser: My project uses pytest\nUser: I prefer type hints",
            "expected_output": ["Python 3.11", "Windows 10", "pytest", "type hints"],
            "test_cases": [
                {"input": "Extract environment", "expected": "Python.*3\\.11.*Windows.*pytest", "description": "Fact extraction"}
            ],
            "tags": ["extraction", "facts"]
        },
        {
            "id": "memory-extract-environment",
            "difficulty": "easy",
            "description": "Extract environment details",
            "prompt": "What environment is the user working in?\nUser: I'm on WSL2 with Ubuntu 22.04, using VS Code",
            "context": "User: I'm on WSL2 with Ubuntu 22.04, using VS Code",
            "expected_output": ["WSL2", "Ubuntu 22.04", "VS Code"],
            "test_cases": [
                {"input": "Environment extraction", "expected": "WSL2.*Ubuntu.*VS Code", "description": "Environment details"}
            ],
            "tags": ["extraction", "environment"]
        },
        {
            "id": "memory-summarize-long",
            "difficulty": "hard",
            "description": "Summarize long conversation",
            "prompt": "Summarize this 50-turn conversation in 3 sentences:\n[Long conversation about building a web app with Flask, adding authentication, deploying to Heroku, fixing bugs, adding tests]",
            "context": "[Simulated 50-turn conversation about Flask web app development]",
            "constraints": {"max_sentences": 3},
            "test_cases": [
                {"input": "Long summary", "expected": "\\..*\\..*\\.", "description": "Concise summary"}
            ],
            "tags": ["summarization", "long-context"]
        },
        {
            "id": "memory-identify-preferences",
            "difficulty": "medium",
            "description": "Identify user preferences",
            "prompt": "What are the user's coding preferences?\nUser: I like black for formatting\nUser: Always use f-strings\nUser: Prefer async/await over threads",
            "context": "User: I like black for formatting\nUser: Always use f-strings\nUser: Prefer async/await over threads",
            "expected_output": ["black formatter", "f-strings", "async/await"],
            "test_cases": [
                {"input": "Preference extraction", "expected": "black.*f-string.*async", "description": "Coding preferences"}
            ],
            "tags": ["extraction", "preferences"]
        },
        {
            "id": "memory-detect-contradictions",
            "difficulty": "hard",
            "description": "Find contradictory statements",
            "prompt": "Find contradictions:\nUser: I never use type hints\nUser: All my functions have type hints",
            "context": "User: I never use type hints\nUser: All my functions have type hints",
            "expected_output": "Contradiction about type hints usage",
            "test_cases": [
                {"input": "Contradiction detection", "expected": "contradict|conflict|inconsistent", "description": "Find contradiction"}
            ],
            "tags": ["analysis", "contradiction"]
        },
        {
            "id": "memory-update",
            "difficulty": "medium",
            "description": "Update memory entry",
            "prompt": "Current memory: 'User prefers dark mode'\nNew info: 'User now prefers light mode'\nUpdate the memory",
            "context": "Current: User prefers dark mode\nNew: User now prefers light mode",
            "expected_output": "User prefers light mode",
            "test_cases": [
                {"input": "Memory update", "expected": "light mode", "description": "Update preference"}
            ],
            "tags": ["update", "memory"]
        },
        {
            "id": "memory-merge",
            "difficulty": "hard",
            "description": "Merge related memories",
            "prompt": "Merge these memories:\n1. 'User uses Python 3.11'\n2. 'User is on Windows'\n3. 'User uses VS Code'",
            "context": "Memory 1: Python 3.11\nMemory 2: Windows\nMemory 3: VS Code",
            "expected_output": "User uses Python 3.11 on Windows with VS Code",
            "test_cases": [
                {"input": "Memory merge", "expected": "Python.*Windows.*VS Code", "description": "Combine memories"}
            ],
            "tags": ["merge", "memory"]
        },
        {
            "id": "memory-prioritize",
            "difficulty": "medium",
            "description": "Prioritize facts by importance",
            "prompt": "Rank these facts by importance for future sessions:\n1. User's favorite color is blue\n2. User's project uses PostgreSQL\n3. User prefers dark mode",
            "context": "Facts: favorite color, PostgreSQL, dark mode",
            "expected_output": "PostgreSQL > dark mode > favorite color",
            "test_cases": [
                {"input": "Prioritization", "expected": "PostgreSQL.*dark.*color", "description": "Rank importance"}
            ],
            "tags": ["prioritize", "importance"]
        },
        {
            "id": "memory-format",
            "difficulty": "easy",
            "description": "Format for MEMORY.md",
            "prompt": "Format this fact for MEMORY.md: 'User uses Python 3.11 on Windows 10 with WSL2'",
            "expected_format": "memory_md",
            "test_cases": [
                {"input": "Memory format", "expected": "Python.*Windows.*WSL2", "description": "Proper formatting"}
            ],
            "tags": ["format", "memory"]
        },
        {
            "id": "memory-validate",
            "difficulty": "hard",
            "description": "Check if memory is still valid",
            "prompt": "Is this memory still valid?\nMemory: 'User is using Python 3.9'\nRecent conversation: User mentions Python 3.11 features",
            "context": "Memory: Python 3.9\nRecent: Python 3.11 features",
            "expected_output": "Memory is outdated, should be Python 3.11",
            "test_cases": [
                {"input": "Validation", "expected": "outdated|invalid|3\\.11", "description": "Check validity"}
            ],
            "tags": ["validate", "memory"]
        }
    ],
    
    "planning": [
        {
            "id": "planning-webapp",
            "difficulty": "hard",
            "description": "Plan web application",
            "prompt": "Create a detailed plan to build a todo web application with user authentication",
            "expected_steps": ["setup project", "database design", "backend API", "frontend UI", "authentication", "testing", "deployment"],
            "test_cases": [
                {"input": "Web app plan", "expected": "project.*database.*API.*UI.*auth.*test.*deploy", "description": "Complete plan"}
            ],
            "tags": ["planning", "webapp"]
        },
        {
            "id": "planning-debug",
            "difficulty": "medium",
            "description": "Plan debugging approach",
            "prompt": "The API is returning 500 errors intermittently. Plan your debugging approach.",
            "expected_steps": ["check logs", "reproduce error", "identify pattern", "check dependencies", "test fixes"],
            "test_cases": [
                {"input": "Debug plan", "expected": "log.*reproduce.*pattern.*fix", "description": "Debugging strategy"}
            ],
            "tags": ["planning", "debugging"]
        },
        {
            "id": "planning-refactor",
            "difficulty": "hard",
            "description": "Plan code refactoring",
            "prompt": "Plan how to refactor a 5000-line monolithic Python file into modular components",
            "expected_steps": ["analyze dependencies", "identify modules", "create interfaces", "extract functions", "write tests", "migrate gradually"],
            "test_cases": [
                {"input": "Refactor plan", "expected": "analyze.*module.*interface.*extract.*test.*migrate", "description": "Refactoring strategy"}
            ],
            "tags": ["planning", "refactoring"]
        },
        {
            "id": "planning-feature",
            "difficulty": "medium",
            "description": "Plan feature implementation",
            "prompt": "Plan implementing a search feature for an e-commerce site with filters and sorting",
            "expected_steps": ["define requirements", "design API", "implement backend", "create UI", "add filters", "test performance"],
            "test_cases": [
                {"input": "Feature plan", "expected": "requirement.*API.*backend.*UI.*filter.*test", "description": "Feature implementation"}
            ],
            "tags": ["planning", "feature"]
        },
        {
            "id": "planning-migration",
            "difficulty": "hard",
            "description": "Plan database migration",
            "prompt": "Plan migrating from MySQL to PostgreSQL with zero downtime",
            "expected_steps": ["analyze schema", "create migration scripts", "setup dual-write", "validate data", "switch read traffic", "decommission MySQL"],
            "test_cases": [
                {"input": "Migration plan", "expected": "schema.*migration.*dual.*validate.*switch.*decommission", "description": "Migration strategy"}
            ],
            "tags": ["planning", "migration"]
        },
        {
            "id": "planning-deploy",
            "difficulty": "medium",
            "description": "Plan deployment strategy",
            "prompt": "Plan deploying a Python web app to AWS with auto-scaling",
            "expected_steps": ["choose services", "setup infrastructure", "configure CI/CD", "setup monitoring", "test scaling", "deploy"],
            "test_cases": [
                {"input": "Deploy plan", "expected": "service.*infrastructure.*CI.*monitor.*scale.*deploy", "description": "Deployment strategy"}
            ],
            "tags": ["planning", "deployment"]
        },
        {
            "id": "planning-test",
            "difficulty": "medium",
            "description": "Plan testing strategy",
            "prompt": "Plan a comprehensive testing strategy for a payment processing system",
            "expected_steps": ["unit tests", "integration tests", "security tests", "performance tests", "edge cases", "regression tests"],
            "test_cases": [
                {"input": "Test plan", "expected": "unit.*integration.*security.*performance.*edge.*regression", "description": "Testing strategy"}
            ],
            "tags": ["planning", "testing"]
        },
        {
            "id": "planning-api",
            "difficulty": "medium",
            "description": "Plan REST API design",
            "prompt": "Design a REST API for a blog platform with posts, comments, and users",
            "expected_steps": ["define resources", "design endpoints", "specify request/response", "add authentication", "document API"],
            "test_cases": [
                {"input": "API design", "expected": "resource.*endpoint.*request.*auth.*document", "description": "API design"}
            ],
            "tags": ["planning", "api"]
        },
        {
            "id": "planning-security",
            "difficulty": "hard",
            "description": "Plan security audit",
            "prompt": "Plan a security audit for a web application handling sensitive user data",
            "expected_steps": ["identify assets", "threat modeling", "code review", "penetration testing", "compliance check", "remediation plan"],
            "test_cases": [
                {"input": "Security plan", "expected": "asset.*threat.*review.*penetration.*compliance.*remediation", "description": "Security audit"}
            ],
            "tags": ["planning", "security"]
        },
        {
            "id": "planning-performance",
            "difficulty": "hard",
            "description": "Plan performance optimization",
            "prompt": "Plan optimizing a slow Python application that processes large datasets",
            "expected_steps": ["profile code", "identify bottlenecks", "optimize algorithms", "add caching", "parallelize", "monitor improvements"],
            "test_cases": [
                {"input": "Performance plan", "expected": "profile.*bottleneck.*optimize.*cache.*parallel.*monitor", "description": "Optimization strategy"}
            ],
            "tags": ["planning", "performance"]
        }
    ],
    
    "error-recovery": [
        {
            "id": "error-command-not-found",
            "difficulty": "easy",
            "description": "Handle missing command",
            "prompt": "Command failed: 'jq: command not found'. How do you proceed?",
            "scenario": "jq: command not found",
            "expected_output": "Install jq or use alternative like python -m json.tool",
            "test_cases": [
                {"input": "Missing command", "expected": "install|alternative|python.*json", "description": "Recovery strategy"}
            ],
            "tags": ["error", "command"]
        },
        {
            "id": "error-permission-denied",
            "difficulty": "medium",
            "description": "Handle permission errors",
            "prompt": "Command failed: 'Permission denied' when trying to write to /etc/hosts. How do you proceed?",
            "scenario": "Permission denied: /etc/hosts",
            "expected_output": "Use sudo or run as administrator",
            "test_cases": [
                {"input": "Permission error", "expected": "sudo|administrator|root", "description": "Permission fix"}
            ],
            "tags": ["error", "permission"]
        },
        {
            "id": "error-syntax",
            "difficulty": "easy",
            "description": "Fix syntax errors",
            "prompt": "Fix this Python syntax error:\ndef my_function(x\n    return x * 2",
            "scenario": "SyntaxError: invalid syntax",
            "code": "def my_function(x\n    return x * 2",
            "expected_output": "def my_function(x):\n    return x * 2",
            "test_cases": [
                {"input": "Syntax fix", "expected": "def my_function\\(x\\):", "description": "Fix syntax"}
            ],
            "tags": ["error", "syntax"]
        },
        {
            "id": "error-runtime",
            "difficulty": "medium",
            "description": "Fix runtime exceptions",
            "prompt": "Fix this runtime error:\nTypeError: can only concatenate str (not \"int\") to str\nCode: result = \"Value: \" + 42",
            "scenario": "TypeError: can only concatenate str",
            "code": "result = \"Value: \" + 42",
            "expected_output": "result = \"Value: \" + str(42)",
            "test_cases": [
                {"input": "Runtime fix", "expected": "str\\(42\\)|f-string|format", "description": "Type conversion"}
            ],
            "tags": ["error", "runtime"]
        },
        {
            "id": "error-api",
            "difficulty": "hard",
            "description": "Handle API failures",
            "prompt": "API call failed with 503 Service Unavailable after 3 retries. How do you proceed?",
            "scenario": "HTTP 503 after 3 retries",
            "expected_output": "Implement exponential backoff, check service status, use fallback",
            "test_cases": [
                {"input": "API failure", "expected": "backoff|fallback|status|circuit.*breaker", "description": "API recovery"}
            ],
            "tags": ["error", "api"]
        },
        {
            "id": "error-timeout",
            "difficulty": "medium",
            "description": "Handle timeout errors",
            "prompt": "Database query timed out after 30 seconds. How do you proceed?",
            "scenario": "Query timeout: 30s exceeded",
            "expected_output": "Optimize query, add indexes, increase timeout, or paginate results",
            "test_cases": [
                {"input": "Timeout handling", "expected": "optimize|index|timeout|paginate", "description": "Timeout recovery"}
            ],
            "tags": ["error", "timeout"]
        },
        {
            "id": "error-infinite-loop",
            "difficulty": "hard",
            "description": "Detect and fix infinite loops",
            "prompt": "This code is stuck in an infinite loop. Fix it:\nwhile True:\n    data = fetch_data()\n    if not data:\n        continue\n    process(data)",
            "scenario": "Infinite loop detected",
            "code": "while True:\n    data = fetch_data()\n    if not data:\n        continue\n    process(data)",
            "expected_output": "Add break condition or timeout",
            "test_cases": [
                {"input": "Loop fix", "expected": "break|timeout|max.*iteration", "description": "Break infinite loop"}
            ],
            "tags": ["error", "loop"]
        },
        {
            "id": "error-memory-leak",
            "difficulty": "hard",
            "description": "Identify memory issues",
            "prompt": "Application memory usage keeps growing. Identify potential causes in this code:\ncache = {}\ndef get_data(key):\n    if key not in cache:\n        cache[key] = fetch_large_dataset(key)\n    return cache[key]",
            "scenario": "Memory leak detected",
            "code": "cache = {}\ndef get_data(key):\n    if key not in cache:\n        cache[key] = fetch_large_dataset(key)\n    return cache[key]",
            "expected_output": "Unbounded cache growth, add LRU eviction or size limit",
            "test_cases": [
                {"input": "Memory fix", "expected": "LRU|evict|limit|max.*size", "description": "Fix memory leak"}
            ],
            "tags": ["error", "memory"]
        },
        {
            "id": "error-race-condition",
            "difficulty": "hard",
            "description": "Fix concurrency bugs",
            "prompt": "Fix this race condition:\ncounter = 0\ndef increment():\n    global counter\n    counter += 1",
            "scenario": "Race condition in concurrent counter",
            "code": "counter = 0\ndef increment():\n    global counter\n    counter += 1",
            "expected_output": "Use threading.Lock or atomic operations",
            "test_cases": [
                {"input": "Race fix", "expected": "Lock|atomic|mutex|synchronize", "description": "Fix race condition"}
            ],
            "tags": ["error", "concurrency"]
        },
        {
            "id": "error-deadlock",
            "difficulty": "hard",
            "description": "Fix deadlock situations",
            "prompt": "Fix this deadlock:\nlock1 = Lock()\nlock2 = Lock()\ndef thread1():\n    lock1.acquire()\n    lock2.acquire()\ndef thread2():\n    lock2.acquire()\n    lock1.acquire()",
            "scenario": "Deadlock between two threads",
            "code": "lock1 = Lock()\nlock2 = Lock()\ndef thread1():\n    lock1.acquire()\n    lock2.acquire()\ndef thread2():\n    lock2.acquire()\n    lock1.acquire()",
            "expected_output": "Always acquire locks in same order or use timeout",
            "test_cases": [
                {"input": "Deadlock fix", "expected": "order|timeout|tryLock|consistent", "description": "Fix deadlock"}
            ],
            "tags": ["error", "deadlock"]
        }
    ],
    
    "code-review": [
        {
            "id": "review-find-bugs",
            "difficulty": "medium",
            "description": "Identify logic errors",
            "prompt": "Find bugs in this code:\ndef average(numbers):\n    total = 0\n    for n in numbers:\n        total += n\n    return total / len(numbers)",
            "code": "def average(numbers):\n    total = 0\n    for n in numbers:\n        total += n\n    return total / len(numbers)",
            "expected_issues": ["Division by zero if list is empty"],
            "test_cases": [
                {"input": "Bug detection", "expected": "zero|empty|division|len.*0", "description": "Find logic bug"}
            ],
            "tags": ["review", "bugs"]
        },
        {
            "id": "review-security",
            "difficulty": "hard",
            "description": "Find security vulnerabilities",
            "prompt": "Find security issues:\ndef get_user(user_id):\n    query = f\"SELECT * FROM users WHERE id = {user_id}\"\n    return db.execute(query)",
            "code": "def get_user(user_id):\n    query = f\"SELECT * FROM users WHERE id = {user_id}\"\n    return db.execute(query)",
            "expected_issues": ["SQL injection vulnerability"],
            "test_cases": [
                {"input": "Security review", "expected": "SQL.*injection|parameterized|sanitize", "description": "Find security issue"}
            ],
            "tags": ["review", "security"]
        },
        {
            "id": "review-performance",
            "difficulty": "medium",
            "description": "Find performance issues",
            "prompt": "Find performance problems:\ndef process_items(items):\n    result = []\n    for item in items:\n        if item not in result:\n            result.append(item)\n    return result",
            "code": "def process_items(items):\n    result = []\n    for item in items:\n        if item not in result:\n            result.append(item)\n    return result",
            "expected_issues": ["O(n²) complexity, should use set"],
            "test_cases": [
                {"input": "Performance review", "expected": "O\\(n.*2\\)|set|complexity|slow", "description": "Find performance issue"}
            ],
            "tags": ["review", "performance"]
        },
        {
            "id": "review-improvements",
            "difficulty": "medium",
            "description": "Suggest code improvements",
            "prompt": "Suggest improvements:\ndef calc(x, y, op):\n    if op == '+': return x + y\n    if op == '-': return x - y\n    if op == '*': return x * y\n    if op == '/': return x / y",
            "code": "def calc(x, y, op):\n    if op == '+': return x + y\n    if op == '-': return x - y\n    if op == '*': return x * y\n    if op == '/': return x / y",
            "expected_issues": ["Use dictionary dispatch", "Add error handling", "Add type hints"],
            "test_cases": [
                {"input": "Improvement suggestions", "expected": "dictionary|dispatch|error|type.*hint", "description": "Suggest improvements"}
            ],
            "tags": ["review", "improvements"]
        },
        {
            "id": "review-style",
            "difficulty": "easy",
            "description": "Check PEP 8 compliance",
            "prompt": "Check style issues:\ndef MyFunction( x,y ):\n    z=x+y\n    return z",
            "code": "def MyFunction( x,y ):\n    z=x+y\n    return z",
            "expected_issues": ["Function name should be lowercase", "Missing spaces around operators", "Unused variable name"],
            "test_cases": [
                {"input": "Style check", "expected": "PEP.*8|lowercase|space|naming", "description": "Style issues"}
            ],
            "tags": ["review", "style"]
        },
        {
            "id": "review-docs",
            "difficulty": "easy",
            "description": "Check documentation",
            "prompt": "Check documentation:\ndef calculate_compound_interest(principal, rate, time, n=12):\n    return principal * (1 + rate/n) ** (n*time)",
            "code": "def calculate_compound_interest(principal, rate, time, n=12):\n    return principal * (1 + rate/n) ** (n*time)",
            "expected_issues": ["Missing docstring", "No parameter descriptions", "No return type"],
            "test_cases": [
                {"input": "Documentation check", "expected": "docstring|document|comment|description", "description": "Documentation issues"}
            ],
            "tags": ["review", "documentation"]
        },
        {
            "id": "review-tests",
            "difficulty": "medium",
            "description": "Check test coverage",
            "prompt": "What test cases are missing for this function?\ndef is_palindrome(s):\n    return s == s[::-1]",
            "code": "def is_palindrome(s):\n    return s == s[::-1]",
            "expected_issues": ["Empty string", "Single character", "Case sensitivity", "Non-alphanumeric characters"],
            "test_cases": [
                {"input": "Test coverage", "expected": "empty|single|case|edge|boundary", "description": "Missing tests"}
            ],
            "tags": ["review", "tests"]
        },
        {
            "id": "review-types",
            "difficulty": "easy",
            "description": "Check type hints",
            "prompt": "Check type hints:\ndef greet(name, greeting):\n    return f\"{greeting}, {name}!\"",
            "code": "def greet(name, greeting):\n    return f\"{greeting}, {name}!\"",
            "expected_issues": ["Missing type hints for parameters", "Missing return type"],
            "test_cases": [
                {"input": "Type hint check", "expected": "type.*hint|:.*str|->.*str", "description": "Type hint issues"}
            ],
            "tags": ["review", "types"]
        },
        {
            "id": "review-complexity",
            "difficulty": "hard",
            "description": "Check code complexity",
            "prompt": "Analyze complexity:\ndef process_data(data):\n    result = []\n    for i in range(len(data)):\n        for j in range(len(data)):\n            if data[i] == data[j]:\n                result.append((i, j))\n    return result",
            "code": "def process_data(data):\n    result = []\n    for i in range(len(data)):\n        for j in range(len(data)):\n            if data[i] == data[j]:\n                result.append((i, j))\n    return result",
            "expected_issues": ["O(n²) time complexity", "Nested loops", "Could be optimized with hash map"],
            "test_cases": [
                {"input": "Complexity analysis", "expected": "O\\(n.*2\\)|nested|complexity|optimize", "description": "Complexity issues"}
            ],
            "tags": ["review", "complexity"]
        },
        {
            "id": "review-best-practices",
            "difficulty": "medium",
            "description": "Check Python best practices",
            "prompt": "Check best practices:\ndata = []\nfor i in range(100):\n    data.append(i * 2)",
            "code": "data = []\nfor i in range(100):\n    data.append(i * 2)",
            "expected_issues": ["Should use list comprehension", "Magic number 100"],
            "test_cases": [
                {"input": "Best practices", "expected": "comprehension|list.*comp|magic.*number|constant", "description": "Best practice issues"}
            ],
            "tags": ["review", "best-practices"]
        }
    ]
}

def generate_tasks():
    """Generate all task YAML files."""
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    
    total_tasks = 0
    index_data = {
        "version": "1.0",
        "total_tasks": 0,
        "categories": []
    }
    
    for category, tasks in TASK_TEMPLATES.items():
        category_dir = TASKS_DIR / category
        category_dir.mkdir(exist_ok=True)
        
        task_ids = []
        for task in tasks:
            # Add category to task
            task["category"] = f"hermes-{category}"
            
            # Write task file
            task_file = category_dir / f"{task['id']}.yaml"
            with open(task_file, 'w') as f:
                yaml.dump(task, f, default_flow_style=False, sort_keys=False)
            
            task_ids.append(task['id'])
            total_tasks += 1
            print(f"Created: {task_file}")
        
        # Add to index
        index_data["categories"].append({
            "name": f"hermes-{category}",
            "count": len(tasks),
            "tasks": task_ids
        })
    
    # Write index
    index_data["total_tasks"] = total_tasks
    index_file = TASKS_DIR / "index.yaml"
    with open(index_file, 'w') as f:
        yaml.dump(index_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n✓ Generated {total_tasks} tasks across {len(TASK_TEMPLATES)} categories")
    print(f"✓ Index file: {index_file}")

if __name__ == "__main__":
    generate_tasks()
