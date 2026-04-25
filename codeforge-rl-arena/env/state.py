from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class CodeMetrics:
    loc: int = 0
    cyclomatic_complexity: float = 0.0
    maintainability_index: float = 0.0
    dead_code_lines: int = 0
    unused_imports: int = 0
    runtime_ms: float = 0.0
    memory_kb: float = 0.0

@dataclass
class TestResult:
    total: int = 0
    passed: int = 0
    failed: int = 0
    failed_names: List[str] = field(default_factory=list)
    stdout: str = ""

@dataclass
class Observation:
    source_code: str = ""
    test_result: TestResult = field(default_factory=TestResult)
    metrics: CodeMetrics = field(default_factory=CodeMetrics)
    baseline_metrics: CodeMetrics = field(default_factory=CodeMetrics)
    previous_attempts: List[str] = field(default_factory=list)  # capped at 3
    action_history: List[str] = field(default_factory=list)
    done: bool = False
    reward: float = 0.0
    info: Dict[str, Any] = field(default_factory=dict)
