from datasets import Dataset

def build_dataset() -> Dataset:
    """
    Builds the task dataset for GRPO training.
    """
    data = [
        {
            "prompt": "Fix the off-by-one error in this loop.",
            "code": "def count_to_ten():\n    for i in range(10):\n        print(i)",
            "tests": ["def test_count():\n    assert '10' in count_to_ten()"]
        },
        {
            "prompt": "Optimize this Fibonacci function.",
            "code": "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)",
            "tests": ["def test_fib():\n    assert fib(10) == 55"]
        }
    ]
    
    formatted_data = [
        {
            "prompt": [{"role": "system", "content": "You are a Python expert."}, {"role": "user", "content": d["prompt"] + "\n" + d["code"]}]
        }
        for d in data
    ]
    
    return Dataset.from_list(formatted_data)
