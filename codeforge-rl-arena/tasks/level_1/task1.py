# Level 1 Task: Simple bug fix
task_config = {
    "task_id": "lvl1_001",
    "description": "Fix the IndexError in the list access.",
    "code": "def get_last_element(lst):\n    return lst[len(lst)]",
    "tests": [
        "from solution import get_last_element",
        "def test_last():",
        "    assert get_last_element([1, 2, 3]) == 3"
    ]
}
