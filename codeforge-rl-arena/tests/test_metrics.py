"""
Test suite for env.metrics — CodeForge metrics scaffolding.

Validates analyze_code, diff_metrics, and validate_determinism against
known code samples covering clean code, complex branching, dead code,
and syntax errors.
"""

import sys
import os

# Ensure the codeforge-rl-arena package root is on sys.path so that
# `from env.metrics import ...` resolves correctly regardless of
# where pytest is invoked from.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from env.metrics import CodeMetrics, analyze_code, diff_metrics, validate_determinism


# -----------------------------------------------------------------------
# Sample code snippets
# -----------------------------------------------------------------------

SAMPLE_DEAD = """
def used():
    return 42

def unused_func():
    x = 1  # dead

class UnusedClass:
    pass
"""

SAMPLE_COMPLEX = """
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

SAMPLE_CLEAN = """
def add(a, b):
    return a + b
"""

SAMPLE_SYNTAX_ERR = "def broken(: pass"


# -----------------------------------------------------------------------
# Test 1: clean code metrics
# -----------------------------------------------------------------------

def test_clean_code_metrics():
    """analyze_code(SAMPLE_CLEAN) should return reasonable basic metrics."""
    m = analyze_code(SAMPLE_CLEAN)
    assert isinstance(m, CodeMetrics)
    assert m.cyclomatic_complexity == 1.0, (
        f"Expected CC=1.0 for a single linear function, got {m.cyclomatic_complexity}"
    )
    assert m.loc > 0, f"Expected loc > 0, got {m.loc}"


# -----------------------------------------------------------------------
# Test 2: complex code metrics
# -----------------------------------------------------------------------

def test_complex_code_metrics():
    """analyze_code(SAMPLE_COMPLEX) should detect high branching complexity."""
    m = analyze_code(SAMPLE_COMPLEX)
    assert m.cyclomatic_complexity >= 4.0, (
        f"Expected CC >= 4.0, got {m.cyclomatic_complexity}"
    )
    assert m.max_complexity >= 4, (
        f"Expected max_complexity >= 4, got {m.max_complexity}"
    )


# -----------------------------------------------------------------------
# Test 3: dead code detection
# -----------------------------------------------------------------------

def test_dead_code_detection():
    """analyze_code(SAMPLE_DEAD) should find at least 1 dead-code line."""
    m = analyze_code(SAMPLE_DEAD)
    assert m.dead_code_lines >= 1, (
        f"Expected dead_code_lines >= 1, got {m.dead_code_lines}"
    )


# -----------------------------------------------------------------------
# Test 4: syntax error handling
# -----------------------------------------------------------------------

def test_syntax_error_returns_sentinel():
    """Unparseable source must NOT raise; it returns all-negative-one metrics."""
    m = analyze_code(SAMPLE_SYNTAX_ERR)
    assert m.loc == -1
    assert m.cyclomatic_complexity == -1
    assert m.maintainability_index == -1
    assert m.dead_code_lines == -1
    assert m.num_functions == -1
    assert m.num_classes == -1
    assert m.max_complexity == -1


# -----------------------------------------------------------------------
# Test 5: determinism validation
# -----------------------------------------------------------------------

def test_validate_determinism():
    """Repeated analysis of the same source must yield identical results."""
    assert validate_determinism(SAMPLE_COMPLEX) is True


# -----------------------------------------------------------------------
# Test 6: diff_metrics helper
# -----------------------------------------------------------------------

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
