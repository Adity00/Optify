import os
import json
import tempfile
from enum import Enum
from typing import Tuple, List, Optional
from uuid import uuid4
import libcst as cst


from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State as OpenEnvState

from .state import Observation, CodeMetrics, TestResult
from .sandbox import run_tests, apply_patch, run_code
from .metrics import analyze_code

class ActionType(Enum):
    APPLY_PATCH = "apply_patch"           # apply a code change
    REMOVE_DEAD_CODE = "remove_dead_code" # delete unused function/var
    REMOVE_UNUSED_IMPORTS = "remove_unused_imports"
    RENAME_VARIABLE = "rename_variable"   # libcst rename
    EXTRACT_FUNCTION = "extract_function" # pull repeated block into helper
    OPTIMIZE_LOOP = "optimize_loop"       # algorithmic improvement
    REVERT = "revert"                     # undo last action
    RUN_TESTS = "run_tests"               # observe test state without changing code
    ADD_DOCSTRING = "add_docstring"
    NO_OP = "no_op"                       # explicit do-nothing (penalised)

class SyntaxPenalty(Exception):
    pass

class CodeForgeEnv(Environment):
    """
    CodeForge RL Arena Environment Implementation.
    """
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = OpenEnvState(episode_id=str(uuid4()), step_count=0)
        self.source_code = ""
        self.history = [] # Stack for REVERT (last 3 source states)
        self.action_history = []
        self.previous_attempts = [] # capped at 3
        self.baseline_metrics = None
        self.task = None



    def reset(self, task) -> Observation:
        self._state = OpenEnvState(episode_id=str(uuid4()), step_count=0)
        self.task = task
        self.source_code = task.initial_code
        self.baseline_metrics = analyze_code(self.source_code)
        self.previous_attempts = []
        self.action_history = []
        self.history = [self.source_code] # Stack for revert
        
        with tempfile.TemporaryDirectory() as sandbox_dir:
            initial_test = run_tests(task.test_path, sandbox_dir)
            
        return Observation(
            source_code=self.source_code,
            test_result=initial_test,
            metrics=self.baseline_metrics,
            baseline_metrics=self.baseline_metrics,
        )

    def step(self, model_output: str) -> Tuple[Observation, float, bool, dict]:
        """
        Critical step function following the exact flow:
        1. parse_action -> 2. apply_patch -> 3. run_tests -> 4. analyze_code -> 5. build Obs -> 6. check done
        """
        self._state.step_count += 1
        
        try:
            # 1. parse_action(model_output)
            try:
                action_data = json.loads(model_output)
                action_type_str = action_data.get("action")
                action_type = ActionType(action_type_str)
                patch = action_data.get("patch", "")
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                raise SyntaxPenalty(f"Malformed JSON or invalid action: {str(e)}")

            # 7. Implement REVERT action
            if action_type == ActionType.REVERT:
                if len(self.history) > 1:
                    self.history.pop() # Remove current
                    self.source_code = self.history[-1]
                
                with tempfile.TemporaryDirectory() as sandbox_dir:
                    test_result = run_tests(self.task.test_path, sandbox_dir)
                metrics = analyze_code(self.source_code)
                
                return self._finalize_step(test_result, metrics, reward=0.0)

            # 2. apply_patch(source_code, action.patch, action.type)
            # Raises SyntaxError if libcst parse fails
            updated_code = apply_patch(self.source_code, patch, action_type.value)

            # 3. run_tests(task.test_path, sandbox_dir)
            with tempfile.TemporaryDirectory() as sandbox_dir:
                # Agent must never see or modify the original, handled in run_tests
                # We need the code file in sandbox_dir for pytest to find it
                with open(os.path.join(sandbox_dir, "solution.py"), "w") as f:
                    f.write(updated_code)
                test_result = run_tests(self.task.test_path, sandbox_dir)

            # 4. analyze_code(updated_code)
            metrics = analyze_code(updated_code)

            # Update persistent state
            self.source_code = updated_code
            self.history.append(updated_code)
            if len(self.history) > 4: # Store last 3 + current
                self.history.pop(0)
            
            # 5. build new Observation (append to previous_attempts capped at 3)
            self.previous_attempts.append(updated_code)
            if len(self.previous_attempts) > 3:
                self.previous_attempts.pop(0)
            
            self.action_history.append(action_type.value)

            # 6. check done condition
            done = (
                test_result.passed == test_result.total and test_result.total > 0
                and any([
                    metrics.loc < self.baseline_metrics.loc,
                    metrics.cyclomatic_complexity < self.baseline_metrics.cyclomatic_complexity,
                    metrics.dead_code_lines == 0 and self.baseline_metrics.dead_code_lines > 0, # Placeholder logic
                ])
            )

            reward = 1.0 if done else 0.0 # Reward logic to be refined by Person 2
            
            return self._finalize_step(test_result, metrics, reward, done)

        except SyntaxPenalty as e:
            return self._build_error_obs(reward=-1.0, info={"error": str(e), "type": "SyntaxPenalty"})
        except SyntaxError as e:
            return self._build_error_obs(reward=-0.5, info={"error": str(e), "type": "SyntaxError"})
        except Exception as e:
            return self._build_error_obs(reward=-1.0, info={"error": str(e), "type": "InternalError"})

    def _finalize_step(self, test_result, metrics, reward, done=False):
        obs = Observation(
            source_code=self.source_code,
            test_result=test_result,
            metrics=metrics,
            baseline_metrics=self.baseline_metrics,
            previous_attempts=self.previous_attempts,
            action_history=self.action_history[-3:],
            done=done,
            reward=reward
        )
        return obs, reward, done, {}

    def _build_error_obs(self, reward: float, info: dict) -> Tuple[Observation, float, bool, dict]:
        # Return state without updating source_code
        with tempfile.TemporaryDirectory() as sandbox_dir:
            test_result = run_tests(self.task.test_path, sandbox_dir)
        metrics = analyze_code(self.source_code)
        obs = Observation(
            source_code=self.source_code,
            test_result=test_result,
            metrics=metrics,
            baseline_metrics=self.baseline_metrics,
            previous_attempts=self.previous_attempts,
            action_history=self.action_history[-3:],
            done=False,
            reward=reward,
            info=info
        )
        return obs, reward, False, info

    @property
    def state(self) -> OpenEnvState:
        return self._state
