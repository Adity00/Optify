from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class CodeForgeState:
    episode_id: str
    step_count: int
    code: str = ""
    original_code: str = ""
    tests: List[str] = field(default_factory=list)
    task_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    done: bool = False
    reward: float = 0.0
