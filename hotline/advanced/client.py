import json
from twisted.internet import reactor, protocol


class HotlineClient(protocol.Protocol):
    def connectionMade(self):
        self.transport.write('{"command" : "call", "id": "1"}'.encode('utf-8'))

    def dataReceived(self, data):
        message = json.loads(data.decode('utf-8'))
        print(message['message'])
        self.transport.loseConnection()


class HotlineFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return HotlineClient()

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed.")
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print("Connection lost.")
        reactor.stop()
        

reactor.connectTCP("localhost", 5678, HotlineFactory())
reactor.run()