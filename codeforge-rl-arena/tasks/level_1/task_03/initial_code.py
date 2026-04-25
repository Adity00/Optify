def used_function(x):
    return x + 1

def unused_function():
    return "I am never used"

if __name__ == "__main__":
    print(used_function(5))
