from itertools import chain, combinations
from functools import reduce

"""Export various helper functions that do not fit anywhere else in particular."""

def powerset(iterable):
    """Return the powerset of an iterable as an iterator over tuples."""

    # from https://stackoverflow.com/a/41626759/3042497
    
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def _aux(accumulator, element):
    """Auxilliary function used to quickly merge dictionaries."""
    for key, value in element.items():
        accumulator[key] = accumulator.get(key, 0) + value
    return accumulator


def merge_dicts(d1: dict, d2: dict):
    """Merge two dictionaries."""
    return reduce(_aux, [d1, d2], {})