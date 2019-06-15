

import unittest
from unittest import TestCase
from collections.abc import *
from validators import *
from errors import *
from itertools import *
from inspect import *

# Different random values of any kind of types
values = [
    'foo', b'bar', 10, None, 1.5,
    [1, 2, 3], (1, 2, 3), set([4, 5, 6]), frozenset([7, 8, 9]),
    complex(1, 2), False, True, {'a':1, 'b':2, 'c':3},
    lambda x, y, z: (x, y, z), lambda x, *args, **kwargs: (x, args, kwargs),
    [], {}, ()
]

# Set of random validators
validators = [
    AnyValidator(), NoneValidator(),
    TypeValidator([int]), TypeValidator([bool]), TypeValidator([float, str]),
    UserValidator(lambda x: isinstance(x, int) and x in range(0, 100))
]

class TestValidators(TestCase):
    '''
    Set of tests to check validators
    '''
    def test_call_return_value(self):
        '''
        Check that all validator instances return a boolean value, None or a
        generator when calling to its __call__ method
        '''
        for validator, value in product(validators, values):
            self.assertIsInstance(validator(value), (bool, Generator, type(None)))


    def test_call_return_value_None(self):
        '''
        Check that if validator __call__ method return the value None or True,
        validate() will not raise any exception passing the same argument

        '''
        class Foo(Validator):
            def __call__(self, value):
                pass

        foo = Foo()

        try:
            for value in values:
                foo.validate(value)
        except:
            self.fail('validate() must not raise any exception if __call__ returns None')


    def test_call_return_value_False(self):
        '''
        Check that if validator __call__ method return the value False or a generator
        that returns the value False as the first item,
        validate() will raise an exception passing the same argument (A validation error
        exception)
        '''
        class Foo(Validator):
            def __call__(self, value):
                return False

        class Bar(Validator):
            def __call__(self, value):
                yield False

        foo, bar = Foo(), Bar()

        for value in values:
            self.assertRaises(ValidationError, foo.validate, value)
            self.assertRaises(ValidationError, bar.validate, value)


    def test_call_return_value_True(self):
        '''
        Test that if __call__ method returns the value True or a generator that returns
        True as the first item, validate() will not raise any exception
        '''
        class Foo(Validator):
            def __call__(self, value):
                return True

        class Bar(Validator):
            def __call__(self, value):
                yield True

        foo, bar = Foo(), Bar()

        try:
            for value in values:
                foo.validate(value)
        except ValidationError:
            self.fail('validate() must not raise an exception if __call__ returns True')



    def test_call_return_value_empty_generator(self):
        '''
        If __call__ returns an empty generator, is assumed that the input argument is valid,
        thus, validate() will not raise any exception passing it the same same argument
        '''

        class Foo(Validator):
            def __call__(self, value):
                if value is not None:
                    yield True

        foo = Foo()

        try:
            foo.validate(None)
        except ValidationError:
            self.fail('validate() must not raise an exception if __call__ returns an exhausted generator')

    def test_validate_return_value(self):
        '''
        validate(x) will return the argument itself (if the argument is valid) or a proxy
        that implements the same interface (Iterable, Callable, ...):

        - if __call__(x) returns an exhausted generator, validate(x) returns x
        - if __call__(x) returns a generator that only returns the value True, validate(x) returns x
        - if __call__(x) returns None or True, validate(x) will also return x
        '''

        class Foo(Validator):
            def __call__(self, value):
                return True

        class Bar(Validator):
            def __call__(self, value):
                return None

        class Qux(Validator):
            def __call__(self, value):
                yield True

        class Baz(Validator):
            def __call__(self, value):
                if self is None:
                    yield True


        for validator, value in product([Foo(), Bar(), Qux(), Baz()], values):
            result = validator.validate(value)
            self.assertIs(result, value)


        for validator, value in product(validators, values):
            try:
                result = validator.validate(value)
                if value is not result:
                    for cls in collections.abc:
                        if not isclass(cls) or not isinstance(value, cls):
                            continue
                        self.assertIsInstance(result, cls)

            except ValidationError:
                pass


    def test_test_return_bool(self):
        '''
        Method test() on Validator class always return False or True values
        '''
        for validator, value in product(validators, values):
            self.assertIsInstance(validator.test(value), bool)


    def test_test_return_value(self):
        '''
        Method test() always return False when validate() raises an exception
        with the same input argument. Also returns True if validate() dont raise
        an exception
        '''
        for validator, value in product(validators, values):
            try:
                validator.validate(value)
                self.assertTrue(validator.test(value))
            except ValidationError:
                self.assertFalse(validator.test(value))



    def test_context(self):
        '''
        If __call__ returns a generator, the first time it returns an item via yield,
        it receives a dictionary value (sent via send() using Generator API).

        New entries can be passed when calling validate() method using the 'context' parameter
        '''

        tester = self
        class Foo(Validator):
            def __call__(self, value):
                context = yield True
                tester.assertIsInstance(context, dict)
                tester.assertIn('param', context)

        class Bar(Validator):
            def __call__(self, value):
                context = yield False
                tester.assertIsInstance(context, dict)
                tester.assertIn('param', context)

        for validator, value in product([Foo(), Bar()], values):
            try:
                validator.validate(value, context={'param': 'qux'})
            except ValidationError:
                pass


    def test_any_validator(self):
        '''
        AnyValidator matches any kind of validator. validate(x) will never raise
        an exception. Also, validate(x) will return always x
        '''

        validator = AnyValidator()
        try:
            for value in values:
                result = validator.validate(value)
                self.assertIs(result, value)
        except ValidationError:
            self.fail('AnyValidator must match any kind of argument value')


    def test_none_validator(self):
        '''
        NoneValidator only matches the value None. validate(x) will raise an
        exception if x is not None.
        '''

        validator = NoneValidator()

        for value in values:
            if value is not None:
                self.assertRaises(ValidationError, validator.validate, value)

        try:
            result = validator.validate(None)
            self.assertIs(result, None)
        except ValidationError:
            self.fail('NoneValidator must match the None value')


    def test_true_validator(self):
        '''
        Test TrueValidator (truth value testing validator)
        '''
        validator = TrueValidator()

        for value in values:
            self.assertEqual(validator.test(value), bool(value))


    def test_false_validator(self):
        '''
        Test FalseValidator (false value testing validator)
        '''
        validator = FalseValidator()

        for value in values:
            self.assertEqual(validator.test(value), not bool(value))


    def test_type_validator(self):
        '''
        Check TypeValidator works properly
        '''
        for a in values:
            try:
                TypeValidator([type(a)], check_subclasses=False).validate(a)
                TypeValidator([type(a)], check_subclasses=True).validate(a)
            except ValidationError:
                self.fail()

            for b in values:
                if type(a) != type(b):
                    self.assertRaises(
                        ValidationError,
                        TypeValidator([type(a)], check_subclasses=False).validate,
                        b)

        all_types = frozenset([type(value) for value in values])
        for value in values:
            try:
                TypeValidator(all_types, check_subclasses=False).validate(value)
                TypeValidator(all_types, check_subclasses=True).validate(value)
            except ValidationError:
                self.fail()

        class Foo:
            pass

        class Bar(Foo):
            pass

        try:
            TypeValidator([Foo]).validate(Foo())
            TypeValidator([Foo], check_subclasses=True).validate(Bar())
        except ValidationError:
            self.fail()

        self.assertRaises(ValidationError, TypeValidator([Foo], check_subclasses=False).validate, Bar())



    def test_type_validator_compatible_classes(self):
        for method, cls in dict(__int__=int, __float__=float, __str__=str).items():
            for value in values:
                if type(value) not in (cls, complex):
                    validator = TypeValidator([cls], check_subclasses=False, check_compatible_classes=True)

                    self.assertEqual(validator.test(value), hasattr(value, method))
                    if validator.test(value):
                        self.assertIsInstance(validator.validate(value), cls)




    def test_user_validator(self):
        '''
        Check UserValidator works properly
        '''

        for v in validators:
            validator = UserValidator(v.__call__)
            for value in values:
                try:
                    validator.validate(value)
                    try:
                        v.validate(value)
                    except ValidationError:
                        self.fail()

                except ValidationError:
                    self.assertRaises(ValidationError, v.validate, value)


    def test_iterator_validator(self):
        '''
        Test for IteratorValidator class
        '''

        for value in values:
            self.assertRaises(ValidationError, IteratorValidator().validate, value)

            if isinstance(value, collections.abc.Iterable):
                validator = IteratorValidator()
                proxy = validator.validate(iter(value))

                self.assertIsInstance(proxy, collections.abc.Iterator)
                self.assertEqual(list(proxy), list(value))

                if len(tuple(value)) > 0:
                    validator = IteratorValidator([TypeValidator(map(type, value))])
                    proxy = validator.validate(iter(value))

                    self.assertIsInstance(proxy, collections.abc.Iterator)
                    self.assertEqual(list(proxy), list(value))

        validator = IteratorValidator([TypeValidator([int])])
        self.assertRaises(ValidationError, validator.validate, [1, 2, 3.4])


    def test_iterable_validator(self):
        '''
        Test for IterableValidator class
        '''

        for value in values:
            if isinstance(value, collections.abc.Iterable):
                validator = IterableValidator()
                proxy = validator.validate(value)

                self.assertIs(proxy, value)

                if len(tuple(value)) > 0:
                    validator = IterableValidator([TypeValidator(map(type, value))])
                    proxy = validator.validate(value)

                    self.assertIsInstance(proxy, collections.abc.Iterable)
                    self.assertEqual(list(proxy), list(value))
            else:
                self.assertRaises(ValidationError, IterableValidator().validate, value)


    def test_callable_validator(self):
        '''
        Test for CallableValidator class
        '''

        # Validator expect callable objects
        validator = CallableValidator()
        for value in values:
            if callable(value):
                validator.validate(value)
            else:
                self.assertRaises(ValidationError, validator.validate, value)

        # Number of param validators must match the number of parameters of the callable
        validator = CallableValidator([NoneValidator(), NoneValidator(), NoneValidator()])
        self.assertRaises(ValidationError, validator.validate, lambda x: None)
        self.assertRaises(ValidationError, validator.validate, lambda x, y, z: None)

        # Callable input arguments are checked
        for func in [lambda x, y: None, lambda x, y, *args: None]:
            proxy = validator.validate(func)
            self.assertTrue(callable(proxy))
            proxy(None, None)
            self.assertRaises(TypeError, proxy, None)
            self.assertRaises((ValidationError, TypeError), proxy, None, None, None)
            self.assertRaises(ValidationError, proxy, None, 1)
            self.assertRaises(ValidationError, proxy, 1, None)

        # Callable return values are checked
        proxy = validator.validate(lambda x, y: None)
        self.assertEqual(proxy(None, None), None)

        proxy = validator.validate(lambda x, y: True)
        self.assertRaises(ValidationError, proxy, None, None)


    def test_optional_validator(self):
        '''
        Test for OptionalValidator class
        '''

        for validator, value in product(validators, values):
            v = OptionalValidator([validator])

            if value is None or validator.test(value):
                self.assertTrue(v.test(value))
            else:
                self.assertFalse(v.test(value))



if __name__ == '__main__':
    unittest.main()
