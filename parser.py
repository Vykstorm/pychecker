

import typing
import collections.abc
from typing import *
from validators import *
from inspect import isclass
from config import settings


def is_type_hint(x) -> bool:
    '''
    :return True if x is a valid type hint or not (to be used as argument validator). False otherwise

    is_type_hint(typing.Iterable) -> True
    is_type_hint(collections.abc.Iterable) -> True
    is_type_hint([1,2,3]) -> False
    '''
    return (not isclass(x) and hasattr(x, '__args__')) or (isclass(x) and hasattr(x, '__module__') and x.__module__ == 'collections.abc')


def get_type_hint_info(x) -> Tuple[Any, Tuple]:
    '''
    Collect type hint info. Returns a tuple with two items:
    - Kind of type hint (a class of the module collections.abc)
    - A tuple with the arguments given by the type hint.

    Is assumed that is_type_hint(x) is True

    get_type_hint_args(Iterable) -> collections.abc.Iterable, ()
    get_type_hint_args(Iterable[int, float]) -> collections.abc.Iterable, (int, float)
    get_type_hint_args(collections.abc.Iterator) -> collections.abc.Iterator, ()
    '''
    assert is_type_hint(x)
    if isclass(x):
        return x, ()
    return x.__origin__, tuple(filter(lambda arg: not isinstance(arg, typing.TypeVar), x.__args__))




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

    # Validator instances
    if isinstance(x, Validator):
        return x

    # Type hints using collections.abc or typing modules
    if is_type_hint(x):
        kind, args = get_type_hint_info(x)

        # Parse each arg specified on the type hint
        args = tuple(map(parse_annotation, args))

        # Iterator
        if kind == collections.abc.Iterator:
            return IteratorValidator(args)

        # Iterable
        if kind == collections.abc.Iterable:
            return IterableValidator(args)

        # Callable
        if kind == collections.abc.Callable:
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
        return TypeValidator([x], check_subclasses=not options['ignore_subclasses'], check_compatible_types=options['match_compatible_types'])

    if isinstance(x, collections.abc.Iterable) and all(map(isclass, x)):
        # Type validator but multiple types indicated
        return TypeValidator(x, check_subclasses=not options['ignore_subclasses'], check_compatible_types=options['match_compatible_types'])

    if callable(x):
        # User validator
        return UserValidator(x)

    # Default validator
    return AnyValidator()
