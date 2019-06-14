

from typing import *
from functools import lru_cache
from config import settings, Settings
from wrappers import ValidateFuncWrapper


INVALID_USAGE_MESSAGE = '''
    Invalid usage of the decorator
    Correct syntax is:
    @checked
    def foo(...):
        ...
      or
    @checked(...)
    def foo(...)
        ...
'''


class checked:
    '''
    Decorator that enables argument & return value validation on the decorated callable
    object (function, method or class)

    e.g:
    @checked
    def foo(x : int, y : int) -> float:
        return x / y
    '''
    def __init__(self, *args, **kwargs):
        self.func = args[0] if len(args) == 1 and callable(args[0]) else None
        self.args, self.kwargs = (args, kwargs) if self.func is None else ((), {})

    def __call__(self, *args, **kwargs):
        if self.func is None:
            if len(args) != 1 or not callable(args[0]):
                raise TypeError(INVALID_USAGE_MESSAGE)

            self.func = args[0]
            return self._wrapper
        return self._wrapper(*args, **kwargs)

    def __get__(self, obj, objtype=None):
        return self._wrapper.__get__(obj, objtype)

    def __getattribute__(self, key):
        try:
            if not key in ['__doc__']:
                return object.__getattribute__(self, key)
            raise AttributeError()
        except:
            return getattr(object.__getattribute__(self, '_wrapper'), key)

    def __str__(self):
        return str(self._wrapper)

    def __repr__(self):
        return repr(self._wrapper)


    @property
    @lru_cache(maxsize=1)
    def _wrapper(self):
        assert self.func is not None

        func = self.func
        args, kwargs = self.args, self.kwargs

        if len(args) > 0:
            raise ValueError('Positional arguments are not allowed in @checked decorator. '+
                             'Use keyword arguments instead')


        # Configure wrapper (arguments override global settings)
        options = settings.copy()
        options.update(kwargs)

        # If validation is disabled, just return the function undecorated
        if not options.enabled:
            return func

        # Decorate function and return wrapper
        return ValidateFuncWrapper(func, options)
