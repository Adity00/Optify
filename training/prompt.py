from typing import Any

SYSTEM_PROMPT = """
You are CodeForge, an expert code optimization agent. 
You will be given Python code and a goal. Your job is to iteratively 
improve the code by choosing one action at a time.

Available actions: apply_patch, remove_dead_code, remove_unused_imports,
rename_variable, extract_function, optimize_loop, revert, run_tests,
add_docstring, no_op.

Always respond with valid JSON in this exact format:
{
  "action": "<action_type>",
  "patch": "<the modified code or specific change>",
  "reasoning": "<why you chose this action>"
}
"""

def format_observation(obs: Any) -> str:
    return f"""
Current code:
```python
{obs.source_code}
```
Test results: {obs.test_result.passed}/{obs.test_result.total} passing
Failed tests: {obs.test_result.failed_names}
LOC: {obs.metrics.loc} (baseline: {obs.baseline_metrics.loc})
Complexity: {obs.metrics.cyclomatic_complexity:.1f} (baseline: {obs.baseline_metrics.cyclomatic_complexity:.1f})
Dead code lines: {obs.metrics.dead_code_lines}
Unused imports: {obs.metrics.unused_imports}
Previous actions: {obs.action_history[-3:]}
"""
