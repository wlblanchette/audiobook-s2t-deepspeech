from functools import reduce

def dedupe_list(l, accessor=lambda x: x):
    keys = {}

    def reducer(accum, item):
        if accessor(item) in keys:
            return accum
        keys[accessor(item)] = accessor(item)
        return accum + [item]

    return reduce(reducer, l, [])
