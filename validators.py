




'''
This script defines all validators used to check function arguments &
return values.

There 3 kind of interfaces a validator can have:

- Simple validator (Only pre-validation & no custom error messages). They
are simple functions that returns True/False if the given argument is
valid or not

e.g:
```
def validate(value : Any) -> bool:
    if isinstance(value, int):
        return True
    return False
```


- Validator with custom error message (Only pre-validation). This is useful if you
want to provide additional information to the user about the validation error

In this scenario, you need to define a generator such that the first iteration
(first value sent via yield) is a boolean value indicating if the given argument is
valid or not.
After executing yield False, you can raise an exception with a custom error message

e.g:
```
def validate(value : Any) -> Generator:
    if isinstance(value, int):
        yield True
        return
    yield False
    raise Exception('? must be a int value')
```
The '?' in the error message is replaced by the parameter name or 'return value' string
A full error message will be:
'Validation error at function bar: x must be a int value'



- The last kind of validator is like the second one, but it allows also to do validation
by demand:
If the argument is valid, you do 'yield True'. After that, you can also
yield another value which will be passed to the body function as a replacement to the
original argument.
With that, you can validate for example the kind of items of an iterable by demand:

e.g: Check if value is an iterable and its elements are all ints
```
def validate(value : Any) -> Generator:
    if not isinstance(value, Iterable):
        yield False
        raise Exception('? is not an iterable')

    yield True

    class Proxy:
        def __iter__(self):
            it = iter(value)
            while True:
                x = next(it)
                if not isinstance(x, int):
                    raise Exception('? is not an iterable of ints')
                yield x
    yield Proxy()
```

'''


from typing import *
from operator import attrgetter
from inspect import signature
from itertools import count


class Validator:
    '''
    Super class for all base validators. Validator dont need to be instances of
    classes, only callables that satisfies one of the three interfaces explained.
    '''
    def __call__(self, value) -> Union[bool, Iterator]:
        '''
        Validates the given argument.
        '''
        raise NotImplementedError()



    def validate(self, value) -> Tuple[bool, Any]:
        '''
        :return A tuple with two items. The first indicates if the given argument
        is valid or not (True or False).
        The second item will be string with the error message provided by this validator
        if the first item is False.
        Otherwise, it must be set to the same value as the given argument being validated
        or a replacement for it (for on-demand validation)
        '''
        result = self(value)
        assert isinstance(result, (bool, Iterator))
        default_msg = '? is not valid'

        if isinstance(result, bool):
            if result:
                return True, value
            return False, default_msg

        valid = next(result)

        if valid:
            try:
                proxy = next(result)
                return True, proxy
            except StopIteration:
                return True, value

        try:
            message = next(result)
        except StopIteration:
            message = default_msg
        except Exception as e:
            message = default_msg if len(e.args) == 0 or not isinstance(e.args[0], str) else e.args[0]
        return False, message


    def brief(self) -> str:
        '''
        This will return a short string message that defines how this instance validates
        the arguments
        '''
        raise NotImplementedError()



class EmptyValidator(Validator):
    '''
    Validator that matches any value
    '''
    def __call__(self, value):
        return True

    def validate(self, value):
        '''
        Overrided method to increase performance
        '''
        return (True, value)


    def brief(self):
        return 'any'


class TypeValidator(Validator):
    '''
    Validator that checks if the given argument matches the expected type(s)
    '''
    def __init__(self, types: Iterable[Type], check_subclasses: bool=True) -> None:
        '''
        Constructor.
        :param types: An iterable with all possible valid types that argument
        must have to pass the test
        :param check_subclasses: If True, the argument will be valid if its an instance
        of a subclass of any of the classes specified in types. Default is True
        '''
        super().__init__()
        self.types = tuple(types)
        self.check_subclasses = check_subclasses
        assert len(self.types) > 0

    def __call__(self, value) -> Generator:
        if self.check_subclasses:
            valid = isinstance(value, self.types)
        else:
            value_type = type(value)
            valid = any(map(lambda t: value_type == t, self.types))

        if not valid:
            yield False
            raise Exception('? must be an {} but got {} instead'.format(
                self.brief(), type(value).__name__))
        yield True

    def brief(self) -> str:
        types = self.types
        if len(types) == 1:
            return types[0].__name__
        return ', '.join(map(attrgetter('__name__'), types[:-1])) + ' or ' + types[-1].__name__




class Proxy:
    def __init__(self, obj) -> None:
        self.obj = obj

    def __str__(self):
        return str(self.obj)

    def __repr__(self):
        return repr(self.obj)


class IteratorProxy(Proxy):
    def __init__(self, obj : Iterator, validator : Validator) -> None:
        super().__init__(obj)
        self.validator = validator

    def __iter__(self):
        return self

    def __next__(self):
        old = next(self.obj)
        valid, new = self.validator.validate(old)
        if not valid:
            raise Exception('? must be an iterator of {} but {} found'.format(self.validator.brief(), type(old).__name__))
        return new


class IterableProxy(Proxy):
    def __init__(self, obj : Iterable, validator : Validator) -> None:
        super().__init__(obj)
        self.validator = validator

    def __iter__(self):
        it = iter(self.obj)
        try:
            while True:
                old = next(it)
                valid, new = self.validator.validate(old)
                if not valid:
                    raise Exception('? must be an iterable of {} but {} found'.format(self.validator.brief(), type(old).__name__))
                yield new
        except StopIteration:
            pass


