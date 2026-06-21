# Contributing to Agent Benchmark

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)
- [Your First Code Contribution](#your-first-code-contribution)
- [Improving The Documentation](#improving-the-documentation)
- [Style Guides](#style-guides)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.

## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](README.md).

Before you ask a question, it is best to search for existing [Issues](https://github.com/pbedynski-priv/agent-benchmark/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue.

The best way to get your question answered is:

1. Open an [Issue](https://github.com/pbedynski-priv/agent-benchmark/issues/new).
2. Provide as much context as you can about what you're running into.
3. Include your environment (OS, Python version, dependencies).

## I Want To Contribute

> ### Legal Notice
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project license.

### Reporting Bugs

#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to investigate carefully, collect information and describe the issue in detail in your report. Please complete the following steps in advance:

- Make sure you are using the latest version.
- Determine if your bug is really a bug and not an error on your side.
- To see if other users have experienced (and potentially already solved) the same issue you are having, check if there is a reported bug in the issue tracker.
- Collect information about the bug:
  - Stack trace
  - OS, Platform and Version
  - Python version
  - Can you reliably reproduce the issue?

#### How Do I Submit a Good Bug Report?

> You must never report security related issues, vulnerabilities or bugs including sensitive information to the issue tracker, or elsewhere in public. Instead sensitive bugs must be sent as described in [SECURITY.md](SECURITY.md).

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/pbedynski-priv/agent-benchmark/issues/new) using the bug report template.
- Explain the behavior you would expect and the actual behavior.
- Provide the *minimal* amount of code to reproduce the issue.
- Include your environment details.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion, including completely new features and minor improvements to existing functionality.

#### Before Submitting an Enhancement

- Make sure that you are using the latest version.
- Read the documentation carefully and find out if the functionality is already covered.
- Perform a [search](https://github.com/pbedynski-priv/agent-benchmark/issues) to see if the enhancement has already been suggested.
- Find out whether your idea fits with the scope and aims of the project.

#### How Do I Submit a Good Enhancement Suggestion?

- Use a **clear and descriptive title** for the issue.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
- **Explain why this enhancement would be useful** to most users.

### Your First Code Contribution

#### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/pbedynski-priv/agent-benchmark.git
cd agent-benchmark

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .
```

#### Making Changes

1. Create a new branch: `git checkout -b feature/my-feature` or `git checkout -b fix/my-fix`
2. Make your changes
3. Add/update tests as needed
4. Ensure all tests pass: `pytest`
5. Ensure code passes linting: `ruff check .`
6. Commit with a clear message (see [Commit Messages](#commit-messages))
7. Push to your fork
8. Open a Pull Request

### Improving The Documentation

Documentation improvements are highly valued. We use:
- **README.md** for project overview and quick start
- **docs/** for detailed documentation
- **Inline docstrings** (Google style) for API documentation

### Style Guides

#### Python Code Style

- Follow [PEP 8](https://pep8.org/)
- Use [Ruff](https://github.com/astral-sh/ruff) for linting (configured in pyproject.toml)
- Line length: 100 characters
- Use type hints for function signatures
- Write docstrings for all public functions/classes (Google style)

Example:
```python
def calculate_score(scores: dict[str, float], weights: dict[str, float]) -> float:
    """Calculate weighted score from individual dimension scores.
    
    Args:
        scores: Dictionary mapping dimension names to scores (0-10).
        weights: Dictionary mapping dimension names to weights (must sum to 1.0).
    
    Returns:
        Weighted total score as a float.
    
    Raises:
        ValueError: If weights don't sum to 1.0.
    """
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 0.001:
        raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    return sum(scores[k] * weights[k] for k in scores)
```

#### YAML Task Style

- Use descriptive task IDs (kebab-case)
- Include all required fields: `id`, `category`, `difficulty`, `prompt`
- Add comprehensive `expected_output` for reviewer context
- Include `tags` for filtering

Example:
```yaml
id: binary-search
category: algorithms
difficulty: easy
description: Implement binary search algorithm
prompt: |
  Implement a binary search function that finds a target value in a sorted array.
  Return the index of the target, or -1 if not found.
  
  Requirements:
  - Time complexity: O(log n)
  - Space complexity: O(1) for iterative, O(log n) for recursive
  - Handle edge cases (empty array, target not found)
expected_output: |
  Function should correctly find elements and return -1 for missing elements.
tags:
  - search
  - arrays
  - recursion
```

#### Markdown Style

- Use ATX-style headers (`#`, `##`, etc.)
- One sentence per line (for better git diffs)
- Use fenced code blocks with language identifiers
- Keep lines under 100 characters where possible

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding/missing tests
- `chore`: Changes to build process or tools

Examples:
```
feat(tasks): add concurrency benchmark tasks
fix(api): handle rate limit errors with exponential backoff
docs(readme): add installation instructions
test(scorer): add unit tests for weighted scoring
```

### Pull Request Process

1. **Fork** the repository (if you don't have write access)
2. **Create a branch** from `main`
3. **Make your changes** following the style guides
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Run tests** locally: `pytest`
7. **Run linter**: `ruff check .`
8. **Commit** with conventional commit messages
9. **Push** to your branch
10. **Open a Pull Request** against `main`
11. **Fill out the PR template** completely
12. **Wait for review** from maintainers
13. **Address feedback** and push additional commits
14. **Squash and merge** when approved

#### PR Requirements

- ✅ All tests pass
- ✅ Code passes linting
- ✅ Documentation updated (if applicable)
- ✅ Conventional commit messages
- ✅ No breaking changes without discussion
- ✅ Signed off on DCO (Developer Certificate of Origin) if required

#### Review Process

- At least 1 approval required for merge
- All conversations must be resolved
- CI must pass
- No merge conflicts

## Development Workflow

### Adding New Tasks

1. Create YAML file in appropriate `tasks/` subdirectory
2. Follow the task schema (see existing tasks for examples)
3. Update `tasks/index.yaml` if adding a new category
4. Test that task loads: `python -c "from src.code_benchmark.task_loader import TaskLoader; from pathlib import Path; print(len(TaskLoader(Path('tasks')).load_all()))"`

### Adding New Models

1. Add model to `config.yaml` under `models.candidates`
2. If model uses different API format, update `src/code_benchmark/api_client.py`
3. Test the model works: `python -c "import asyncio; from src.code_benchmark.api_client import APIClient; from src.code_benchmark.config import Config; asyncio.run(APIClient(Config.load()).call_model('your-model', 'test'))"`

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/code_benchmark

# Run specific test file
pytest tests/test_scorer.py

# Run with verbose output
pytest -v
```

## Getting Help

- Check the [documentation](README.md)
- Search [existing issues](https://github.com/pbedynski-priv/agent-benchmark/issues)
- Ask in [Discussions](https://github.com/pbedynski-priv/agent-benchmark/discussions)

Thank you for contributing! 🎉
