from itertools import ifilter


def first(predicate_or_None, iterable, default=None):
    """
    Returns the first item of iterable for which predicate(item) is true.
    If predicate is None, matches the first item that is true.
    Returns value of default in case of no matching items.
    """
    return next(ifilter(predicate_or_None, iterable), default)


def int_or_0(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def int_or_None(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def get_intervals_overlap(a, b):
    """
    >>> get_overlap([0,  5], [10, 20])
    -5
    >>> get_overlap([0,  9], [10, 20])
    -1
    >>> get_overlap([0,  10], [10, 20])
    0
    >>> get_overlap([0,  15], [10, 20])
    5
    >>> get_overlap([10,  15], [10, 20])
    5
    >>> get_overlap([10,  20], [10, 20])
    10
    >>> get_overlap([15,  20], [10, 20])
    5
    >>> get_overlap([15,  15], [10, 20])
    0
    >>> get_overlap([20, 20], [10, 20])
    0
    >>> get_overlap([20, 20], [10, 20])
    0
    >>> get_overlap([30, 40], [10, 20])
    -10
    """
    return min(a[1], b[1]) - max(a[0], b[0])
