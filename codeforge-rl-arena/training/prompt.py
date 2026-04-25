SYSTEM_PROMPT = """You are an expert software engineer participating in a coding arena.
Your task is to fix bugs, optimize performance, and improve the cleanliness of the provided Python code.

Format your response as a valid Python code block.
```python
# your code here
```
"""

def build_prompt(task_description: str, code: str) -> str:
    return f"""Task: {task_description}

Code:
```python
{code}
```

Please provide the corrected and optimized code."""
