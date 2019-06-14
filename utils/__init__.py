
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
