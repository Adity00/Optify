import subprocess
import tempfile
import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    passed_tests: int = 0
    total_tests: int = 0
    timed_out: bool = False

def run_in_sandbox(code: str, tests: List[str], timeout: int = 10) -> ExecutionResult:
    """
    Runs code and tests in a temporary directory using pytest.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = os.path.join(tmpdir, "solution.py")
        test_path = os.path.join(tmpdir, "test_solution.py")
        
        with open(code_path, "w") as f:
            f.write(code)
            
        with open(test_path, "w") as f:
            f.write("\n\n".join(tests))
            
        try:
            # Using pytest-timeout as requested
            result = subprocess.run(
                ["pytest", test_path, f"--timeout={timeout}", "--json-report"],
                capture_output=True,
                text=True,
                timeout=timeout + 5
            )
            
            # TODO: Parse json-report if available for detailed metrics
            return ExecutionResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                stdout="",
                stderr="Timeout expired",
                exit_code=1,
                timed_out=True
            )
