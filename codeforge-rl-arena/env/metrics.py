"""
CodeForge Metrics Scaffolding Module — Person 2 Deliverable.

Statically analyzes Python source code and returns a CodeMetrics dataclass
containing key quality indicators for the RL reward pipeline.

Public API:
    - CodeMetrics                  : dataclass holding all metric fields
    - get_cyclomatic_complexity    : str → float
    - get_maintainability_index    : str → float
    - get_dead_code_lines          : str → int
    - get_unused_imports           : str → int
    - analyze_code(src)            : str → CodeMetrics
    - diff_metrics(a, b)           : (CodeMetrics, CodeMetrics) → dict
    - validate_determinism         : determinism smoke-test helper
"""

from __future__ import annotations

import ast
import os
import subprocess
import tempfile


from radon.complexity import cc_visit
from radon.metrics import mi_visit

import vulture as _vulture_mod


# ---------------------------------------------------------------------------
# 1. CodeMetrics dataclass
# ---------------------------------------------------------------------------

from .state import CodeMetrics


# ---------------------------------------------------------------------------
# 2. Standalone helper functions (Person 2 — Steps 1-3)
# ---------------------------------------------------------------------------

def get_cyclomatic_complexity(source: str) -> float:
    """Return the average cyclomatic complexity across all functions in *source*.

    Uses radon's ``cc_visit``. Returns 0.0 if no functions are found.
    """
    blocks = cc_visit(source)
    if not blocks:
        return 0.0
    return sum(b.complexity for b in blocks) / len(blocks)


def get_maintainability_index(source: str) -> float:
    """Return the maintainability index (0–100) for *source*.

    Uses radon's ``mi_visit`` with ``multi=False`` (single float result).
    """
    return mi_visit(source, multi=False)


def get_dead_code_lines(source: str) -> int:
    """Return the number of dead-code lines detected by vulture.

    Writes *source* to a temp file, runs vulture on it, and counts
    the findings. Tries subprocess first; falls back to the Python API
    if subprocess is blocked (e.g. by Application Control policies).
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False
        ) as f:
            f.write(source)
            tmp_path = f.name

        # Attempt subprocess approach (as specified in Person 2 spec)
        try:
            result = subprocess.run(
                ["vulture", tmp_path],
                capture_output=True,
                text=True,
            )
            lines = [line for line in result.stdout.strip().split("\n") if line]
            return len(lines)
        except (OSError, FileNotFoundError):
            # Fallback: use vulture Python API directly
            v = _vulture_mod.Vulture()
            v.scavenge([tmp_path])
            return len(v.get_unused_code())
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def get_unused_imports(source: str) -> int:
    """Return the count of unused imports detected by autoflake.

    Writes *source* to a temp file, runs autoflake on it, and counts
    occurrences of unused imports. Tries subprocess first; falls back
    to AST-based detection if subprocess is blocked.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False
        ) as f:
            f.write(source)
            tmp_path = f.name

        # Attempt subprocess approach (as specified in Person 2 spec)
        try:
            result = subprocess.run(
                ["autoflake", "--check", tmp_path],
                capture_output=True,
                text=True,
            )
            return result.stdout.count("Unused")
        except (OSError, FileNotFoundError):
            # Fallback: use pyflakes API directly to detect unused imports
            return _count_unused_imports_via_ast(source)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _count_unused_imports_via_ast(source: str) -> int:
    """Fallback: detect unused imports using AST analysis.

    Parses the source, collects all imported names, then checks which
    ones are never referenced in the rest of the code.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0

    # Collect all imported names
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imported_names.add(name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imported_names.add(name)

    # Collect all Name references (excluding the import statements themselves)
    used_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle cases like os.path — the root 'os' is a Name node
            pass

    # Count imports that are never used anywhere
    unused = imported_names - used_names
    return len(unused)


# ---------------------------------------------------------------------------
# 3. analyze_code — unified entry point (Person 2 — Step 4)
# ---------------------------------------------------------------------------

def analyze_code(source: str) -> CodeMetrics:
    """Statically analyze *source* and return a populated :class:`CodeMetrics`.

    If any analysis step raises an exception (e.g. ``SyntaxError`` from
    unparseable source), a sentinel ``CodeMetrics`` with every field set to
    ``-1`` is returned so the training loop never crashes.
    """
    try:
        loc = len([line for line in source.splitlines() if line.strip()])
        cyclomatic_complexity = get_cyclomatic_complexity(source)
        maintainability_index = get_maintainability_index(source)
        dead_code_lines = get_dead_code_lines(source)
        unused_imports = get_unused_imports(source)

        return CodeMetrics(
            loc=int(loc),
            cyclomatic_complexity=float(cyclomatic_complexity),
            maintainability_index=float(maintainability_index),
            dead_code_lines=int(dead_code_lines),
            unused_imports=int(unused_imports),
        )

    except Exception:
        # Never let exceptions propagate to the training loop.
        return CodeMetrics(
            loc=-1,
            cyclomatic_complexity=-1,
            maintainability_index=-1,
            dead_code_lines=-1,
            unused_imports=-1,
        )


# ---------------------------------------------------------------------------
# 4. diff_metrics — delta computation for logging
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
# 5. validate_determinism (Person 2 — Step 5)
# ---------------------------------------------------------------------------

def validate_determinism(source: str, runs: int = 3) -> bool:
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
