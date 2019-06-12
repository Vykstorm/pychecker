
'''
Helper functions for general purpose on this library
'''

import inspect
from itertools import chain
import collections.abc
from typing import *


def ordinal(k):
    '''
    Return ordinal number abbreviation for the cardinal number k
    :param k: Must be an integer greater than 0
    '''
    assert isinstance(k, int) and k > 0

    if k == 1:
        return '1st'
    if k == 2:
        return '2nd'
    return '{}th'.format(k)



def get_caller_module():
    '''
    If a module A defines the next function:
    ```
    def foo():
        module = get_caller_module()
        if module is not None:
            print('Called from ', module.__name__)
        else:
            print('Called from ', __name__)
    ```

    And a module B imports A and calls foo(), the output will be 'Called from B'
    Whereas if module A calls itself the functon foo(), the output will be 'Called from A'
    '''
    stack = inspect.stack()
    if len(stack) <= 2:
        raise ValueError('You must call get_caller_module() inside another function')

    called_module = inspect.getmodule(stack[1].frame)
    if called_module is None:
        return None

    for item in stack[2:]:
        module = inspect.getmodule(item.frame)
        if module is None or module != called_module:
            return module
    return None



class MappingBundle(collections.abc.Mapping):
    '''
    Instances of this class are inmutable mappings that are built stacking up
    different mapping objects.

    If this object M, uses x0, x1, ..., xk  mapping objects, this instance will have
    have the next properties:

    - set(x0.keys() + x1.keys() + ... + xk.keys()) = M.keys()
    - len(M.keys()) == len(M)
    - __iter__ returns iter([key, M[key] for key in M.keys()])

    - M[key] = item(x1, x2, ..., xk, key)
    where item(x1, x2, ..., xk, key) is:
    - xk[key] if key is contained by xk
    - item(x1, x2, ..., xk-1, key) otherwise
    '''
    def __init__(self, *args: Mapping):
        self.items = list(args)

    def __getitem__(self, key):
        for item in reversed(self.items):
            if key in item:
                return item[key]
        raise KeyError()

    def __iter__(self):
        for key in self.keys():
            yield key, self[key]

    def __len__(self):
        return len(list(iter(self)))

    def __str__(self):
        return str(dict(iter(self)))

    def __repr__(self):
        return repr(dict(iter(self)))

    def keys(self):
        return frozenset(chain.from_iterable(map(lambda item: item.keys(), self.items)))
