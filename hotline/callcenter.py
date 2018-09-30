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
        self.status = 'available'

    def __repr__(self):
        return f'Operator #{self.id} - {self.status}'


class Call:
    '''
    Call abstraction.

    Args:
        id (int): call id.
    '''
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return f'Call #{self.id}'


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

    def forward_call(self, call):
        '''
        Forwards call to available operator or waiting queue.

        Args:
            call (Call): incoming call object.
        Returns:
            None.
        '''
        for operator in self.operators.values():
            if operator.status == 'available':
                operator.status = 'ringing'
                self.ongoing[operator] = call
                print(f'Call {call.id} ringing for operator {operator.id}')        
                return

        self.waiting.append(call)
        print(f'Call {call.id} waiting in queue')

    def do_call(self, id):
        '''
        Handles incoming call.

        Args:
            id (int): call id.
        Returns:
            None.
        '''
        call = Call(id)
        print(f'Call {call.id} received')
        self.forward_call(call)
        
    def do_answer(self, id):
        '''
        Operator accepts call.

        Args:
            id (str): operator id.
        Returns:
            None.
        '''
        operator = self.operators[id]
        call = self.ongoing[operator]
        
        operator.status = 'busy'
        
        print(f'Call {call.id} answered by operator {operator.id}')
        print('\n', self.operators, self.ongoing, self.waiting)

if __name__ == '__main__':
    call_center = CallCenter(2)
    call_center.cmdloop('Hello, welcome!')
