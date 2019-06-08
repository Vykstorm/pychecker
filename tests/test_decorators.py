
import unittest
from unittest import TestCase
from validators import *
from errors import *
from itertools import *
from inspect import *
from types import new_class
from typing import *
import collections.abc
from decorators import checked


class TestDecorators(TestCase):
    '''
    Set of functions to test the decorator @checked
    '''

    def test_wrapper_info(self):
        '''
        Check that methods & attributes __name__ , __doc__ & __annotations__
        are the same or return the same value for the wrapper & the wrapped functions
        '''

        def foo(x :int, y : float, z : str) -> complex:
            '''
            #TODO
            '''
            pass

        bar = checked(foo)
        self.assertEqual(foo.__name__, bar.__name__)
        self.assertEqual(foo.__doc__, bar.__doc__)
        self.assertEqual(foo.__annotations__, bar.__annotations__)


    def test_wrapped_func_no_args(self):
        '''
        Check that we can decorate a function with no arguments and call it
        '''
        @checked
        def foo():
            pass
        foo()


    def test_wrapped_func_with_args(self):
        '''
        Check that we can decorate a function with arguments
        Also verifies that we call the wrapped function using positional or keyword
        arguments and the values passed are consistent with its signature
        '''

        @checked
        def foo(x):
            self.assertEqual(x, 1)

        @checked
        def bar(x, y, z):
            self.assertEqual((x, y, z), (1, 2, 'hello'))

        foo(1)
        bar(1, 2, 'hello')


    def test_wrapped_func_with_varargs(self):
        '''
        Check that we can decorate a function with varadict position arguments (*args)
        Also verifies that values passed to the wrapped function are consistent with its signature
        '''
        @checked
        def foo(*args):
            for k, arg in zip(count(), args):
                self.assertEqual(k, arg)

        @checked
        def bar(x, y, *args):
            self.assertEqual(x, 0)
            self.assertEqual(y, 1)
            for k, arg in zip(count(2), args):
                self.assertEqual(k, arg)

        @checked
        def baz(*args : str):
            pass

        @checked
        def qux(x, *args : int):
            pass

        foo()
        foo(0)
        foo(0, 1, 2)

        bar(0, 1)
        bar(0, 1, 2, 3)


    def test_wrapped_func_with_varkwargs(self):
        '''
        Check that we can decorate a function with varadict keyword arguments (**kwargs)
        Also verifies that values passed to the wrapped function are consistent with its signature
        and ensures that **kwargs parameter cannot have any annotation
        '''

        @checked
        def foo(**kwargs):
            self.assertEqual(kwargs, {'a': 1, 'b': 2})

        @checked
        def bar(x, y, **kwargs):
            self.assertEqual(kwargs, {'a': 1, 'b': 2})

        @checked
        def qux(x, y, *args, **kwargs):
            self.assertEqual(kwargs, {'a': 1, 'b': 2})

        foo(b=2, a=1)
        bar(0, 0, a=1, b=2)
        qux(0, 0, b=2, a=1)

        def mux():
            @checked
            def baz(**kwargs : str):
                pass
            baz()
        self.assertRaises(Exception, mux)


    def test_wrapped_func_missing_arg(self):
        '''
        Wrapper function raises an exception if an argument is missing
        '''

        @checked
        def foo(x):
            pass

        @checked
        def bar(x, y, z):
            pass

        @checked
        def qux(x, *args):
            pass

        @checked
        def baz(x, **kwargs):
            pass

        self.assertRaises(TypeError, foo)
        self.assertRaises(TypeError, bar, 1, 2)
        self.assertRaises(TypeError, qux)
        self.assertRaises(TypeError, baz)



if __name__ == '__main__':
    unittest.main()