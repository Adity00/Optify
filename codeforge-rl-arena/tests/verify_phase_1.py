import sys
import os
import json
from dataclasses import dataclass

# Add the project root and the specific arena folder to sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
arena_path = os.path.join(root, "codeforge-rl-arena")
sys.path.append(root)
sys.path.append(arena_path)

# Try to import from the env folder directly
try:
    from env.codeforge_env import CodeForgeEnv, ActionType
    from env.state import Observation
except ImportError:
    # Fallback if the above fails
    sys.path.append(os.path.join(arena_path, "env"))
    from codeforge_env import CodeForgeEnv, ActionType
    from state import Observation

@dataclass
class Task:
    initial_code: str
    test_path: str

def test_reset():
    print("Testing env.reset()...")
    env = CodeForgeEnv()
    task_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../tasks/level_1/task_01"))
    task = Task(
        initial_code=open(os.path.join(task_dir, "initial_code.py")).read(),
        test_path=os.path.join(task_dir, "test_solution.py")
    )
    obs = env.reset(task)
    assert isinstance(obs, Observation)
    assert obs.baseline_metrics.loc > 0
    assert obs.metrics.loc == obs.baseline_metrics.loc
    print("✓ env.reset() passed.")

def test_revert():
    print("Testing REVERT action...")
    env = CodeForgeEnv()
    task_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../tasks/level_1/task_01"))
    task = Task(
        initial_code=open(os.path.join(task_dir, "initial_code.py")).read(),
        test_path=os.path.join(task_dir, "test_solution.py")
    )
    env.reset(task)
    
    # Modify code
    original_code = env.source_code
    new_code = original_code + "\n# Test Comment"
    env.step(json.dumps({"action": "apply_patch", "patch": new_code}))
    assert env.source_code == new_code
    
    # Revert
    env.step(json.dumps({"action": "revert"}))
    assert env.source_code == original_code
    print("✓ REVERT action passed.")

def verify_tasks():
    print("Verifying level_1 tasks...")
    for i in range(1, 6):
        task_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../tasks/level_1/task_0{i}"))
        assert os.path.exists(task_dir)
    print("✓ 5 level_1 tasks exist.")

if __name__ == "__main__":
    try:
        test_reset()
        test_revert()
        verify_tasks()
        print("\nAll automated checks passed!")
    except Exception as e:
        print(f"\nVerification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
