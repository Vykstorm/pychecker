

from typing import *
import collections.abc
from inspect import signature
from itertools import count, islice
from operator import attrgetter
from errors import ValidationError
from utils.singleton import singleton



class Validator:
    '''
    Base class for all validators
    '''

    def __call__(self):
        raise NotImplementedError()


    @property
    def niddle(self):
        raise NotImplementedError()


    def error(self, value, **kwargs):
        try:
            return ValidationError(expected=self.niddle, **kwargs)
        except NotImplementedError:
            return ValidationError(**kwargs)


    def validate(self, value, context={}):
        result = self(value)

        if isinstance(result, bool) or result is None:
            # Returned boolean or None (None is the same as True)
            if result is None:
                result = True
            valid = result
            if not valid:
                raise self.error(value, **context)
            # Argument ok
            return value

        if isinstance(result, collections.abc.Generator):
            # Returned a generator
            try:
                # First item is boolean
                valid = next(result)
                if not isinstance(valid, bool):
                    # TODO
                    raise TypeError()
            except StopIteration:
                # Generator exhausted (no items)
                # We assume the argument is valid
                valid = True

            if not valid:
                try:
                    # Let validator trigger error with custom message
                    result.send(context)
                    # Throw error with default message
                    raise self.error(value, **context)
                except StopIteration:
                    # Throw error with default message
                    raise self.error(value, **context)

            # Argument is ok
            try:
                # Get proxy
                proxy = result.send(context)
                # Replace value with proxy
                value = proxy
            except StopIteration:
                # No proxy returned
                pass

            return value



@singleton
class AnyValidator(Validator):
    '''
    Type of validator that matches any value
    '''

    def __call__(self, value):
        # All values are ok
        return True

    @property
    def niddle(self):
        return 'any'


@singleton
class NoneValidator(Validator):
    '''
    Kind of validator which only accepts the None value.
    '''

    def __call__(self, value):
        # Only None value is ok
        return value is None


    @property
    def niddle(self):
        return 'None'


    def error(self, value, **kwargs):
        return super().error(value, got=type(value).__name__, **kwargs)



class TypeValidator(Validator):
    '''
    Validator that checks if the given input argument has the expected type
    '''

    def __init__(self, types: Iterable[Type], check_subclasses: bool=True):
        '''
        Constructor.
        :param types: An iterable with all possible valid types that argument
        must have to pass the test
        :param check_subclasses: If True, the argument will be valid if its an instance
        of a subclass of any of the classes specified in types. Default is True
        '''
        types = tuple(types)
        assert len(types) > 0

        super().__init__()
        self.types = types
        self.check_subclasses = check_subclasses


    def __call__(self, value):
        if self.check_subclasses:
            valid = isinstance(value, self.types)
        else:
            value_type = type(value)
            valid = any(map(lambda t: value_type == t, self.types))
        return valid


    @property
    def niddle(self):
        types = self.types
        if len(types) == 1:
            return types[0].__name__
        return ', '.join(map(attrgetter('__name__'), types[:-1])) + ' or ' + types[-1].__name__


    def error(self, value, **kwargs):
        return super().error(value,
            got=type(value).__name__ if value is not None else str(None),
            **kwargs)



class UserValidator(Validator):
    '''
    Instances of this class can be used to define user custom validators
    '''

    def __init__(self, func : Callable):
        '''
        Constructor.
        :param func: Must be a callable object that implements the validator interface
        described above
        '''
        super().__init__()
        self.func = func


    def __call__(self, value):
        return self.func(value)


    @property
    def niddle(self):
        return '...'


    def error(self, value, **kwargs):
        return ValidationError(details='{} returned False'.format(self.func.__name__), **kwargs)
