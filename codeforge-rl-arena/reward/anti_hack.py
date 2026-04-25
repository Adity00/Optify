import ast

def detect_reward_hacking(code: str) -> bool:
    """
    Detects suspicious patterns like infinite loops or test overrides.
    """
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # Example: check for overwriting builtins or suspicious imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ["sys", "os", "subprocess"]:
                        # Might be hacking, or might be needed. 
                        # This is a simple placeholder.
                        pass
        return False
    except:
        return True # Syntax error is a form of failure
