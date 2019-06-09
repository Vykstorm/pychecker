

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
            except StopIteration as e:
                if e.value is not None and not isinstance(e.value, bool):
                    # TODO
                    raise TypeError()
                valid = e.value if e.value is not None else True

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
        described above.
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



class TreeValidator(Validator):
    '''
    Base class for IteratorValidator, IterableValidator, and more...
    Represents a node in a tree structure (where each node its also a validator)
    '''
    def __init__(self, children: Iterable[Validator]=[]):
        self.children = list(children)



class IteratorValidator(TreeValidator):
    '''
    Validator that checks the given argument is an iterator
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert len(self.children) <= 1


    def __call__(self, value):
        if not isinstance(value, collections.abc.Iterator):
            # Not an iterator
            return False
        context = yield True

        if len(self.children) == 0:
            # No proxy needed
            return

        # Return proxy
        validator = self
        item_validator = self.children[0]

        class Proxy(collections.abc.Iterator):
            def __next__(self):
                item = next(value)
                try:
                    return item_validator.validate(item)
                except ValidationError:
                    raise validator.error(
                        value,
                        details='{} value found while iterating'.format(type(item).__name__ if item is not None else None),
                        **context
                    )

        yield Proxy()


    @property
    def niddle(self):
        return 'an iterator' + ('' if len(self.children) == 0 else ' of ' + self.children[0].niddle)



class IterableValidator(TreeValidator):
    '''
    Validator that checks if the given argument is an iterable
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert len(self.children) <= 1


    def __call__(self, value):
        if not isinstance(value, collections.abc.Iterable):
            # Not an iterable
            return False
        context = yield True

        if len(self.children) == 0:
            # No proxy needed
            return

        # Return proxy
        validator = self
        item_validator = self.children[0]

        class Proxy(collections.abc.Iterable):
            def __iter__(self):
                it = iter(value)
                try:
                    while True:
                        item = next(it)
                        try:
                            item = item_validator.validate(item)
                            yield item
                        except ValidationError:
                            raise validator.error(
                                value,
                                details='{} value found while iterating'.format(type(item).__name__ if item is not None else None),
                                **context
                            )
                except StopIteration:
                    pass

        yield Proxy()

    @property
    def niddle(self):
        return 'an iterable of' + ('' if len(self.children) == 0 else ' of ' + self.children[0].niddle)
