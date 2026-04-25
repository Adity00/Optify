from ..env.sandbox import ExecutionResult

def calculate_correctness_reward(result: ExecutionResult) -> float:
    """
    Reward based on test pass rate.
    """
    if result.timed_out:
        return -1.0
    if result.exit_code != 0:
        return 0.0
    
    # Placeholder for pass rate parsing
    # For now, if exit_code is 0, assume all tests passed
    return 1.0
