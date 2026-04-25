from dataclasses import dataclass
from typing import List
import os
import json
import datasets
from training.prompt import SYSTEM_PROMPT

@dataclass
class Task:
    task_id: str
    initial_code: str
    test_path: str
    goal: str
    difficulty: int          # 1, 2, or 3
    baseline_loc: int
    baseline_complexity: float
    baseline_dead_code: int

def load_tasks(tasks_dir: str, level: int) -> List[Task]:
    path = os.path.join(tasks_dir, f"level_{level}")
    tasks = []
    if not os.path.exists(path):
        return tasks
    
    for task_folder in os.listdir(path):
        folder_path = os.path.join(path, task_folder)
        if os.path.isdir(folder_path):
            code_path = os.path.join(folder_path, "initial_code.py")
            info_path = os.path.join(folder_path, "task_info.json")
            
            if os.path.exists(code_path) and os.path.exists(info_path):
                with open(code_path, "r", encoding="utf-8") as f:
                    initial_code = f.read()
                with open(info_path, "r", encoding="utf-8") as f:
                    info = json.load(f)
                
                tasks.append(Task(
                    task_id=info.get("task_id", task_folder),
                    initial_code=initial_code,
                    test_path=info.get("test_path", f"tests/test_{task_folder}.py"),
                    goal=info.get("goal", ""),
                    difficulty=info.get("difficulty", level),
                    baseline_loc=info.get("baseline_loc", 0),
                    baseline_complexity=info.get("baseline_complexity", 0.0),
                    baseline_dead_code=info.get("baseline_dead_code", 0)
                ))
    return tasks

def build_dataset(tasks: List[Task]) -> datasets.Dataset:
    data = []
    for t in tasks:
        data.append({
            "task_id": t.task_id,
            "prompt": SYSTEM_PROMPT,
            "initial_code": t.initial_code,
            "test_path": t.test_path,
            "goal": t.goal,
            "difficulty": t.difficulty
        })
    return datasets.Dataset.from_list(data)
