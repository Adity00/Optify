"""
Test suite for env.metrics — CodeForge metrics scaffolding (Person 2).

Validates analyze_code, standalone helpers, diff_metrics, and
validate_determinism against known code samples covering dead code,
unused imports, LOC counting, complexity, and syntax errors.
"""

import sys
import os

# Ensure the codeforge-rl-arena package root is on sys.path so that
# `from env.metrics import ...` resolves correctly regardless of
# where pytest is invoked from.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from env.metrics import (
    CodeMetrics,
    analyze_code,
    diff_metrics,
    get_cyclomatic_complexity,
    get_dead_code_lines,
    get_maintainability_index,
    get_unused_imports,
    validate_determinism,
)


# -----------------------------------------------------------------------
# Sample code snippets
# -----------------------------------------------------------------------

# Source with 1 dead (unused) function → vulture should flag it
SAMPLE_ONE_DEAD_FUNC = """\
def used():
    return 42

def unused_helper():
    return 99
"""

# Source with 2 unused imports → autoflake should flag them
SAMPLE_TWO_UNUSED_IMPORTS = """\
import os
import sys

def hello():
    return "hello"
"""

# Source with blank lines to verify LOC counting ignores blanks
SAMPLE_WITH_BLANKS = """\
def foo():
    x = 1

    y = 2

    return x + y
"""

# Complex branching for complexity checks
SAMPLE_COMPLEX = """\
def branchy(x):
    if x > 0:
        if x > 10:
            return 'big'
        return 'small'
    elif x == 0:
        return 'zero'
    else:
        return 'neg'
"""

# Clean, simple code
SAMPLE_CLEAN = """\
def add(a, b):
    return a + b
"""

# Syntax error — should return sentinel, never crash
SAMPLE_SYNTAX_ERR = "def broken(: pass"


# -----------------------------------------------------------------------
# Person 2 — Step 6: Required test cases
# -----------------------------------------------------------------------

def test_dead_code_one_dead_function():
    """Source with 1 dead (unused) function → dead_code_lines >= 1."""
    m = analyze_code(SAMPLE_ONE_DEAD_FUNC)
    assert m.dead_code_lines >= 1, (
        f"Expected dead_code_lines >= 1 for source with 1 unused function, "
        f"got {m.dead_code_lines}"
    )


def test_unused_imports_two():
    """Source with 2 unused imports → unused_imports == 2."""
    m = analyze_code(SAMPLE_TWO_UNUSED_IMPORTS)
    assert m.unused_imports == 2, (
        f"Expected unused_imports == 2, got {m.unused_imports}"
    )


def test_loc_ignores_blank_lines():
    """LOC counting should ignore blank lines."""
    m = analyze_code(SAMPLE_WITH_BLANKS)
    # "def foo():", "x = 1", "y = 2", "return x + y" → 4 non-blank lines
    assert m.loc == 4, (
        f"Expected loc == 4 (non-blank lines only), got {m.loc}"
    )


# -----------------------------------------------------------------------
# Additional validation tests
# -----------------------------------------------------------------------

def test_clean_code_metrics():
    """analyze_code(SAMPLE_CLEAN) should return reasonable basic metrics."""
    m = analyze_code(SAMPLE_CLEAN)
    assert isinstance(m, CodeMetrics)
    assert m.cyclomatic_complexity == 1.0, (
        f"Expected CC=1.0 for a single linear function, got {m.cyclomatic_complexity}"
    )
    assert m.loc > 0, f"Expected loc > 0, got {m.loc}"


def test_complex_code_metrics():
    """analyze_code(SAMPLE_COMPLEX) should detect high branching complexity."""
    m = analyze_code(SAMPLE_COMPLEX)
    assert m.cyclomatic_complexity >= 4.0, (
        f"Expected CC >= 4.0, got {m.cyclomatic_complexity}"
    )


def test_syntax_error_returns_sentinel():
    """Unparseable source must NOT raise; it returns all-negative-one metrics."""
    m = analyze_code(SAMPLE_SYNTAX_ERR)
    assert m.loc == -1
    assert m.cyclomatic_complexity == -1
    assert m.maintainability_index == -1
    assert m.dead_code_lines == -1
    assert m.unused_imports == -1


def test_validate_determinism():
    """Repeated analysis of the same source must yield identical results."""
    assert validate_determinism(SAMPLE_COMPLEX) is True


def test_diff_metrics():
    """diff_metrics should compute correct deltas and improvement flag."""
    before = analyze_code(SAMPLE_COMPLEX)
    after = analyze_code(SAMPLE_CLEAN)

    delta = diff_metrics(before, after)

    # Clean code should have fewer LOC than complex code
    assert delta["loc_delta"] > 0, "Expected positive loc_delta (fewer lines)"
    # Clean code should have lower complexity
    assert delta["complexity_delta"] > 0, "Expected positive complexity_delta"
    # At least one metric improved
    assert delta["improved"] is True


# -----------------------------------------------------------------------
# Standalone helper function tests
# -----------------------------------------------------------------------

def test_get_cyclomatic_complexity_standalone():
    """Standalone helper should match analyze_code result."""
    cc = get_cyclomatic_complexity(SAMPLE_COMPLEX)
    assert cc >= 4.0, f"Expected CC >= 4.0, got {cc}"


def test_get_maintainability_index_standalone():
    """MI should return a float in reasonable range."""
    mi = get_maintainability_index(SAMPLE_CLEAN)
    assert 0.0 <= mi <= 100.0, f"Expected MI in [0, 100], got {mi}"


def test_get_dead_code_lines_standalone():
    """Standalone dead-code helper should detect unused function."""
    count = get_dead_code_lines(SAMPLE_ONE_DEAD_FUNC)
    assert count >= 1, f"Expected >= 1 dead code line, got {count}"


def test_get_unused_imports_standalone():
    """Standalone unused-imports helper should detect 2 unused imports."""
    count = get_unused_imports(SAMPLE_TWO_UNUSED_IMPORTS)
    assert count == 2, f"Expected 2 unused imports, got {count}"
