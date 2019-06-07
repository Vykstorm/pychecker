

from typing import *
from functools import lru_cache, wraps, update_wrapper
from itertools import count
from inspect import signature
from parser import parse_annotation

from errors import ValidationError


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
    # Change validation settings
    options = kwargs

    # Get function annotations & signature
    annotations = func.__annotations__
    sig = signature(func)

    # Replace default values with "Any" validator
    s = sig.replace(parameters=[param.replace(default=parse_annotation(Any)) for key, param in sig.parameters.items()])

    # Parse param annotations to validators and bound them to the function signature
    bounded = s.bind_partial(
        **dict([(key, parse_annotation(annot)) for key, annot in annotations.items() if key != 'return'])
    )
    bounded.apply_defaults()

    param_validators = bounded.args

    # Also parse the return value annotation into a validator
    ret_validator = parse_annotation(annotations['return'] if 'return' in annotations else Any)


    # Validated function definition
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Bind arguments like if we call to the wrapped function
        bounded = sig.bind(*args, **kwargs)

        # Apply function default values
        bounded.apply_defaults()

        # Get bounded args
        args = list(bounded.args)

        # Validate each argument
        for k, param, arg, validator in zip(count(), sig.parameters.keys(), args, param_validators):
            args[k] = validator.validate(arg, context=dict(func=func.__name__, param=param))

        # Now call the wrapped function
        result = func(*args)

        # Finally validate the return value
        result = ret_validator.validate(result, context=dict(func=func.__name__, param='return value'))

        # Return the final output
        return result

    return wrapper
