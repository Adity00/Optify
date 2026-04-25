from typing import Dict, Any, List
from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field

class CodeforgeAction(Action):
    """Action for the Codeforge Env environment."""
    code: str = Field(..., description="The code to execute or analyze.")

class CodeforgeObservation(Observation):
    """Observation from the Codeforge Env environment."""
    stdout: str = Field(default="", description="Standard output from execution")
    stderr: str = Field(default="", description="Standard error from execution")
    exit_code: int = Field(default=0, description="Exit code of the execution")
    
    # CodeForge specific fields
    cyclomatic_complexity: float = Field(default=0.0, description="Average cyclomatic complexity")
    maintainability_index: float = Field(default=0.0, description="Maintainability index")
    loc: int = Field(default=0, description="Lines of code")
    dead_code_flags: List[str] = Field(default_factory=list, description="Vulture dead code findings")
    unused_imports: List[str] = Field(default_factory=list, description="Autoflake unused import findings")
    lint_results: str = Field(default="", description="General linting results")

class CodeforgeState(State):
    """State for Codeforge environment with persistent execution context."""
    last_exit_code: int = 0
    total_tests: int = 0
    passed_tests: int = 0
