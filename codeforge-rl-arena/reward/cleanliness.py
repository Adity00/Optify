from radon.complexity import cc_visit
import subprocess
import tempfile
import os

def calculate_cleanliness_reward(code: str) -> float:
    """
    Reward based on cyclomatic complexity and dead code.
    """
    # Cyclomatic Complexity
    try:
        blocks = cc_visit(code)
        avg_cc = sum(b.complexity for b in blocks) / len(blocks) if blocks else 1.0
        cc_reward = max(0, 1.0 - (avg_cc / 10.0))
    except:
        cc_reward = 0.0

    # Dead code detection placeholder (requires running vulture on a file)
    return cc_reward
