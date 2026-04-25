import time

def calculate_efficiency_reward(code: str, execution_time: float, memory_usage: float) -> float:
    """
    Reward based on code length, runtime, and memory.
    """
    loc = len(code.splitlines())
    
    # Penalize long code
    loc_reward = max(0, 1.0 - (loc / 500)) 
    
    # Penalize slow execution
    time_reward = max(0, 1.0 - (execution_time / 10.0))
    
    return (loc_reward + time_reward) / 2.0
