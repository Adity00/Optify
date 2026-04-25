from __future__ import annotations

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient

from .models import CodeforgeAction, CodeforgeObservation, CodeforgeState

class CodeforgeEnvClient(EnvClient[CodeforgeAction, CodeforgeObservation, CodeforgeState]):

    def _step_payload(self, action: CodeforgeAction) -> dict:
        return {
            "code": action.code,
        }

    def _parse_result(self, payload: dict) -> StepResult[CodeforgeObservation]:
        obs = CodeforgeObservation(**payload["observation"])
        return StepResult(
            observation=obs,
            reward=payload.get("reward"),
            done=bool(payload.get("done", False)),
        )

    def _parse_state(self, payload: dict) -> CodeforgeState:
        return CodeforgeState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            last_exit_code=payload.get("last_exit_code", 0),
            total_tests=payload.get("total_tests", 0),
            passed_tests=payload.get("passed_tests", 0),
        )
