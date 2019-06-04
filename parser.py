

import typing
import collections.abc
from typing import *
from validators import *
from inspect import isclass


def is_type_hint(x) -> bool:
    '''
    :return True if x is a valid type hint or not (to be used as argument validator). False otherwise

    is_type_hint(typing.Iterable) -> True
    is_type_hint(collections.abc.Iterable) -> True
    is_type_hint([1,2,3]) -> False
    '''
    return (not isclass(x) and hasattr(x, '__origin__')) or (isclass(x) and hasattr(x, '__module__') and x.__module__ == 'collections.abc')


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




def parse_annotation(x) -> Validator:
    '''
    This method will turn a type annotation into a validator.

    - If the input is a basic type like int, float, str, ... a custom
    class defined by the user or an iterable of classes (list, tuple, ...), like
    (int, float), a TypeValidator is returned:

    int -> TypeValidator([int])
    (int, float) -> TypeValidator([int, float])

    - If input is the Iterator keyword, returns a IteratorValidator

    Iterator -> IteratorValidator()

    Also if its a expression of the form Iterator[expr], returns an IteratorValidator
    of the form IteratorValidator(parse(expr))

    Iterator[int] -> IteratorValidator(TypeValidator([int]))


    - If input is None, returns NoneValidator

    - If input is a callable and none of the previous conditions are satisfied, its assumed
    to be a custom validator (Returns CustomValidator)

    lambda x: x > 0  -> CustomValidator(lambda x: x > 0)

    '''

    # None validator
    if x is None:
        return NoneValidator()

    # Explicit empty validator if 'Any' or ... specified
    if x is Any or x is Ellipsis:
        return EmptyValidator()

    # Type hints using collections.abc or typing modules
    if is_type_hint(x):
        kind, args = get_type_hint_info(x)

        # Parse each arg specified on the type hint
        args = tuple(map(parse_annotation, args))

        # Iterator
        if kind == collections.abc.Iterator:
            return IteratorValidator(*args)

        # Iterable
        if kind == collections.abc.Iterable:
            return IterableValidator(*args)

        # Callable
        if kind == collections.abc.Callable:
            return CallableValidator(args[:-1], args[-1])

        # TODO
        # ...
        raise NotImplementedError()

    if isclass(x):
        # Regular type validator
        return TypeValidator([x])

    if isinstance(x, collections.abc.Iterable) and all(map(isclass, x)):
        # Type validator but multiple types indicated
        return TypeValidator(x)

    if callable(x):
        # User validator
        return UserValidator(x)

    return EmptyValidator()
