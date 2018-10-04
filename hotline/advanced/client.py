import cmd
import json
from os import linesep as delimiter
from twisted.internet import stdio, reactor, protocol
from twisted.protocols import basic


class DataForwardingProtocol(protocol.Protocol, cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.output = None

    def dataReceived(self, data):
        '''
        Callback for receiving data.

        Args:
            data (bytes): incoming data.
        '''
        if self.output:
            self.onecmd(data.decode('utf-8'))

    def do_call(self, id):
        '''
        Send <call> command to server.

        Args:
            id (int): call id.
        Returns:
            None.
        '''
        self.output.write(self.make_command('call', id))

    def do_answer(self, id):
        '''
        Send <answer> command to server.

        Args:
            id (str): operator id.
        Returns:
            None.
        '''
        self.output.write(self.make_command('answer', id))

    def do_reject(self, id):
        '''
        Send <reject> command to server.

        Args:
            id (str): operator id.
        '''
        self.output.write(self.make_command('reject', id))

    def do_hangup(self, id):
        '''
        Send <hangup> command to server.

        Args:
            id (int): call id.
        '''
        self.output.write(self.make_command('hangup', id))

    def make_command(self, command, id):
        '''
        Format command string as server interpretable JSON.

        Args:
            command (str): command to be sent.
            id (str or int): operator or call id.
        Returns:
            command (str): JSON-like command string .
        '''
        return json.dumps({'command': command, 'id': id}).encode('utf-8')

class HotlineClient(protocol.Protocol):
    def connectionMade(self):
        '''
        Callback for successful connection.

        Args:
            None.
        Returns:
            None.
        '''
        self.forwarder = DataForwardingProtocol()
        self.forwarder.output = self.transport
        stdioWrapper = stdio.StandardIO(self.forwarder)
        self.output = stdioWrapper

    def dataReceived(self, data):
        '''
        Callback for receiving data.

        Args:
            data (bytes): incoming data.
        Returns:
            None.        
        '''
        data = json.loads(data.decode('utf-8'))
        print(data['message'])
        

class HotlineFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        '''
        Protocol object factory method.

        Args:
            addr (IAdress): an object implementing twisted.internet.interfaces.IAddress.
        Returns:
            protocol (HotlineClient): protocol object.
        '''
        return HotlineClient()
        

reactor.connectTCP("localhost", 5678, HotlineFactory())
reactor.run()