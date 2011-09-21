#!/usr/bin/python

import optparse, os, time

from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import defer

def parse_args():
    usage = """usage: (--port=<port number>) <host>
"""

    parser = optparse.OptionParser(usage)

    help = "The port to listen on. Default to a random available port."
    parser.add_option('--port', type='int', help=help)

    options, args = parser.parse_args()

    if len(args) != 1:
        parser.error('You must specify the host!')

    hostname = args[0]

    return options, hostname 

class WatcherClientProtocol(Protocol):

    pinged = False
    connected = False
    started = True
    
    def dataReceived(self, data):
        data = data.replace("\n","")
        if (data.find("PONG") != -1):
            self.pinged = True
        elif (data.find("*****") != -1):
            self.started = False
        elif not self.started:
            print data
        
    #@defer.inlineCallbacks
    def connectionMade(self):
        print "Client connected"
        self.connected = True
        #yield wait(1)
        print "sending user"
        self.transport.write("terg\r\n")
        #yield wait(1)
        print "sending pass"
        self.transport.write("terg\r\n")
        from twisted.internet import reactor
        reactor.callInThread(self.pingerThread)

    def connectionLost(self, reason):
        print "Connection lost"
        self.connected = False

    @defer.inlineCallbacks
    def pingerThread(self):
        while(self.connected):
            self.pinged = False
            self.transport.write("PING\r\n")
            yield wait(5)
            if not self.pinged:
                print "Disconnected!"
                self.transport.loseConnection()

class AggressiveClientFactory(ClientFactory):

    protocol = WatcherClientProtocol

    def __init__(self):
        print "Hold onto your butts"

    @defer.inlineCallbacks
    def clientConnectionFailed(self, connector, reason):
        print "Client failed, reconnecting"
        yield wait(5)
        connector.connect()

    @defer.inlineCallbacks
    def clientConnectionLost(self, connector, reason):
        print "Client lost, reconnecting"
        yield wait(5)
        connector.connect()

def connect(host, port):
    from twisted.internet import reactor
    factory = AggressiveClientFactory()
    reactor.connectTCP(host, port, factory)

def wait(seconds, result=None):
    d = defer.Deferred()
    from twisted.internet import reactor
    reactor.callLater(seconds, d.callback, result)
    return d

def main():
    options, hostname = parse_args()

    from twisted.internet import reactor

    connect(hostname, options.port or 2346)

    reactor.run()


if __name__ == '__main__':
    main()
