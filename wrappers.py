
from typing import *
from inspect import signature
from errors import ValidationError
from itertools import count
from functools import lru_cache, partial, update_wrapper
from inspect import signature, Parameter, Signature
from parser import parse_annotation
import types



class CallableWrapper:
    '''
    Objects of this class wraps callable objects:
    - Calling this instance will invoke the wrapped callable with the same arguments.
    - Also it has the attributes __name__, __qualname__, __module__, __annotations__,
    __doc__ equal than the wrapped callable.
    - _str__ & __repr__ returns the same as if you call __str__ and __repr__ in the wrapped object
    '''
    def __init__(self, obj):
        '''
        Initializes this instance.
        :param obj: Is the object to be wrapped. Must be callable
        '''
        assert callable(obj)
        self.obj = obj
        update_wrapper(self, obj)


    @property
    def wrapped(self):
        '''
        :return Returns the callable object wrapped by this instance
        '''
        return self.obj


    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)


    def __str__(self):
        return str(self.obj)

    def __repr__(self):
        return repr(self.obj)





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


    def get_validators(self, options):
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
                    Any if param.annotation is Parameter.empty else param.annotation,
                    options
                )
        param_validators = dict(zip(self.parameters.keys(), get_param_validators()))

        # Get return validator
        ret_validator = parse_annotation(
                Any if self.return_annotation is Parameter.empty else self.return_annotation,
                options
            )

        return param_validators, ret_validator



class ValidateFuncWrapper(CallableWrapper):
    def __init__(self, func, options):
        super().__init__(func)
        self.options = options

        # Get function signature
        self.signature = SignatureMixin(signature(self))

        # No varadic keyword parameter annotations allowed
        if self.signature.varkwargs_param is not None and self.signature.varkwargs_param.annotation is not Signature.empty:
            raise ValueError('Varadic keyword parameter annotations are not allowed')

        # Turn annotations into validators
        self.param_validators, self.return_validator = self.signature.get_validators(self.options)


    def __get__(self, obj, objtype):
        if obj is None:
            return self
        return types.MethodType(self, obj)


    def __call__(self, *args, **kwargs):
        '''
        This method is called when the user invokes the wrapped function
        '''
        # Bind arguments like if we call to the wrapped function
        bounded = self.signature.bind(*args, **kwargs)

        # Apply function default values
        bounded.apply_defaults()

        # Validate each argument
        if self.options.match_args:
            args = []
            varargs = []
            varkwargs = bounded.kwargs

            for key, value in bounded.arguments.items():
                param = self.signature.parameters[key]

                if param.kind == Parameter.VAR_KEYWORD:
                    # **kwargs
                    continue
                if param.kind == Parameter.VAR_POSITIONAL:
                    # *args
                    if key in self.param_validators and self.options.match_varargs:
                        validate = partial(self.param_validators[key].validate, context={'func': self.__name__, 'param': 'items on *{}'.format(key)})
                        varargs.extend(map(validate, value))
                    else:
                        # *args items will not be validated
                        varargs.extend(value)
                else:
                    # Regular argument
                    validate = partial(self.param_validators[key].validate, context={'func': self.__name__, 'param': key})
                    args.append(validate(value))
            args += varargs

        else:
            # No validation is performed on input arguments
            args = bounded.args

        # Now call the wrapped function
        result = super().__call__(*args, **kwargs)

        if self.options.match_return:
            # Validate the return value
            result = self.return_validator.validate(result, context={'func': self.__name__, 'param': 'return value'})

        # Return the final output
        return result
