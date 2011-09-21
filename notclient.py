#!/usr/bin/python

import optparse, os, time

from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import defer


def parse_args():
    usage = """usage: (-n) (--port=<port number>) <host>
-n or --nogtk will disable pynotify notifications (omitting requires pynotify)
--port will default to 2346
"""

    parser = optparse.OptionParser(usage)

    help = "The port to listen on. Default to a random available port."
    parser.add_option('--port', type='int', help=help)

    help = "Disable the GTK pynotify notification"
    parser.add_option('-n', '--nogtk', action="store_false", default=True, dest="gtk", help=help)

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
            if self.factory.gtk:
                try:
                    import gtk, pygtk, os, os.path, pynotify
                    pygtk.require('2.0')
                except:
                    print "Error: need python-notify, python-gtk2 and gtk"
                    return
                where = data[:data.find(' ')]
                message = data[data.find(' ')+1:]
                n = pynotify.Notification(where, message)
                n.set_urgency(pynotify.URGENCY_NORMAL)
                n.set_timeout(5000)
                n.set_category("device")
                helper = gtk.Button()
                icon = helper.render_icon(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
                n.set_icon_from_pixbuf(icon)
                n.show()

    def connectionMade(self):
        print "Client connected"
        self.connected = True
        self.transport.write("terg\r\n")
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

    def __init__(self, gtk=True):
        self.gtk = gtk

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

def wait(seconds, result=None):
    d = defer.Deferred()
    from twisted.internet import reactor
    reactor.callLater(seconds, d.callback, result)
    return d

def main():
    options, hostname = parse_args()
    
    if options.gtk:
        print "enabling GTK"
        try:
            import gtk, pygtk, os, os.path, pynotify
            pygtk.require('2.0')
        except:
            print "Error: need python-notify, python-gtk2 and gtk"
            sys.exit(1)
        if not pynotify.init("Timekpr notification"):
            sys.exit(1)

    from twisted.internet import reactor

    factory = AggressiveClientFactory(options.gtk)
    reactor.connectTCP(hostname, options.port or 2346, factory)

    reactor.run()


if __name__ == '__main__':
    main()
