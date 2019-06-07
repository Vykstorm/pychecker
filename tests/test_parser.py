
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
        self.assertEqual(tuple(validator.types), tuple(types))



if __name__ == '__main__':
    unittest.main()
