

from functools import lru_cache, wraps, update_wrapper
from inspect import signature



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

    You can also tune some variables to change how validation is done in your function
    e.g:
    @checked(ondemand=False)
    def foo(x : Iterable[int]) -> int:
        s = 0
        for item in x:
            s += item
        return s
    '''
    def __init__(self, *args, **kwargs):
        self.func = args[0] if len(args) == 1 and callable(args[0]) else None
        self.args, self.kwargs = (args, kwargs) if self.func is None else ((), {})
        if self.func is not None:
            update_wrapper(self, self.func)

    def __call__(self, *args, **kwargs):
        if self.func is None:
            if len(args) != 1 or not callable(args[0]):
                raise TypeError(INVALID_USAGE_MESSAGE)

            self.func = args[0]
            return self._wrapper
        return self._wrapper(*args, **kwargs)

    def __str__(self):
        return str(self._wrapper) if self.func is not None else super().__str__()

    def __repr__(self):
        return repr(self._wrapper) if self.func is not None else super().__repr__()

    @property
    @lru_cache(maxsize=1)
    def _wrapper(self):
        assert self.func is not None
        return build_wrapper(self.func, *self.args, **self.kwargs)


def build_wrapper(func, *args, **kwargs):
    if len(args) > 0:
        raise ValueError('Positional arguments are not allowed in @checked decorator. '+
                         'Use keyword arguments instead')
    options = kwargs
    annotations = func.__annotations__

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper