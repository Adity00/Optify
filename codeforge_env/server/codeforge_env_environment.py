import os
from uuid import uuid4
import tempfile
import subprocess
from radon.complexity import cc_visit
from radon.metrics import mi_visit

from openenv.core.env_server.interfaces import Environment

try:
    from ..models import CodeforgeAction, CodeforgeObservation, CodeforgeState
except ImportError:
    from models import CodeforgeAction, CodeforgeObservation, CodeforgeState


class CodeforgeEnvironment(Environment):
    """
    CodeForge execution environment.
    Runs code in an isolated manner and extracts static analysis metrics.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = CodeforgeState(episode_id=str(uuid4()), step_count=0)

    def reset(self) -> CodeforgeObservation:
        self._state = CodeforgeState(episode_id=str(uuid4()), step_count=0)
        return CodeforgeObservation()

    def step(self, action: CodeforgeAction) -> CodeforgeObservation:
        self._state.step_count += 1
        
        code = action.code
        
        # Sandbox execution
        stdout_data, stderr_data, exit_code = "", "", 1
        loc = len(code.splitlines())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "solution.py")
            with open(file_path, "w") as f:
                f.write(code)
                
            try:
                result = subprocess.run(
                    ["python", file_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                stdout_data = result.stdout
                stderr_data = result.stderr
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                stderr_data = "Timeout expired"
                exit_code = 124

            # Vulture (dead code)
            dead_code_flags = []
            try:
                v_res = subprocess.run(["vulture", file_path], capture_output=True, text=True)
                if v_res.stdout:
                    dead_code_flags = v_res.stdout.strip().split("\n")
            except Exception:
                pass
                
            # Autoflake (unused imports/vars)
            unused_imports = []
            try:
                a_res = subprocess.run(["autoflake", "--check", file_path], capture_output=True, text=True)
                if a_res.stdout or a_res.stderr:
                    unused_imports = [line for line in (a_res.stdout + a_res.stderr).split("\n") if "Unused" in line]
            except Exception:
                pass

        # Radon metrics
        cc = 0.0
        mi = 0.0
        try:
            blocks = cc_visit(code)
            if blocks:
                cc = sum(b.complexity for b in blocks) / len(blocks)
            mi = mi_visit(code, multi=False)
        except Exception:
            pass
            
        self._state.last_exit_code = exit_code

        return CodeforgeObservation(
            stdout=stdout_data,
            stderr=stderr_data,
            exit_code=exit_code,
            cyclomatic_complexity=cc,
            maintainability_index=mi,
            loc=loc,
            dead_code_flags=dead_code_flags,
            unused_imports=unused_imports,
            lint_results="",
            done=False,
            reward=0.0,
            metadata={"step": self._state.step_count}
        )

    @property
    def state(self) -> CodeforgeState:
        return self._state
