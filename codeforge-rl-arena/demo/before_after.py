import difflib

def generate_diff(before_code: str, after_code: str) -> str:
    """Generates a unified diff for visualization in the UI."""
    diff = difflib.unified_diff(
        before_code.splitlines(),
        after_code.splitlines(),
        fromfile='Before',
        tofile='After',
        lineterm=''
    )
    return '\n'.join(diff)
