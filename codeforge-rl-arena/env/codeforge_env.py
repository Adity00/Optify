import os
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State as OpenEnvState

from .state import CodeForgeState
from .sandbox import ExecutionResult, run_in_sandbox

class CodeForgeEnv(Environment):
    """
    CodeForge RL Arena Environment.
    Handles code modification tasks and reward coordination.
    """
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = OpenEnvState(episode_id=str(uuid4()), step_count=0)
        self.forge_state = CodeForgeState(episode_id=self._state.episode_id, step_count=0)

    def reset(self, task_config: Optional[dict] = None) -> CodeForgeState:
        self._state = OpenEnvState(episode_id=str(uuid4()), step_count=0)
        
        # Initialize with task data if provided
        if task_config:
            self.forge_state = CodeForgeState(
                episode_id=self._state.episode_id,
                step_count=0,
                code=task_config.get("code", ""),
                original_code=task_config.get("code", ""),
                tests=task_config.get("tests", []),
                task_id=task_config.get("task_id", "")
            )
        else:
            self.forge_state = CodeForgeState(episode_id=self._state.episode_id, step_count=0)
            
        return self.forge_state

    def step(self, action: dict) -> CodeForgeState:
        """
        Action is expected to be a dict with:
        - type: 'modify' | 'submit'
        - code: new code (if modify)
        """
        self._state.step_count += 1
        self.forge_state.step_count = self._state.step_count
        
        action_type = action.get("type", "submit")
        
        if action_type == "modify":
            self.forge_state.code = action.get("code", self.forge_state.code)
            self.forge_state.done = False
        elif action_type == "submit":
            self.forge_state.done = True
            
        # Reward calculation happens externally or via a reward manager
        return self.forge_state

    @property
    def state(self) -> OpenEnvState:
        return self._state
