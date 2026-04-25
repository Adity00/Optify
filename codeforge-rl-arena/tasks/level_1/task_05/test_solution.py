try:
    from initial_code import greet
except SyntaxError:
    greet = None

def test_greet():
    assert greet("World") == "Hello World"
