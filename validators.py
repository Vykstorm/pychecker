

from typing import *
import collections.abc
from inspect import signature, Parameter
from itertools import count, islice
from functools import update_wrapper
from operator import attrgetter
from errors import ValidationError
from utils import ordinal
import operator
from wrappers import Wrapper, CallableWrapper


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


    def test(self, value):
        result = self(value)
        if result is not None and not isinstance(result, (bool, collections.abc.Generator)):
            raise TypeError('Validator.__call__ should return None, bool or generator')

        if result is None:
            return True

        if isinstance(result, bool):
            return result

        try:
            valid = next(result)
            if not isinstance(valid, bool):
                raise TypeError('Validator.__call__ generator must always return first a bool value')

        except StopIteration as e:
            assert e.value is None or isinstance(e.value, bool)
            valid = e.value if e.value is not None else True

        return valid



    def validate(self, value, context={}):
        result = self(value)
        if result is not None and not isinstance(result, (bool, collections.abc.Generator)):
            raise TypeError('Validator.__call__ should return None, bool or generator')

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
                    raise TypeError('Validator.__call__ generator must always return first a bool value')

            except StopIteration as e:
                assert e.value is None or isinstance(e.value, bool)
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



class TrueValidator(Validator):
    '''
    This validator matches any object that is evaluated to True in an if statemnt
    '''
    def __call__(self, value):
        return bool(value)

    @property
    def niddle(self):
        return 'any true value or statement'


class FalseValidator(Validator):
    '''
    This validator matches any object that is evaluated to False in an if statemnt
    '''
    def __call__(self, value):
        return not bool(value)

    @property
    def niddle(self):
        return 'any false value or statement'



class TypeValidator(Validator):
    '''
    Validator that checks if the given input argument has the expected type
    '''

    def __init__(self, types: Iterable[Type], check_subclasses: bool=True, check_compatible_classes: bool=False):
        '''
        Constructor.
        :param types: An iterable with all possible valid types that argument
        must have to pass the test

        :param check_subclasses: If True, the argument will be valid also if it is an instance
        of a subclass of any of the classes specified in types. Default is True
        '''
        types = frozenset(types)
        assert len(types) > 0

        super().__init__()
        self.types = tuple(types)
        self.check_subclasses = check_subclasses
        self.check_compatible_classes = check_compatible_classes


    def __call__(self, value):
        if self.check_subclasses:
            valid = isinstance(value, self.types)
        else:
            value_type = type(value)
            valid = any(map(lambda t: value_type == t, self.types))

        if not valid and self.check_compatible_classes:
            return self.make_cast(value)
        return valid


    def make_cast(self, value):
        methods = {
            '__int__': int,
            '__trunc__': int,
            '__bool__': bool,
            '__str__': str,
            '__float__': float,
            '__complex__': complex,
            '__bytes__': bytes
        }
        for attr, cls in methods.items():
            if cls in self.types and hasattr(value, attr):
                if type(value) == complex and cls in (float, int):
                    # No conversion from complex to int or float (even if complex
                    # defines __int__ and __float__)
                    continue

                yield True
                cast_value = getattr(value, attr)
                casted_value = cast_value()
                yield casted_value
                return
        return False


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

    @property
    def num_children(self):
        return len(self.children)





class ProxyMixin:
    def __init__(self, validator: TreeValidator, context: Dict):
        self.validator, self.context = validator, context


class IteratorProxy(collections.abc.Iterator, Wrapper, ProxyMixin):
    def __init__(self, target, *args, **kwargs):
        ProxyMixin.__init__(self, *args, **kwargs)
        Wrapper.__init__(self, target)
        assert self.validator.num_children == 1 and isinstance(self.wrapped, collections.abc.Iterator)

    def __next__(self):
        item = next(self.wrapped)
        try:
            return self.validator.children[0].validate(item)
        except ValidationError:
            raise self.validator.error(
                self.wrapped,
                details='{} value found while iterating'.format(type(item).__name__ if item is not None else None),
                **self.context
            )


class IterableProxy(collections.abc.Iterable, Wrapper, ProxyMixin):
    def __init__(self, target, *args, **kwargs):
        ProxyMixin.__init__(self, *args, **kwargs)
        Wrapper.__init__(self, target)
        assert self.validator.num_children == 1 and isinstance(self.wrapped, collections.abc.Iterable)

    def __iter__(self):
        return IteratorProxy(iter(self.wrapped), self.validator, self.context)



