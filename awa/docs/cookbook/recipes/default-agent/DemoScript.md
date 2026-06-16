# PydanticAI Agent Workflow - Example Usage

This example demonstrates the PydanticAI Agent Workflow autonomously building a complete Python project with implementation, tests, and documentation.

## Example Prompt

The following prompt instructs the agent to build a math calculator project:

```markdown
# AGENT IDENTITY

You are an autonomous desktop automation agent. You execute tasks by using Desktop Commander MCP tools
to perform real file operations, process execution, and system management.

## Core Rules

1. **Execute, Don't Describe**: Use your tools to perform actual operations, not just describe them
2. **Track Progress Forward**: Check existing `task_checklist.md` - if items are checked (✅), skip them and work on unchecked items only
3. **Handle Errors Gracefully**: If a tool fails, try alternatives (max 3 attempts), then move to the next task
4. **Verify Your Work**: After creating/modifying files, read them back to confirm success

## Working Directory

/Users/robert.forshier/Projects/AWA/agentic-workflow-accelerator

## Progress Tracking

- **First action**: Check if `task_checklist.md` exists and read it
- **If it doesn't exist**: Create it with all tasks below as `- [ ] Task description`
- **If it exists**: Read it to see what's done (✅) and what needs work ([ ])
- **After completing each task**: Use rewrite tool to change `[ ]` to `[✅]` for that task only
- **NEVER uncheck completed items** - only work on unchecked tasks

## Tasks to Execute

1. Initialize progress tracking (create task_checklist.md if needed)
2. Create project structure:
   - Create `math_calculator/` directory
   - Create `math_calculator/src`, `math_calculator/tests`, `math_calculator/results` subdirectories
   - Verify directories exist
3. Write Python implementation:
   - Create `math_calculator/src/big_math.py` with:
     - `add_big_numbers(a: int, b: int) -> int`
     - `multiply_big_numbers(a: int, b: int) -> int`
     - `factorial_big_number(n: int) -> int`
     - Include type hints and docstrings
   - Read file back to verify
4. Create test suite:
   - Write `math_calculator/tests/test_big_math.py` with:
     - Tests for numbers > 10^20
     - Performance/timing tests
   - Read file back to verify
5. Execute and validate:
   - Run: `python math_calculator/tests/test_big_math.py`
   - Save output to `math_calculator/results/test_output.txt`
6. Create documentation:
   - Write `math_calculator/README.md` with project description
   - Write `math_calculator/OPERATIONS_SUMMARY.md` documenting MCP tools used

## Success Criteria

Complete when all tasks in `task_checklist.md` are marked with ✅ and all files exist with proper content.
```

## Execution

```bash
uv run -m awa.main run -w "awa-agent-mode-pydantic-ai"
```

## Generated Output

The agent autonomously created the following complete project structure:

```
math_calculator/
├── src/
│   └── big_math.py
├── tests/
│   └── test_big_math.py
├── results/
│   └── test_output.txt
├── README.md
└── OPERATIONS_SUMMARY.md
```

### Task Checklist (`task_checklist.md`)

```markdown
- [✅] Initialize progress tracking (create task_checklist.md if needed)
- [✅] Create project structure:
  - Create `math_calculator/` directory
  - Create `math_calculator/src`, `math_calculator/tests`, `math_calculator/results` subdirectories
  - Verify directories exist
- [✅] Write Python implementation:
  - Create `math_calculator/src/big_math.py` with:
    - `add_big_numbers(a: int, b: int) -> int`
    - `multiply_big_numbers(a: int, b: int) -> int`
    - `factorial_big_number(n: int) -> int`
    - Include type hints and docstrings
  - Read file back to verify
- [✅] Create test suite:
  - Write `math_calculator/tests/test_big_math.py` with:
    - Tests for numbers > 10^20
    - Performance/timing tests
  - Read file back to verify
- [✅] Execute and validate:
  - Run: `python math_calculator/tests/test_big_math.py`
  - Save output to `math_calculator/results/test_output.txt`
- [✅] Create documentation:
  - Write `math_calculator/README.md` with project description
  - Write `math_calculator/OPERATIONS_SUMMARY.md` documenting MCP tools used
```

### Implementation (`src/big_math.py`)

```python
def add_big_numbers(a: int, b: int) -> int:
    """Add two big integers."""
    return a + b

def multiply_big_numbers(a: int, b: int) -> int:
    """Multiply two big integers."""
    return a * b

def factorial_big_number(n: int) -> int:
    """Compute factorial of integer n (n!)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    return math.factorial(n)
```

### Test Suite (`tests/test_big_math.py`)

```python
class TestBigMath(unittest.TestCase):
    def test_add_large_numbers(self):
        a = 10**50
        b = 10**50
        expected = 2 * 10**50
        self.assertEqual(add_big_numbers(a, b), expected)

    def test_multiply_large_numbers(self):
        a = 10**25
        b = 10**25
        expected = 10**50
        self.assertEqual(multiply_big_numbers(a, b), expected)

    def test_factorial_large_number(self):
        n = 100
        expected = math.factorial(100)
        self.assertEqual(factorial_big_number(n), expected)

    def test_performance_add(self):
        # Performance test with 10^1000 numbers
        ...
```

### Test Results (`results/test_output.txt`)

```
......
----------------------------------------------------------------------
Ran 6 tests in 0.001s

OK
Addition with very large numbers took 0.0002 seconds for 1000 runs
Factorial of 5000 took 0.0009 seconds
```

### Operations Summary (`OPERATIONS_SUMMARY.md`)

The agent documented every MCP tool it used:

- `read_file` - Verified file contents
- `write_file` - Created all source files
- `create_directory` - Built project structure
- `start_process`/`read_process_output` - Executed tests
- `edit_block` - Updated task checklist
- `list_directory`/`get_file_info` - Verified structure

### README (`README.md`)

````markdown
# Math Calculator

## Project Description

The Math Calculator project provides high-precision mathematical operations implemented in Python. The main module (`big_math.py`) supports operations on extremely large integers, including addition, multiplication, and factorial calculation. The calculator is designed for reliability and performance, making it suitable for computational tasks involving very large numbers.

### Structure

- **src/**: Contains implementation code.
- **tests/**: Test suites, including performance and high-value tests.
- **results/**: Stores test outputs.

### Main Features

- Arithmetic with numbers greater than 10^20
- Factorial calculations with big numbers
- Performance and correctness validation through unit tests

## Usage

Run the test suite with:

```bash
python math_calculator/tests/test_big_math.py
```
````

Results are output to `math_calculator/results/test_output.txt`.

## Summary

This example demonstrates the PydanticAI Agent Workflow's ability to autonomously:

- Interpret complex task requirements from a detailed prompt
- Create complete project structures with proper organization
- Write production-quality code with type hints and documentation
- Generate comprehensive test suites with performance benchmarks
- Execute tests and capture results
- Document both the implementation and the automation process itself

The agent leverages Desktop Commander's MCP tools to perform real file operations, execute commands, and validate its work - functioning as an autonomous developer within the AWA framework.
