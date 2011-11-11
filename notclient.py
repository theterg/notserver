#!/usr/bin/python

import optparse, os, time, sys
import indicate 
#python-indicate, the reason for this example
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import defer
import os.path, pynotify, gtk, pygtk

notifications = {}

def parse_args():
    usage = """usage: (--port=<port number>) <host>
--port will default to 2346
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
            self.started = False
        elif not self.started:
            print data
            where = data[:data.find(' ')]
            message = data[data.find(' ')+1:]
            addNotification(where)
            if where[0] != '#':
                message = "Private message"
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

    #def __init__(self):
        #nothing

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
   
    pynotify.init("Timekpr notification")
    configureIndicate()

    from twisted.internet import reactor

    factory = AggressiveClientFactory()
    reactor.connectTCP(hostname, options.port or 2346, factory)

    reactor.run()

def clearNotifications():
    nots = dict(notifications)
    for item in nots:
        notifications[item].set_property("draw-attention","false")
        del notifications[item]
    del(nots)

def serverClick(*args):
    clearNotifications()

def labelClick(indicator, time):
    clearNotifications()

def addNotification(who):
    if not who in notifications:
        notifications[who] = indicate.Indicator()
        notifications[who].set_property("name", who)
        notifications[who].set_property("count", "1")
        notifications[who].label = who
        notifications[who].connect("user-display", labelClick)
        notifications[who].set_property("draw-attention","true")
        notifications[who].show()
    else:
        amt = int(notifications[who].get_property("count")) + 1
        notifications[who].set_property("count", str(amt))
        notifications[who].set_property("draw-attention","true")

def configureIndicate():
    server = indicate.indicate_server_ref_default()
    server.set_type("message.mail")
    server.set_desktop_file("/usr/share/applications/notclient.desktop")
    server.connect("server-display", serverClick)

if __name__ == '__main__':
    main()
