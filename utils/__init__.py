
'''
Helper functions for general purpose on this library
'''

from functools import update_wrapper


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




class CallableWrapper:
    '''
    Objects of this class wraps callable objects:
    - Calling this instance will invoke the wrapped callable with the same arguments.
    - Also it has the attributes __name__, __qualname__, __module__, __annotations__,
    __doc__ equal than the wrapped callable.
    - _str__ & __repr__ returns the same as if you call __str__ and __repr__ in the wrapped object
    '''
    def __init__(self, obj):
        '''
        Initializes this instance.
        :param obj: Is the object to be wrapped. Must be callable
        '''
        assert callable(obj)
        self.obj = obj
        update_wrapper(self, obj)


    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)


    def __str__(self):
        return str(self.obj)

    def __repr__(self):
        return repr(self.obj)
