

from functools import lru_cache, wraps, update_wrapper
from inspect import signature



class checked:
    def __init__(self, *args, **kwargs):
        self.func = args[0] if len(args) == 1 and callable(args[0]) else None
        self.args, self.kwargs = (args, kwargs) if self.func is None else ((), {})
        if self.func is not None:
            update_wrapper(self, self.func)

    def __call__(self, *args, **kwargs):
        if self.func is None:
            if len(args) != 1 or not callable(args[0]):
                raise TypeError(
                'Invalid usage of the decorator\n'+
                'Correct syntax is:\n\n'
                '@checked\n'
                'def foo(...):\n'
                '    ...\n\n'
                '  or  \n\n'
                '@checked(...)\n'
                'def foo(...):\n'
                '    ...\n')

            self.func = args[0]
            return self._wrapper
        return self._wrapper(*args, **kwargs)

    def __str__(self):
        return str(self.func) if self.func is not None else super().__str__()

    def __repr__(self):
        return repr(self.func) if self.func is not None else super().__repr__()

    @property
    @lru_cache(maxsize=1)
    def _wrapper(self):
        assert self.func is not None

        @wraps(self.func)
        def foo(*args, **kwargs):
            return self.func(*args, **kwargs)
        return foo
