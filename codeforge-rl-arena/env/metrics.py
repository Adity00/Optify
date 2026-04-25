"""
CodeForge Metrics Scaffolding Module.

Statically analyzes Python source code and returns a CodeMetrics dataclass
containing key quality indicators for the RL reward pipeline.

Public API:
    - CodeMetrics         : dataclass holding all metric fields
    - analyze_code(src)   : str → CodeMetrics
    - diff_metrics(a, b)  : (CodeMetrics, CodeMetrics) → dict
    - validate_determinism: determinism smoke-test helper
"""

from __future__ import annotations

import ast
import os
import tempfile
from dataclasses import dataclass

import radon.complexity
import radon.metrics
import radon.raw
import vulture


# ---------------------------------------------------------------------------
# 1. CodeMetrics dataclass
# ---------------------------------------------------------------------------

@dataclass
class CodeMetrics:
    """Container for static-analysis results of a single Python source string."""

    loc: int                        # Logical lines of code (non-blank, non-comment)
    cyclomatic_complexity: float    # Average cyclomatic complexity across all functions
    maintainability_index: float    # Maintainability index (0–100 scale)
    dead_code_lines: int            # Number of unused code lines detected by vulture
    num_functions: int              # Total number of function definitions
    num_classes: int                # Total number of class definitions
    max_complexity: int             # Highest single-function complexity score


# Sentinel returned when analysis fails (e.g. SyntaxError).
_ERROR_METRICS = CodeMetrics(
    loc=-1,
    cyclomatic_complexity=-1,
    maintainability_index=-1,
    dead_code_lines=-1,
    num_functions=-1,
    num_classes=-1,
    max_complexity=-1,
)


# ---------------------------------------------------------------------------
# 2. analyze_code
# ---------------------------------------------------------------------------

def analyze_code(source: str) -> CodeMetrics:
    """Statically analyze *source* and return a populated :class:`CodeMetrics`.

    If any analysis step raises an exception (e.g. ``SyntaxError`` from
    unparseable source), a sentinel ``CodeMetrics`` with every field set to
    ``-1`` is returned so the training loop never crashes.
    """
    try:
        # --- Step A: LOC via radon -------------------------------------------
        raw_metrics = radon.raw.analyze(source)
        loc = raw_metrics.lloc  # logical lines of code

        # --- Step B: Cyclomatic complexity via radon -------------------------
        cc_results = radon.complexity.cc_visit(source)

        if not cc_results:
            cyclomatic_complexity = 0.0
            max_complexity = 0
            num_functions = 0
        else:
            complexities = [block.complexity for block in cc_results]
            cyclomatic_complexity = sum(complexities) / len(complexities)
            max_complexity = max(complexities)
            num_functions = len(cc_results)

        # --- Step C: Maintainability index via radon -------------------------
        mi_score = radon.metrics.mi_visit(source, multi=True)
        # Clamp to [0.0, 100.0] for safety
        maintainability_index = max(0.0, min(100.0, mi_score))

        # --- Step D: Dead code via vulture -----------------------------------
        dead_code_lines = _count_dead_code(source)

        # --- Step E: Class count via ast -------------------------------------
        tree = ast.parse(source)
        num_classes = sum(
            1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        )

        return CodeMetrics(
            loc=int(loc),
            cyclomatic_complexity=float(cyclomatic_complexity),
            maintainability_index=float(maintainability_index),
            dead_code_lines=int(dead_code_lines),
            num_functions=int(num_functions),
            num_classes=int(num_classes),
            max_complexity=int(max_complexity),
        )

    except Exception:
        # Step F — never let exceptions propagate to the training loop.
        return CodeMetrics(
            loc=-1,
            cyclomatic_complexity=-1,
            maintainability_index=-1,
            dead_code_lines=-1,
            num_functions=-1,
            num_classes=-1,
            max_complexity=-1,
        )


def _count_dead_code(source: str) -> int:
    """Run vulture on *source* via a temp file and return the dead-code line count."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False
        ) as tmp:
            tmp.write(source)
            tmp_path = tmp.name

        v = vulture.Vulture()
        v.scavenge([tmp_path])
        return sum(item.size for item in v.get_unused_code())
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# 3. diff_metrics
# ---------------------------------------------------------------------------

def diff_metrics(before: CodeMetrics, after: CodeMetrics) -> dict:
    """Compute deltas between *before* and *after* metrics for logging.

    Returns a dict with:
        - ``loc_delta``        : positive → fewer lines (good)
        - ``complexity_delta`` : positive → lower complexity (good)
        - ``mi_delta``         : positive → better maintainability (good)
        - ``dead_code_delta``  : positive → less dead code (good)
        - ``improved``         : ``True`` if at least one metric improved
    """
    return {
        "loc_delta": before.loc - after.loc,
        "complexity_delta": before.cyclomatic_complexity - after.cyclomatic_complexity,
        "mi_delta": after.maintainability_index - before.maintainability_index,
        "dead_code_delta": before.dead_code_lines - after.dead_code_lines,
        "improved": bool(
            before.loc > after.loc
            or before.cyclomatic_complexity > after.cyclomatic_complexity
            or before.dead_code_lines > after.dead_code_lines
        ),
    }


# ---------------------------------------------------------------------------
# 4. validate_determinism
# ---------------------------------------------------------------------------

def validate_determinism(source: str, runs: int = 5) -> bool:
    """Call :func:`analyze_code` *runs* times and verify all results match.

    Returns ``True`` if deterministic, ``False`` (with a printed warning)
    otherwise.
    """
    results = [analyze_code(source) for _ in range(runs)]
    first = results[0]

    for i, result in enumerate(results[1:], start=2):
        if result != first:
            print(
                f"WARNING: non-deterministic metrics detected on run {i}. "
                f"Expected {first!r}, got {result!r}"
            )
            return False

    return True