class CallableProxy(Proxy):
    def __init__(self, obj : Callable, vargs: Optional[List[Validator]]=None, vret: Optional[Validator]=None):
        super().__init__(obj)
        self.signature = signature(self.obj)
        self.vargs = vargs
        self.vret = vret

    def __call__(self, *args, **kwargs):
        # Validate inputs to callable

        bounded = self.signature.bind(*args, **kwargs)
        args = bounded.args

        if self.vargs is not None:
            args = list(args)
            for k, validator, param, arg in zip(count(), self.vargs, bounded.arguments.keys(), args):
                valid, value = validator.validate(arg)
                if not valid:
                    raise Exception('? callable expected {} on param \'{}\' but got {}'.format(
                        validator.brief(), param, type(arg).__name__
                    ))
                args[k] = value

        # Now invoke the callable
        ret = self.obj(*args)

        # Validate return value
        if self.vret is not None:
            valid, value = self.vret.validate(ret)
            if not valid:
                raise Exception('Expected {} return value calling to ? but got {}'.format(
                    self.vret.brief(), type(ret).__name__
                ))

        # Return the result
        return ret


    def __contains__(self, item):
        return item in self.obj

    def __hash__(self):
        return hash(self.obj)

    def __len__(self):
        return len(self.obj)


class IteratorValidator(Validator):
    '''
    Validator that checks if the given argument implements the Iterator interface.
    It can also perform ondemand validation to check them items returned by the iterator.
    (For that you need to pass a Validator instance to the 'inner' parameter in the constructor)
    '''
    def __init__(self, inner: Optional[Validator]=None) -> None:
        '''
        Constructor.
        :param inner: Optional argument. If specified, must be a validator that will check the items
        returned by the iterator (when user calls __next__)
        If not specified, this validator only check if the given argument is an iterator or not.

        e.g:
        IteratorValidator() # Check for Iterator
        IteratorValidator(TypeValidator([int])) # Check for Iterator[int]
        '''
        super().__init__()
        self.inner = inner

    def __call__(self, value) -> Generator:
        if not isinstance(value, Iterator):
            yield False
            raise Exception('? must be a iterator')

        yield True
        if self.inner is not None:
            yield IteratorProxy(value, self.inner)

    def brief(self) -> str:
        if self.inner is None:
            return 'iterator'
        return 'iterator of ' + self.inner.brief()



class IterableValidator(Validator):
    '''
    Validator that checks if the given argument is an iterable or not.
    It can also validate the items inside the iterable (see parameter 'inner' on
    the constructor)
    '''
    def __init__(self, inner: Validator=None) -> None:
        '''
        Constructor
        :param inner: Optional argument. If specified, must be a validator that will check the items
        inside the iterable when the user iterates over them

        e.g:
        IterableValidator() # Check Iterable
        IterableValidator(TypeValidator([int])) # Check Iterable[int]
        '''
        super().__init__()
        self.inner = inner

    def __call__(self, value) -> Generator:
        if not isinstance(value, Iterable):
            yield False
            raise Exception('? must be an iterable')

        yield True
        if self.inner is not None:
            yield IterableProxy(value, self.inner)

    def brief(self) -> str:
        if self.inner is None:
            return 'iterable'
        return 'iterable of ' + self.inner.brief()



class CallableValidator(Validator):
    '''
    Validator that checks if the input argument is a valid callable object.
    It also can check the values passed to the callback as arguments (see the
    'args' param), and the return value of the callback ('ret' param)
    '''
    def __init__(self, args: Optional[Iterable[Validator]]=None, ret: Optional[Validator]=None) -> None:
        '''
        Constructor.
        :param args: Optional. Must be an iterable of validators. This validators will check
        the values passed to the callable

        :param ret: Optional. Must be a validator that will check the return value when invoking
        the callable.

        e.g:

        CallableValidator() # Check for Callable
        CallableValidator([TypeValidator([int]), TypeValidator([float])]) # Check for Callable[[int, float], Any]
        CallableValidator([TypeValidator([int])], TypeValidator([int])) # Check for Callable[[int], int]
        CallableValidator(None, TypeValidator([str])) # Check Callable[..., str]
        '''
        if args is not None:
            args = list(args)
        self.args, self.ret = args, ret

    def __call__(self, value) -> Generator:
        if not callable(value):
            yield False
            raise Exception('? must be a callable')

        if self.args is not None or self.ret is not None:
            try:
                sig = signature(value)

                if self.args is not None:
                    params = sig.parameters

                    # Check number of parameters in the callable signature matches correctly
                    if len(params) != len(self.args):
                        yield False
                        raise Exception('? expected {} argument{} but got {}'.format(
                            len(self.args), 's' if len(self.args) != 1 else '', len(params)))

                if self.ret is not None:
                    pass

                value = CallableProxy(value, self.args, self.ret)


            except ValueError:
                # No signature could be provided
                pass

        yield True
        yield value

    def brief(self) -> str:
        text = 'callable'
        if self.args is not None:
            text += '(' + ','.join(map(lambda arg: arg.brief(), self.args)) + ')'
        if self.ret is not None:
            text += '->' + self.ret.brief()
        return text
