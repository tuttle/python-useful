from collections import defaultdict
import itertools
import operator


def count_by_attr(iterable, by):
    d = defaultdict(int)
    for obj in iterable:
        key = getattr(obj, by)
        d[key] += 1
    return d


def dict_by_attr(iterable, by, get=None, default_factory=None):
    if default_factory is not None:
        d = defaultdict(default_factory)
    else:
        d = {}

    for obj in iterable:
        key = getattr(obj, by)
        if get is not None:
            obj = getattr(obj, get)
        d[key] = obj

    return d


def group_by_attr(iterable, by, get=None):
    d = defaultdict(list)
    for obj in iterable:
        key = getattr(obj, by)
        if get is not None:
            obj = getattr(obj, get)
        d[key].append(obj)
    return d


def iter_compare_dicts(dict1, dict2, only_common_keys=False, comparison_op=operator.ne):
    """
    A generator for comparation of values in the given two dicts.

    Yields the tuples (key, pair of values positively compared).

    By default, the *difference* of values is evaluated using the usual != op, but can be changed
    by passing other comparison_op (a function of two arguments returning True/False).

    For example: operator.eq for equal values, operator.is_not for not identical objects.

    You can also require comparison only over keys existing in both dicts (only_common_keys=True).
    Otherwise, you will get the pair with the Python built-in Ellipsis placed for dict with
    that key missing. (Be sure to test for Ellipsis using the 'is' operator.)

    >>> d1 = dict(a=1, b=2, c=3)
    >>> d2 = dict(a=1, b=20, d=4)
    >>> dict(iter_compare_dicts(d1, d2, only_common_keys=True))
    {'b': (2, 20)}
    >>> dict(iter_compare_dicts(d1, d2, only_common_keys=True, comparison_op=operator.eq))
    {'a': (1, 1)}
    >>> dict(iter_compare_dicts(d1, d2))
    {'c': (3, Ellipsis), 'b': (2, 20), 'd': (Ellipsis, 4)}
    >>> dict(iter_compare_dicts(d1, d2, comparison_op=operator.eq))
    {'a': (1, 1), 'c': (3, Ellipsis), 'd': (Ellipsis, 4)}
    """
    keyset1, keyset2 = set(dict1), set(dict2)

    for key in (keyset1 & keyset2):
        pair = (dict1[key], dict2[key])
        if reduce(comparison_op, pair):
            yield key, pair

    if not only_common_keys:
        for key in (keyset1 - keyset2):
            yield key, (dict1[key], Ellipsis)
        for key in (keyset2 - keyset1):
            yield key, (Ellipsis, dict2[key])


def iter_ibatches(iterable, size):
    """
    http://code.activestate.com/recipes/303279-getting-items-in-batches/

    Generates iterators of elements of fixed size from the source iterable. Does not create batch sequences in memory.
    The source iterable can be of an unknown arbitrary length, does not need to support anything else than iteration.
    itertools.islice provides a size-bounded iterator over the given iterator.

    To know when we're done batching is the tricky part, as islice is happy to continue returning empty iterators
    on source exhaustion. We never want to yield an empty iterator. So we try to consume each batch a bit, which
    possibly raises StopIteration stopping the generator function itself.

    WARNING:
    Each batch must be entirely consumed before proceeding to the next one, otherwise you will get unexpected behaviour!

    >>> for b in iter_ibatches(xrange(55), 10):
    ...     print tuple(b)
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
    (10, 11, 12, 13, 14, 15, 16, 17, 18, 19)
    (20, 21, 22, 23, 24, 25, 26, 27, 28, 29)
    (30, 31, 32, 33, 34, 35, 36, 37, 38, 39)
    (40, 41, 42, 43, 44, 45, 46, 47, 48, 49)
    (50, 51, 52, 53, 54)

    """
    it = iter(iterable)
    while True:
        batch_it = itertools.islice(it, size)
        yield itertools.chain([batch_it.next()], batch_it)