class CallableProxy(collections.abc.Callable, CallableWrapper, ProxyMixin):
    def __init__(self, target, *args, **kwargs):
        assert callable(target)
        ProxyMixin.__init__(self, *args, **kwargs)
        CallableWrapper.__init__(self, target)

        try:
            self.sig = signature(self.wrapped)
        except:
            # No signature avaliable
            self.sig = None

    def __call__(self, *args, **kwargs):
        # Variables used to format error messages
        func, param = self.context.get('func', '?'), self.context.get('param', '?')


        if self.sig is not None:
            # Callable signature avaliable

            # Bound arguments to the callable signature
            bounded_args = self.sig.bind(*args, **kwargs)
            bounded_args.apply_defaults()
            args = list(bounded_args.args)

            param_validators = self.validator.children[:-1]
            if len(args) != len(param_validators):
                # Incorrect number of args
                raise ValidationError(
                    message='{} expects {} arguments but got {} instead'.format(param, len(args), len(param_validators)),
                    func=func
                )

            # Validate each argument
            for k, arg, validator in zip(count(), args, param_validators):
                try:
                    args[k] = validator.validate(arg, context={'func': func, 'param': '{} argument of {}'.format(ordinal(k+1), param)})
                except ValidationError:
                    raise ValidationError(
                        message='{} argument passed to {} must be {}'.format(ordinal(k+1), param, validator.niddle),
                        func=func
                    )

            # Invoke the callable
            result = CallableWrapper.__call__(self, *args)
        else:
            # Callable signature not avaliable
            result = CallableWrapper.__call__(self, *args, **kwargs)

        # Validate the result
        context = {'func': func, 'param': 'return value of {}'.format(param)}
        validator = self.validator.children[-1]
        try:
            result = validator.validate(result, context=context)
        except ValidationError:
            raise ValidationError(expected=validator.niddle, **context)

        # Finally return the result of the callable
        return result




class IteratorValidator(TreeValidator):
    '''
    Validator that checks the given argument is an iterator
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.num_children <= 1


    def __call__(self, value):
        if not isinstance(value, collections.abc.Iterator):
            # Not an iterator
            return False
        context = yield True

        if self.num_children != 0:
            # Return proxy
            yield IteratorProxy(value, self, context)


    @property
    def niddle(self):
        return 'iterator' + ('' if self.num_children == 0 else ' of ' + self.children[0].niddle)



class IterableValidator(TreeValidator):
    '''
    Validator that checks if the given argument is an iterable
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.num_children <= 1


    def __call__(self, value):
        if not isinstance(value, collections.abc.Iterable):
            # Not an iterable
            return False
        context = yield True

        if self.num_children != 0:
            # Return proxy
            yield IterableProxy(value, self, context)


    @property
    def niddle(self):
        return 'iterable' + ('' if self.num_children == 0 else ' of ' + self.children[0].niddle)



class CallableValidator(TreeValidator):
    '''
    Validator that checks if the given argument is a callable object of some kind
    '''
    def __call__(self, value):
        if not callable(value):
            # Not a callable object
            return False

        try:
            sig = signature(value)

            # Correct amount of parameters?
            try:
                if self.num_children > 0:
                    sig.bind(*self.children[:-1])
            except TypeError:
                # Wrong number of parameters
                context = yield False
                raise self.error(value, details='Wrong number of parameters', **context)
        except ValueError:
            # No signature avaliable
            pass

        context = yield True

        if self.num_children != 0:
            yield CallableProxy(value, self, context)

    @property
    def niddle(self):
        if self.num_children == 0:
            return 'callable'
        return 'callable({})->{}'.format(', '.join(map(attrgetter('niddle'), self.children[:-1])), self.children[-1].niddle)



class OptionalValidator(TreeValidator):
    '''
    Creates a validator that checks if the input argument either satisifies some
    condition or is set to None
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.num_children == 1


    def __call__(self, value):
        if value is None:
            return True

        opt_validator = self.children[0]
        valid = opt_validator.test(value)

        if not valid:
            return False

        context = yield True
        yield opt_validator.validate(value, context)


    @property
    def niddle(self):
        return self.children[0].niddle + ' or None'
