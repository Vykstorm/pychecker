



class ValidationError(Exception):
    '''
    This is the class that is used to raise exceptions when a validation error
    occurs
    '''
    def __init__(self, msg : str) -> None:
        self.msg = msg
        super().__init__(msg)
