from initial_code import get_element

def test_get_element():
    assert get_element([1, 2, 3], 0) == 1
    assert get_element([1, 2, 3], 2) == 3
    assert get_element([1, 2, 3], 3) == None # This will fail
