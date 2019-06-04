

import unittest
from unittest import TestCase
from validators import *
from itertools import *
from inspect import *
from typing import *


class TestValidators(TestCase):
    '''
    Set of tests to check validators
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Some random values of different kind
        class Foo:
            pass
        self.values = (
            'foo', b'bar', 10, None, 1.5,
            [1, 2, 3], (1, 2, 3), set([4, 5, 6]), frozenset([7, 8, 9]),
            complex(1, 2), False, True, {'a':1, 'b':2, 'c':3},
            Foo()
        )

    def test_empty_validator(self):
        '''
        Check EmptyValidator
        '''
        v = EmptyValidator()
        for x in self.values:
            valid, y = v(x)
            self.assertTrue(valid)
            self.assertEqual(x, y)


    def test_type_validator(self):
        '''
        Check type validator
        '''

        # Test with only one type arg
        for x in self.values:
            v = TypeValidator([type(x)], check_subclasses=False)
            self.assertTrue(v(x)[0])

            for y in self.values:
                if x != y and type(x) != type(y):
                    self.assertFalse(v(y)[0])

        # Test check_subclasses arg
        v = TypeValidator([int], check_subclasses=True)
        self.assertTrue(v(False)[0])
        v = TypeValidator([int], check_subclasses=False)
        self.assertFalse(v(True)[0])

        #  Test with more than one arg
        v = TypeValidator(list(map(type, self.values)))
        for x in self.values:
            self.assertTrue(v(x)[0])


    def test_none_validator(self):
        '''
        Test NoneValidator
        '''
        v = NoneValidator()
        for x in self.values:
            if x is not None:
                self.assertFalse(v(x)[0])
        self.assertTrue(v(None)[0])


    def test_user_validator(self):
        '''
        Test UserValidator
        '''

        # True/False user validator
        v = UserValidator(lambda x: x >= 0)
        self.assertTrue(v(1)[0])
        self.assertFalse(v(-1)[0])

        # Generator-like user validator
        def foo(value):
            if value < 0:
                yield False
                raise Exception()
            yield True
        v = UserValidator(foo)
        self.assertTrue(v(1)[0])
        self.assertFalse(v(-1)[0])


    def test_optional_validator(self):
        '''
        Test OptionalValidator
        '''

        v = OptionalValidator(TypeValidator([int]))
        self.assertTrue(v(1)[0])
        self.assertTrue(v(None)[0])
        self.assertFalse(v('foo')[0])


    def test_iterator_validator(self):
        '''
        Test IteratorValidator
        '''
        # TODO
        pass

    def test_iterable_validator(self):
        # TODO
        pass


    def test_callable_validator(self):
        # TODO
        pass

if __name__ == '__main__':
    unittest.main()
