import pytest
import math
from initial_code import calculate_area

def test_area():
    assert calculate_area(1) == pytest.approx(math.pi, rel=1e-3)
    assert calculate_area(2) == pytest.approx(math.pi * 4, rel=1e-3)
