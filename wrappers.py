
from typing import *
from inspect import signature
from errors import ValidationError
from itertools import count
from functools import lru_cache, partial, update_wrapper
import inspect
from inspect import Parameter, Signature
import types




class Wrapper:
    '''
    Instances of this class act like "wrappers" for other objects
    A wrapper has the next properties:
    - Has the attributes __name__, __qualname__, __module__, __annotations__,
    __doc__ equal than the wrapped object
    - _str__ & __repr__ returns the same as if you call __str__ and __repr__ in the wrapped object
    '''
    def __init__(self, obj):
        self.obj = obj
        update_wrapper(self, obj)

    @property
    def wrapped(self):
        '''
        :return Returns the callable object wrapped by this instance
        '''
        return self.obj

    def __str__(self):
        return str(self.obj)

    def __repr__(self):
        return repr(self.obj)



class CallableWrapper(Wrapper):
    '''
    Its the same as Wrapper but instances of this class are also callables. When invoked, they call
    the wrapped object with the same arguments.
    '''
    def __init__(self, obj):
        '''
        Initializes this instance.
        :param obj: Is the object to be wrapped. Must be callable
        '''
        assert callable(obj)
        super().__init__(obj)


    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)







class ValidateFuncWrapper(CallableWrapper):
    '''
    An object of this class is a wrapper to a given function but it incorporates
    validation features, such as checking the type of the input arguments or the return
    value
    '''
    def __init__(self, func, options):
        '''
        Initializes this instance.
        :param func: Is the function to be wrapped
        :param options: Must be a dictionary with settings (check the module config)
        '''
        super().__init__(func)
        self.options = options

        # No varadic keyword parameter annotations allowed
        if self.varkwargs_param is not None and self.varkwargs_param.annotation is not Signature.empty:
            raise ValueError('Varadic keyword parameter annotations are not allowed')


    @property
    @lru_cache(maxsize=1)
    def signature(self):
        '''
        Returns the signature of the wrapped function
        '''
        return inspect.signature(self)


    @property
    @lru_cache(maxsize=1)
    def varargs_param(self):
        '''
        Return the parameter (instance of class inspect.Parameter)
        in the signature of the wrapped function which is of type *args
        or None if *args is not in the signature
        '''
        for param in self.signature.parameters.values():
            if param.kind == Parameter.VAR_POSITIONAL:
                return param
        return None


    @property
    @lru_cache(maxsize=1)
    def varkwargs_param(self):
        '''
        Return the parameter (instance of class inspect.Parameter)
        in the signature of the wrapped function which is of type **kwargs
        or None if **kwargs is not in the signature
        '''
        for param in self.signature.parameters.values():
            if param.kind == Parameter.VAR_KEYWORD:
                return param
        return None


    @property
    @lru_cache(maxsize=1)
    def param_validators(self):
        '''
        Returns a list of validators (on for each parameter in the wrapped function signature),
        that will be used to validate the input arguments
        '''
        from parser import parse_annotation

        signature = self.signature
        validators = []

        for param in signature.parameters.values():
            validators.append(parse_annotation(
                Any if param.annotation is Parameter.empty else param.annotation,
                self.options
            ))
        return dict(zip(signature.parameters.keys(), validators))


    @property
    @lru_cache(maxsize=1)
    def return_validator(self):
        '''
        Returns the validator that will be used to validate the return value
        '''
        from parser import parse_annotation

        signature = self.signature
        return parse_annotation(
                Any if signature.return_annotation is Parameter.empty else signature.return_annotation,
                self.options
            )


    def bind(self, *args, **kwargs):
        '''
        Binds the given arguments to the signature of the wrapped function
        (also applies default values)
        '''
        bounded = self.signature.bind(*args, **kwargs)
        bounded.apply_defaults()
        return bounded


    def validate_input(self, *args, **kwargs):
        '''
        Validates the given input arguments.
        Returns a tuple with the values args and kwargs which are the positional and
        keyword arguments that should be passed when calling to the wrapped function
        '''
        if not self.options['match_args']:
            # Dont validate args
            return args, kwargs

        bounded = self.bind(*args, **kwargs)

        args = []
        varargs = []
        varkwargs = {}

        for key, value in bounded.arguments.items():
            param = self.signature.parameters[key]

            if param.kind == Parameter.VAR_KEYWORD:
                # **kwargs
                varkwargs.update(value)

            elif param.kind == Parameter.VAR_POSITIONAL:
                # *args
                if key in self.param_validators and self.options['match_varargs']:
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
        return args, varkwargs



    def validate_output(self, output):
        '''
        Validates the return value (the output of the wrapped function).
        The value returned by this method will be used as the output of the call to
        this wrapper function
        '''
        if not self.options['match_return']:
            # Dont validate output
            return output

        return self.return_validator.validate(
            output,
            context={'func': self.__name__, 'param': 'return value'})


    def __get__(self, obj, objtype):
        options = self.options
        class MethodWrapper(CallableWrapper):
            def __call__(self, obj, *args, **kwargs):
                # Validate 'self' object
                if options['match_self'] and not isinstance(obj, objtype):
                    raise ValidationError(
                        func=self.__name__,
                        param='1st argument',
                        expected='instance of the class {}'.format(objtype.__name__),
                        got=type(obj).__name__ if obj is not None else str(None))

                return super().__call__(obj, *args, **kwargs)

        if obj is None:
            return MethodWrapper(self)
        return types.MethodType(MethodWrapper(self), obj)


    def __call__(self, *args, **kwargs):
        args, kwargs = self.validate_input(*args, **kwargs)
        result = super().__call__(*args, **kwargs)
        result = self.validate_output(result)
        return result
