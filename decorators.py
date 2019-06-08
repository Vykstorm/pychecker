

from typing import *
from functools import lru_cache, wraps, update_wrapper, partial
from itertools import count
from inspect import signature, Parameter, Signature
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







class SignatureMixin:
    '''
    Helper class that provides additional helper methods over inspect.Signature
    class to parse function annotations to validators
    '''
    def __init__(self, sig):
        self.sig = sig

    def __getattr__(self, key):
        return getattr(self.sig, key)

    def __str__(self):
        return str(self.sig)

    def __repr__(self):
        return repr(self.sig)


    @property
    @lru_cache(maxsize=1)
    def varargs_param(self):
        # Return the parameter in the signature which is of type *args
        # or None if *args is not in the signature
        for param in self.parameters.values():
            if param.kind == Parameter.VAR_POSITIONAL:
                return param
        return None

    @property
    @lru_cache(maxsize=1)
    def varkwargs_param(self):
        # Return the parameter in the signature which is of type **kwargs
        # or None if **kwargs is not in the signature
        for param in self.parameters.values():
            if param.kind == Parameter.VAR_KEYWORD:
                return param
        return None


    @property
    def validators(self):
        '''
        Parse signature annotations to validators
        Return a tuple of two items:
        - A dictionary that maps parameter names to validators
        - Validator obtained parsing function return annotation
        '''

        # Get param validators
        def get_param_validators():
            for param in self.parameters.values():
                yield parse_annotation(
                    Any if param.annotation is Parameter.empty else param.annotation
                )
        param_validators = dict(zip(self.parameters.keys(), get_param_validators()))

        # Get return validator
        ret_validator = parse_annotation(
                Any if self.return_annotation is Parameter.empty else self.return_annotation
            )

        return param_validators, ret_validator




def build_wrapper(func, *args, **kwargs):
    if len(args) > 0:
        raise ValueError('Positional arguments are not allowed in @checked decorator. '+
                         'Use keyword arguments instead')

    # Configure wrapper
    options = kwargs

    # Get function signature
    sig = SignatureMixin(signature(func))

    # No varadic keyword parameter annotations allowed
    if sig.varkwargs_param is not None and sig.varkwargs_param.annotation is not Signature.empty:
        raise ValueError('Varadic keyword parameter annotations are not allowed')

    # Turn annotations into validators
    param_validators, return_validator = sig.validators


    # Validated function definition
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Bind arguments like if we call to the wrapped function
        bounded = sig.bind(*args, **kwargs)

        # Apply function default values
        bounded.apply_defaults()

        # Validate each argument
        args = []
        varargs = []
        varkwargs = bounded.kwargs

        for key, value in bounded.arguments.items():
            context = {'func': func.__name__, 'param': key}
            param = sig.parameters[key]

            if param.kind == Parameter.VAR_KEYWORD:
                # **kwargs
                continue
            if param.kind == Parameter.VAR_POSITIONAL:
                # *args
                if key in param_validators:
                    validate = partial(param_validators[key].validate, context={'func': func.__name__, 'param': 'items on *{}'.format(key)})
                    varargs.extend(map(validate, value))
                else:
                    # *args items will not be validated
                    varargs.extend(value)
            else:
                # Regular argument
                validate = partial(param_validators[key].validate, context={'func': func.__name__, 'param': key})
                args.append(validate(value))

        # Now call the wrapped function
        result = func(*(args + varargs), **kwargs)

        # Finally validate the return value
        result = return_validator.validate(result, context={'func': func.__name__, 'param': 'return value'})

        # Return the final output
        return result

    return wrapper
