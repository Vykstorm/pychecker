

import typing
import collections.abc
from typing import *
from validators import *
from inspect import isclass
from functools import partial
from config import settings



def parse_annotation(x, options: Mapping[str, Any]=None) -> Validator:
    '''
    Transform type annotation to validator
    '''
    if options is None:
        options = dict(settings)


    # None validator
    if x in (None, type(None)) or (isinstance(x, collections.abc.Iterable) and (tuple(x) == (None) or tuple(x) == (type(None)))):
        return NoneValidator()

    # Any validator if 'Any', ... or Optional (without args) specified
    if x is Any or x is Ellipsis or x is Optional:
        return AnyValidator()

    # Truth testing validators
    if x is True:
        return TrueValidator()
    if x is False:
        return FalseValidator()

    # Validator instances
    if isinstance(x, Validator):
        return x

    # collections.abc classes
    if hasattr(x, '__module__') and x.__module__ == 'collections.abc':
        try:
            return parse_annotation({
                collections.abc.Iterator: Iterator,
                collections.abc.Iterable: Iterable,
                collections.abc.Callable: Callable
            }.get(x), options)
        except KeyError:
            raise NotImplementedError()

    # typing module objects
    if hasattr(x, '__module__') and x.__module__ == 'typing':
        kind = x.__origin__ if hasattr(x, '__origin__') and x.__origin__ is not None else x
        args = tuple(filter(lambda arg: not isinstance(arg, typing.TypeVar), x.__args__)) if hasattr(x, '__args__') and x.__args__ is not None else ()

        # Parse each arg specified on the type hint
        args = tuple(map(partial(parse_annotation, options=options), args))

        # Iterator
        if kind == Iterator:
            return IteratorValidator(args)

        # Iterable
        if kind == Iterable:
            return IterableValidator(args)

        # Callable
        if kind == Callable:
            return CallableValidator(args)

        # Union
        if kind == Union:
            # Optional
            if len(args) == 2 and isinstance(args[-1], NoneValidator):
                return OptionalValidator(args[:1])

            return AnyValidator()

        # TODO
        # ...
        raise NotImplementedError()

    if isclass(x):
        # Validator subclass
        if issubclass(x, Validator):
            return x()

        # Regular type validator
        return TypeValidator([x], check_subclasses=not options['ignore_subclasses'], cast=options['cast'])

    if isinstance(x, collections.abc.Iterable) and all(map(isclass, x)):
        # Type validator but multiple types indicated
        return TypeValidator(x, check_subclasses=not options['ignore_subclasses'], cast=options['cast'])

    if callable(x):
        # User validator
        return UserValidator(x)

    # Default validator
    return AnyValidator()
