

import unittest
from unittest import TestCase
from itertools import *
from inspect import *
from typing import *
from errors import *


# Helper method to build validation error messages (Using ValidationError class)
def build_error_message(*args, **kwargs):
    return str(ValidationError(*args, **kwargs))

# Set of random function names
funcs = ['foo', 'bar', 'qux']

# Set of random names for function parameters
params = ['a', 'b', 'c', 'x', 'y', 'z', '_in']


class TestErrors(TestCase):
    # The next tests check error messages are formatted correctly

    def test_format_message_context(self):
        '''
        Error message displays the name of the parameter being validated as well
        as the function name
        '''
        msg = build_error_message(func='foo', param='x')

        # Function name displayed (at the end)
        self.assertRegex(msg, '\(at function foo\)$')

        # Param name displayed (at the beginning)
        self.assertRegex(msg, '^x')


    def test_format_generic_message(self):
        '''
        Ensure the syntax of error messages constructed using only the parameters 'func' and 'param'
        are correct
        '''

        for func, param in product(funcs, params):
            msg = build_error_message(func=func, param=param)
            self.assertRegex(msg, '^\w+ is not valid \(at function \w+\)$')


    def test_format_expected_value_message(self):
        '''
        Ensure the syntax of error messages are correct when using the parameters
        'expected' [and 'got']
        '''

        for func, param in product(funcs, params):
            msg = build_error_message(func=func, param=param, expected='float')
            self.assertRegex(msg, '^\w+ must be float \(at function \w+\)$')

            msg = build_error_message(func=func, param=param, expected='float', got='int')
            self.assertRegex(msg, '^\w+ must be float but got int instead \(at function \w+\)$')



    def test_format_detailed_message(self):
        '''
        Ensure syntax of error messages are valid when using the parameter 'details'
        '''

        details = 'invalid directory path name'
        msg = build_error_message('bar', param='x', details=details)
        self.assertRegex(msg, '\: {} \(at function \w+\)$'.format(details))


    def test_format_custom_message(self):
        '''
        Check that we can build an error message with only the 'message' and 'func' parameters
        '''

        msg = build_error_message('qux', message='input is not valid')
        self.assertRegex(msg, '\(at function \w+\)$')
        self.assertRegex(msg, '^input is not valid')


if __name__ == '__main__':
    unittest.main()
