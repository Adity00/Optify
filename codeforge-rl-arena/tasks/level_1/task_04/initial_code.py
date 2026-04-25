def sum_even(n):
    # Redundant list creation before summing
    evens = []
    for i in range(n):
        if i % 2 == 0:
            evens.append(i)
    return sum(evens)
