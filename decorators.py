

from typing import *
from functools import lru_cache, wraps, update_wrapper, partial
from itertools import count
from inspect import signature, Parameter, Signature
from parser import parse_annotation
import types

from config import settings, Settings
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
        return build_wrapper(self.func, *self.args, **self.kwargs)





class SignatureMixin:
    '''
    Helper class that provides additional helper methods over inspect.Signature
    class to parse function annotations to validators (used to build wrappers
    around decorated functions)
    '''
    def __init__(self, sig):
        self.sig = sig

    def __getattr__(self, key):
        return getattr(self.sig, key)

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
    '''
    Builds a wrapper around the given function to add validation features.
    '''

    if len(args) > 0:
        raise ValueError('Positional arguments are not allowed in @checked decorator. '+
                         'Use keyword arguments instead')

    # Configure wrapper (arguments override global settings)
    options = settings.copy()
    options.update(kwargs)


    # If validation is disabled, we dont decorate the function
    if not options.enabled:
        return func

    # Get function signature
    sig = SignatureMixin(signature(func))

    # No varadic keyword parameter annotations allowed
    if sig.varkwargs_param is not None and sig.varkwargs_param.annotation is not Signature.empty:
        raise ValueError('Varadic keyword parameter annotations are not allowed')

    # Turn annotations into validators
    param_validators, return_validator = sig.validators

    # The wrapper will be an instance of this class
    class Wrapper:
        def __get__(self, obj, objtype):
            if obj is None:
                return self
            return types.MethodType(self, obj)

        def __str__(self):
            return str(func)

        def __repr__(self):
            return repr(func)

        def __call__(self, *args, **kwargs):
            # Bind arguments like if we call to the wrapped function
            bounded = sig.bind(*args, **kwargs)

            # Apply function default values
            bounded.apply_defaults()

            # Validate each argument
            if options.match_args:
                args = []
                varargs = []
                varkwargs = bounded.kwargs

                for key, value in bounded.arguments.items():
                    param = sig.parameters[key]

                    if param.kind == Parameter.VAR_KEYWORD:
                        # **kwargs
                        continue
                    if param.kind == Parameter.VAR_POSITIONAL:
                        # *args
                        if key in param_validators and options.match_varargs:
                            validate = partial(param_validators[key].validate, context={'func': func.__name__, 'param': 'items on *{}'.format(key)})
                            varargs.extend(map(validate, value))
                        else:
                            # *args items will not be validated
                            varargs.extend(value)
                    else:
                        # Regular argument
                        validate = partial(param_validators[key].validate, context={'func': func.__name__, 'param': key})
                        args.append(validate(value))
                args += varargs

            else:
                # No validation is performed on input arguments
                args = bounded.args

            # Now call the wrapped function
            result = func(*args, **kwargs)

            if options.match_return:
                # Validate the return value
                result = return_validator.validate(result, context={'func': func.__name__, 'param': 'return value'})

            # Return the final output
            return result

    # Instantiate the wrapper
    wrapper = Wrapper()

    # Update wrapper properties
    update_wrapper(wrapper, func)

    return wrapper
