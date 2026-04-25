def sum_even(n):
    # Bug: range(n-1) misses elements
    evens = []
    for i in range(n - 1):
        if i % 2 == 0:
            evens.append(i)
    return sum(evens)
