def used_function(x):
    # Bug: should be x + 1
    return x + 2

def unused_function():
    return "I am never used"

if __name__ == "__main__":
    print(used_function(5))
