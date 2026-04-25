import subprocess
import tempfile
import os
import shutil
import libcst as cst
from typing import List, Tuple
from .state import TestResult


def run_code(source: str, timeout: int = 5) -> Tuple[str, str, int]:
    """
    Runs source code in a sandboxed temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        solution_path = os.path.join(tmpdir, "solution.py")
        with open(solution_path, "w") as f:
            f.write(source)
        
        try:
            result = subprocess.run(
                ["python", "solution.py"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Execution timed out", 124
        except Exception as e:
            return "", str(e), 1

def run_tests(test_path: str, sandbox_dir: str, timeout: int = 5) -> TestResult:
    """
    Copies test file into sandbox_dir and runs pytest.
    """
    test_filename = "test_solution.py"
    dest_test_path = os.path.join(sandbox_dir, test_filename)
    shutil.copy2(test_path, dest_test_path)
    
    try:
        # Running pytest with short traceback and quiet mode
        result = subprocess.run(
            ["pytest", test_filename, "--tb=short", "-q", "--timeout=5"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=sandbox_dir
        )
        
        stdout = result.stdout
        
        # Robust parsing of pytest summary
        # Example: "2 passed, 1 failed in 0.05s"
        import re
        passed_match = re.search(r'(\d+) passed', stdout)
        failed_match = re.search(r'(\d+) failed', stdout)
        
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        
        # If no summary line, check dots/Fs (fallback)
        if passed == 0 and failed == 0:
            passed = stdout.count('.')
            failed = stdout.count('F')
            
        total = passed + failed
        
        failed_names = []
        # Extract failed test names from traceback (tb=short puts them in lines starting with FAIL)
        for line in stdout.splitlines():
            if line.startswith("FAIL "):
                parts = line.split()
                if len(parts) > 1:
                    failed_names.append(parts[1])

        return TestResult(
            total=total,
            passed=passed,
            failed=failed,
            failed_names=failed_names,
            stdout=stdout
        )
        
    except subprocess.TimeoutExpired:
        # On timeout: return TestResult with all failed + note in stdout
        # We don't know the total, so we use -1 or 0 to indicate unknown
        return TestResult(
            stdout="Execution timed out during tests",
            total=1,
            passed=0,
            failed=1,
            failed_names=["all (timeout)"]
        )
    except Exception as e:
        return TestResult(stdout=f"Test runner error: {str(e)}", total=1, passed=0, failed=1)

def apply_patch(source: str, patch: str, action_type: str) -> str:
    """
    Applies a patch or transformation to the source code.
    """
    result = source
    
    if action_type == "remove_dead_code":
        # Use vulture to find dead lines
        dead_lines = set()
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(source)
            tmp_path = f.name
        try:
            v_result = subprocess.run(["vulture", tmp_path], capture_output=True, text=True)
            for line in v_result.stdout.strip().split('\n'):
                if line and ':' in line:
                    try:
                        line_num = int(line.split(':')[1])
                        dead_lines.add(line_num)
                    except ValueError:
                        pass
        finally:
            os.unlink(tmp_path)
        
        if dead_lines:
            class DeadCodeRemover(cst.CSTTransformer):
                METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)
                
                def __init__(self, lines_to_remove):
                    self.lines_to_remove = lines_to_remove
                    
                def on_leave(self, original_node, updated_node):
                    if isinstance(original_node, (cst.SimpleStatementLine, cst.FunctionDef, cst.ClassDef)):
                        pos = self.get_metadata(cst.metadata.PositionProvider, original_node)
                        if pos.start.line in self.lines_to_remove:
                            return cst.RemoveFromParent()
                    return updated_node

            try:
                tree = cst.parse_module(source)
                wrapper = cst.metadata.MetadataWrapper(tree)
                transformer = DeadCodeRemover(dead_lines)
                result = wrapper.visit(transformer).code
            except Exception:
                pass
                
    elif action_type == "apply_patch":
        # Line-based deletions or simple string replacements
        # Using string diff logic (simplified here as direct replacement if patch provided)
        if patch:
            result = patch
    
    # After applying: validate with libcst.parse_module(result)
    try:
        cst.parse_module(result)
    except Exception as e:
        raise SyntaxError(f"Invalid syntax after {action_type}: {str(e)}")
        
    return result
