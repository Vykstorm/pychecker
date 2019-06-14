
'''
Helper functions for general purpose on this library
'''

from functools import update_wrapper, partial


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



def is_compatible(obj, cls):
    '''
    Check if the  object is compatible with the given type
    :param obj: The obj to be checked
    :param cls: Must be a basic type: int, bool, float, complex, str, bytes or a tuple
    with any of those types

    If object implements __int__ or __trunc__, it is compatible with int
    For float, bool, complex, str and bytes, obj is comppatible if it implements
    __float__, __bool__, __complex__, __str__ or __bytes__ respectively
    '''
    assert (isinstance(cls, tuple) and len(cls) > 0) or cls in (int, bool, float, complex, str, bytes)
    if isinstance(cls, tuple):
        return any(map(partial(is_compatible, obj), cls))

    if cls == int:
        return hasattr(obj, '__int__') or hasattr(obj, '__trunc__')

    if cls == bool:
        return hasattr(obj, '__bool__')

    if cls == float:
        return hasattr(obj, '__float__')

    if cls == complex:
        return hasattr(obj, '__complex__')

    if cls == str:
        return hasattr(obj, '__str__')

    if cls == bytes:
        return hasattr(obj, '__bytes__')
