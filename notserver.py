#!/usr/bin/python

import optparse, os, time

from twisted.internet.protocol import ServerFactory, Protocol
from twisted.protocols.telnet import Telnet
from twisted.internet import defer

def parse_args():
    usage = """usage: (--port=<port number>) (--iface=<interface>) <file to watch>
File to watch is normally ~/.irssi/fnotify
"""

    parser = optparse.OptionParser(usage)

    help = "The port to listen on. Default to a random available port."
    parser.add_option('--port', type='int', help=help)

    help = "The interface to listen on. Default is localhost."
    parser.add_option('--iface', help=help, default='localhost')

    options, args = parser.parse_args()

    if len(args) != 1:
        parser.error('Provide exactly one poetry file.')

    watch_file = args[0]

    if not os.path.exists(args[0]):
        parser.error('No such file: %s' % poetry_file)

    return options, watch_file


def wait(seconds, result=None):
    d = defer.Deferred()
    from twisted.internet import reactor
    reactor.callLater(seconds, d.callback, result)
    return d

class WatcherProtocol(Telnet):
    delimiter = "\n"

    def welcomeMessage(self):
        return "Welcome!\n"

    def loginPrompt(self):
        return "Enter username followed by password\n"

    def checkUserAndPass(self, u, p):
        return self.factory.authenticate(self,u,p)

    def telnet_Command(self, comm):
        if (comm.find("PING") != -1):
            self.transport.write("PONG\n")

    def connectionLost(self, reason):
        self.factory.remove(self)

class WatcherFactory(ServerFactory):

    protocol = WatcherProtocol
    clients = []

    def __init__(self, watch_file):
        self.filename = watch_file
        self.file = open(self.filename)

    def authenticate(self, client, u, p):
        print "AUTHING "+u+":"+p
        if ((u == "terg") and (p == "terg")):
            self.clients.append(client)
            print "Client "+str(len(self.clients))+" connected"
            return True
        else:
            return False

    def remove(self, client):
        for c in self.clients:
            if c == client:
                self.clients.remove(c)
                print "Client removed, "+str(len(self.clients))+" remain"
                return True
        return False
    
    @defer.inlineCallbacks
    def watcherThread(self):
        from twisted.internet import reactor
        st_results = os.stat(self.filename)
        st_size = st_results[6]
        self.file.seek(st_size)
        while (reactor.running):
            where = self.file.tell()
            line = self.file.readline()
            if not line:
                yield wait(1)
                self.file.seek(where)
            else:
                for client in self.clients:
                    client.transport.write(line)
        print "watcher thread, awaaaayyy!"

def main():
    options, watch_file = parse_args()

    factory = WatcherFactory(watch_file)

    from twisted.internet import reactor

    port = reactor.listenTCP(options.port or 0, factory,
                             interface=options.iface)

    print 'Serving %s on %s.' % (watch_file, port.getHost())

    reactor.callInThread(factory.watcherThread)
    reactor.run()


if __name__ == '__main__':
    main()
