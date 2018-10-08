from collections import deque
import json
import string
from twisted.application import internet, service
from twisted.internet.protocol import Factory, ServerFactory
from twisted.internet import reactor, protocol


class Operator:
    '''
    Call operator.

    Args:
        id (str): operator id.
    '''
    def __init__(self, id):
        self.id = id
        self.status = 'available'


class Call:
    '''
    Call abstraction.

    Args:
        id (int): call id.
    '''
    def __init__(self, id):
        self.id = id


class HotlineProtocol(protocol.Protocol):
    '''
    Protocol for data center call management.

    Args:
        factory (HotlineFactory): Twisted protocol factory.
    '''
    def __init__(self, factory):
        self.factory = factory

    def dataReceived(self, data):
        '''
        Callback for incoming data.

        Args:
            data (bytes): incoming command from client.
        Returns:
            None.
        '''
        message = json.dumps({"message": self.process_command(data)})
        self.transport.write(message.encode('utf-8'))

    def process_command(self, data):
        '''
        Handles incoming string form JSON command.

        Args:
            data (bytes): incoming command in JSON-like string.
        Returns:
            msg (string): queue manager response string.
        '''
        data = json.loads(data.decode('utf-8'))
        command, id = data['command'], data['id']

        if command == 'call':
            return self.process_call(int(id))
        elif command == 'answer':
            return self.process_answer(id)
        elif command == 'reject':
            return self.process_reject(id)
        elif command == 'hangup':
            return self.process_hangup(int(id))

    def process_call(self, id):
        '''
        Process <call> command in the queue manager.

        Args:
            id (int): call id.
        Returns:
            msg (str): previous manager responses concatenated with new responses string.
        '''
        call = Call(id)
        msg = f'Call {call.id} received'        
        msg += self.forward_call(call)
        
        return msg

    def process_answer(self, id):
        '''
        Process <answer> command in the queue manager.

        Args:
            id (str): operator id.
        Returns:
            msg (str): queue manager response.
        '''
        operator = self.factory.service.operators[id]
        call = self.factory.service.ongoing[operator]
        
        operator.status = 'busy'
        
        return f'Call {call.id} answered by operator {operator.id}'

    def process_reject(self, id):
        '''
        Process <reject> command in the queue manager.

        Args:
            id (str): operator id.
        Returns:
            msg (str): queue manager response.
        '''
        operator = self.factory.service.operators[id]
        call = self.factory.service.ongoing[operator]

        self.factory.service.ongoing.pop(operator)
        operator.status = 'available'        
        
        msg = f'Call {call.id} rejected by operator {operator.id}'        
        msg += self.forward_call(call)
        return msg

    def process_hangup(self, id):
        '''
        Process <hangup> command in the queue manager.

        Args:
            id (int): call id.
        Returns:
            msg (str): queue manager response.
        '''
        msg = self.remove_from_waiting(id)
        if not msg:
            msg = self.hangup_call(id)
        
        msg += self.step_waiting_queue()

        return msg

    def forward_call(self, call):
        '''
        Forwards call to available operator or waiting queue.

        Args:
            call (Call): incoming call object.
        Returns:
            msg (str): queue manager response.
        '''
        for operator in self.factory.service.operators.values():
            if operator.status == 'available':
                operator.status = 'ringing'
                self.factory.service.ongoing[operator] = call
                reactor.callLater(10, self.timout_call, operator)
                return f'\nCall {call.id} ringing for operator {operator.id}'

        self.factory.service.waiting.append(call)
        return f'\nCall {call.id} waiting in queue'

    def timout_call(self, operator):
        '''
        Timeout non answered calls.

        Args:
            operator (Operator): unresponsive operator.
        Returns:
            None.
        '''
        if self.factory.service.timeout:
            if operator in self.factory.service.ongoing and operator.status == 'ringing':
                lost_call = self.factory.service.ongoing[operator]
                self.factory.service.ongoing.pop(operator)
                operator.status = 'available'
                
                msg = f'Call {lost_call.id} ignored by operator {operator.id}'
                msg += self.forward_call(lost_call)
                msg += self.step_waiting_queue()
                msg = json.dumps({"message": msg})
                self.transport.write(msg.encode('utf-8'))            

    def remove_from_waiting(self, id):
        '''
        Remove call from waiting queue.

        Args:
            id (int): call id.
        Returns:
            msg (str): queue manager response.
        '''
        msg = ''
        for call in self.factory.service.waiting:
            if call.id == id:
                msg = f'Call {call.id} missed'
                break
        
        if msg:
            self.factory.service.waiting.remove(call)

        return msg

    def hangup_call(self, id):
        '''
        Finish ongoing call and makes operator available.

        Args:
            id (int): call id.
        Returns:
            msg (str): queue manager response.
        '''
        for operator, call in self.factory.service.ongoing.items():
            if call.id == id:
                if operator.status == 'ringing':
                    msg = f'Call {call.id} missed'
                else:
                    msg = f'Call {call.id} finished and operator {operator.id} is available'
                operator.status = 'available'                
                break
        
        self.factory.service.ongoing.pop(operator)
        return msg

    def step_waiting_queue(self):
        '''
        Forwards call in the first position of waiting queue.

        Args:
            None.
        Returns:
            msg (str): queue manager response.
        '''
        if len(self.factory.service.waiting) > 0:
            call = self.factory.service.waiting[0]
        else:
            return ''

        for operator in self.factory.service.operators.values():
            if operator.status == 'available':
                operator.status = 'ringing'
                self.factory.service.ongoing[operator] = call
                self.factory.service.waiting.popleft()
                reactor.callLater(10, self.timout_call, operator)
                return f'\nCall {call.id} ringing for operator {operator.id}'
        
        return ''


class HotlineService(service.Service):
    def __init__(self, n_operators, timeout):
        self.operators = {}
        self.ongoing = {}
        self.waiting = deque()
        self.timeout = timeout
        self.load_operators(n_operators)

    def startService(self):
        '''
        Callback for service start event.

        Args:
            None.
        Returns:
            None.
        '''
        service.Service.startService(self)

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


class HotlineFactory(ServerFactory):
    def __init__(self, service):
        self.service = service

    def buildProtocol(self, addr):
        '''
        Creates Twister Protocol object.

        Args:
            addr (object): an object implementing twisted.internet.interfaces.IAddress .
        Returns:
            protocol (HotlineProtocol): HotlineProtocol object instance.
        '''
        return HotlineProtocol(self)


# Configuration parameters
port = 5678
iface = 'localhost'
n_operators = 2
timeout = True

# Setup Hotline service
top_service = service.MultiService()
hotline_service = HotlineService(n_operators, timeout)
hotline_service.setServiceParent(top_service)

# Setup Hotline factory
factory = HotlineFactory(hotline_service)
tcp_service = internet.TCPServer(port, factory, interface=iface)
tcp_service.setServiceParent(top_service)

# Setup Callcenter Application
application = service.Application('hotline')
top_service.setServiceParent(application)