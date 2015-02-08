from functools import wraps
import hashlib

from django.core import cache  # Importing this way so debug_toolbar can patch it later.
from django.core.cache.backends.base import DEFAULT_TIMEOUT


ALLOWED_CACHED_FUNCTION_ARG_TYPES = set((type(None), int, float, long, bool, str, unicode))


def cached_function(func=None, num_args_to_key=None, timeout=DEFAULT_TIMEOUT):
    """
    We all write this tedious code often::

        key = make_key(arg1, arg2, arg3)
        value = cache.get(key)
        if value is None:
            value = expensive(arg1, arg2, arg3)
            cache.set(key, value, timeout=3600)

        return value

    This decorator tries to remove the need to do this. You only use the following::

        @cached_function(timeout=3600)
        def expensive(arg1, arg2, arg3):
            ...

    To use the Django default timeout, you can omit the arguments::

        @cached_function

    The expensive() must accept the fixed number of positional arguments. All these args must be
    basic and easily repr-esentable Python types, in order a solid cache key can be made from them
    (as well as from the function name and containing module name).

    If you pass arguments to expensive() that do not need to be part of the cache key, put them
    to the end of args and limit the number of key-making args from the left::

        @cached_function(num_args_to_key=2)

    """
    def cached_function_inner(func):
        if func.func_defaults:
            raise RuntimeError("cached_function does not allow function to have default args "
                               "in order to keep the number of passed args fixed.")

        if func.__name__ == '<lambda>':
            raise RuntimeError("cached_function can't work on anonymous funcs in order "
                               "to keep the name unique.")

        @wraps(func)
        def wrapper(*args):
            key_args = args if num_args_to_key is None else args[:num_args_to_key]

            unallowed_types = set(map(type, key_args)) - ALLOWED_CACHED_FUNCTION_ARG_TYPES
            if unallowed_types:
                raise RuntimeError("cached_function received unallowed types of keyable args: %s"
                                   % ', '.join(map(str, unallowed_types)))

            key_fmt = 'cached_function:%s.%s(%%s)' % (func.__module__, func.__name__)
            key = key_fmt % ','.join(map(repr, key_args))

            if len(key) > 200:
                key_args = hashlib.sha256(key_args).hexdigest()
                key = key_fmt % key_args + '-hashed'

            value = cache.cache.get(key)

            if value is None:
                value = func(*args)

                cache.cache.set(key, value, timeout=timeout)

            return value

        return wrapper

    if func is None:
        # @cached_function(...)
        return cached_function_inner

    elif callable(func):
        # @cached_function
        return cached_function_inner(func)

    else:
        raise RuntimeError("Invalid arguments provided to cached_function decorator.")
