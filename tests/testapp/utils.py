
from useful.django.caching import cached_function


@cached_function
def expensive_function(*args):
    return len(args)
