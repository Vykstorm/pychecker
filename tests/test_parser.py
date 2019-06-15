
import unittest
from unittest import TestCase
from validators import *
from errors import *
from itertools import *
from inspect import *
from types import new_class
from parser import parse_annotation as parse
from typing import *
import collections.abc


# Set of random types
types = [int, float, str, complex, bool, new_class('Foo')]

class TestParser(TestCase):
    def test_parse_None(self):
        '''
        None and type(None) annotations are parsed to NoneValidator
        '''
        self.assertIsInstance(parse(None), NoneValidator)
        self.assertIsInstance(parse(type(None)), NoneValidator)


    def test_parse_any(self):
        '''
        Any type annotation is parsed to AnyValidator
        '''
        self.assertIsInstance(parse(Any), AnyValidator)


    def test_parse_validator(self):
        '''
        Validator instance can also be used as type annotations.
        When parsing them, the return value is the validator itself.

        Also Validator classes can be written as annotations. In that case,
        the returned value will be an instance of such class (constructor cant
        accept any argument)
        '''

        # Set of random validators
        validators = [AnyValidator(), NoneValidator(), TypeValidator([int])]

        for validator in validators:
            self.assertIs(parse(validator), validator)
            cls = validator.__class__
            if len(signature(cls).parameters) == 0:
                self.assertIsInstance(parse(cls), cls)


    def test_parse_func(self):
        '''
        Functions are parsed to UserValidator
        '''
        def foo(x):
            return True
        bar = lambda x: True

        self.assertIsInstance(parse(foo), UserValidator)
        self.assertIsInstance(parse(bar), UserValidator)


    def test_parse_types(self):
        '''
        Single types or an iterable of types (classes) are parsed to TypeValidator
        '''
        for type in types:
            validator = parse(type)
            self.assertIsInstance(validator, TypeValidator)
            self.assertEqual(tuple(validator.types), (type,))

        validator = parse(types)
        self.assertIsInstance(validator, TypeValidator)
        self.assertEqual(frozenset(validator.types), frozenset(types))


    def test_parse_Iterator(self):
        '''
        typing.Iterator and collections.abc.Iterator are parsed to an IteratorValidator
        '''
        self.assertIsInstance(parse(collections.abc.Iterator), IteratorValidator)
        self.assertIsInstance(parse(Iterator), IteratorValidator)
        self.assertIsInstance(parse(Iterator[int]), IteratorValidator)
        self.assertIsInstance(parse(Iterator[Iterator[int]]), IteratorValidator)


    def test_parse_Iterable(self):
        '''
        typing.Iterable and collections.abc.Iterable are parsed to an IterableValidator
        '''
        self.assertIsInstance(parse(collections.abc.Iterable), IterableValidator)
        self.assertIsInstance(parse(Iterable), IterableValidator)
        self.assertIsInstance(parse(Iterable[int]), IterableValidator)
        self.assertIsInstance(parse(Iterable[Iterable[int]]), IterableValidator)


    def test_parse_Callable(self):
        '''
        typing.Callable and collections.abc.Callable are parsed to a CallableValidator
        '''
        self.assertIsInstance(parse(collections.abc.Callable), CallableValidator)
        self.assertIsInstance(parse(Callable), CallableValidator)
        self.assertIsInstance(parse(Callable[[int, float, str], Any]), CallableValidator)


    def test_parse_Optional(self):
        '''
        typing.Optional[...] is parsed to an OptionalValidator
        typing.Optional is parsed to AnyValidator
        '''
        self.assertIsInstance(parse(Optional), AnyValidator)
        self.assertIsInstance(parse(Optional[int]), OptionalValidator)
        self.assertIsInstance(parse(Optional[Iterable[int]]), OptionalValidator)



if __name__ == '__main__':
    unittest.main()
