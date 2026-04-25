def get_element(lst, index):
    # This should return None if index is out of bounds
    if index <= len(lst): # Bug: should be <
        return lst[index]
    return None
