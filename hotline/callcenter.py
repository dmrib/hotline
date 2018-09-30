'''Call center application.'''

import cmd
from collections import deque
import string


class Operator:
    '''
    Call operator.

    Args:
        id (str): operator id.
    '''
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return f'Operator #{self.id}'


class CallCenter(cmd.Cmd):
    '''
    Abstraction for call center application.

    Args:
        n_operators (int): number of call operators.
    '''
    def __init__(self, n_operators):
        super().__init__()
        self.operators = {}
        self.ongoing = {}
        self.waiting = deque()

        self.load_operators(n_operators)

    def load_operators(self, n_operators):
        '''
        Load call operators in application. Max is 26.

        Args:
            n_operators (int): number of operators to be created.
        Returns:
            None.
        '''
        for i in range(n_operators):
            id = string.ascii_uppercase[i]
            self.operators[id] = Operator(id)    


if __name__ == '__main__':
    call_center = CallCenter(2)
