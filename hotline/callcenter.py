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
        return f'Operator #{self.id}: {self.status}'


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
        self.prompt = '(Hotline)'
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

    def finish_call(self, id):
        '''
        Finish received call.

        Args:
            id (int): call id.
        Returns:
            None.
        '''
        if not self.remove_from_waiting(id):
            self.hangup_call(id)
        
        self.step_waiting_queue()

    def remove_from_waiting(self, id):
        '''
        Remove call from waiting queue.

        Args:
            id (int): call id.
        Returns:
            removed (bool): True if call was found and deleted, False otherwise.
        '''
        found = False
        for call in self.waiting:
            if call.id == id:
                found = True
                print(f'Call {call.id} missed')
                break
        
        if found:
            self.waiting.remove(call)

        return found

    def hangup_call(self, id):
        '''
        Finish ongoing call and makes operator available.

        Args:
            id (int): call id.
        Returns:
            None.
        '''
        for operator, call in self.ongoing.items():
            if call.id == id:
                if operator.status == 'ringing':
                    print(f'Call {call.id} missed')
                else:
                    print(f'Call {call.id} finished and operator {operator.id} is available')
                operator.status = 'available'                
                break
        
        self.ongoing.pop(operator)

    def step_waiting_queue(self):
        '''
        Forwards call in the first position of waiting queue.

        Args:
            None.
        Returns:
            None.
        '''
        if len(self.waiting) > 0:
            call = self.waiting[0]
        else:
            return

        for operator in self.operators.values():
            if operator.status == 'available':
                operator.status = 'ringing'
                self.ongoing[operator] = call
                self.waiting.popleft()
                print(f'Call {call.id} ringing for operator {operator.id}')        
                break

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

    def do_reject(self, id):
        '''
        Operator rejects call.

        Args:
            id (str): operator id.
        Returns:
            None.
        '''
        operator = self.operators[id]
        call = self.ongoing[operator]

        self.ongoing.pop(operator)
        operator.status = 'available'        
        print(f'Call {call.id} rejected by operator {operator.id}')        
        
        self.forward_call(call)        
        self.step_waiting_queue()        

    def do_hangup(self, id):
        '''
        Finish call.

        Args:
            id (int): call id.
        Returns:
            None.
        '''
        self.finish_call(id)        

    def do_state(self, _):
        '''
        Print application current state for debugging purposes.

        Args:
            None.
        Returns:
            None.
        '''
        print('\n', 'OPERATORS:')
        for operator in self.operators:
            print(f'    {self.operators[operator]}')
        
        print('\n', 'ONGOING CALLS:')
        for operator in self.ongoing:
            print(f'    {operator}, {self.ongoing[operator]}')

        print('\n', 'WAITING QUEUE:')
        for call in self.waiting:
            print(f'    Call #{call.id}', '\n')



if __name__ == '__main__':
    call_center = CallCenter(2)
    call_center.cmdloop('Hello, welcome!')
