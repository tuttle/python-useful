from collections import defaultdict


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
