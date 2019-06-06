

from typing import *


class ValidationError(Exception):
    '''
    This is the class that is used to raise exceptions when a validation error
    occurs.
    It shows a message with the same structure but accepts different variations:

    "ValidationError: x [must be y] [but got z instead][: details](at function f)"

    'x', 'y', 'z', 'details' and 'f' are placeholders that should be replaced to
    format the error message:

    - x must be replaced with the parameter name being validated
    - y is the "expected" type or value for the parameter (optional)
    - z shows info about the value or type of the argument (optional, only if y is indicated)
    - details: Detailed info about the error (optional)
    - f: Name of the function where its argument its being validated

    Different kind of messages can be produced depending on what placeholders are
    filled (x and f are mandatory).

    e.g:
    "s must be float or int but got str instead (at function foo)"
    "values must be an iterable of int: found float item (at function bar)"
    "x is not valid: Must be a valid directory path (at function qux)"
    '''

    def __init__(self, func: Callable, param: str,
    expected: Optional[str]=None, got: Optional[str]=None, details: Optional[str]=None) -> None:
        assert got is None or expected is not None

        msg = param
        if expected is None and got is None:
            msg += ' is not valid'
        else:
            if expected is not None:
                msg += ' must be ' + expected
                if got is not None:
                    msg += ' but got ' + got + ' instead'

        if details is not None:
            msg += ': ' + details

        msg += ' (at function ' + func.__name__ + ')'

        super().__init__(msg)
