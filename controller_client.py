#! /usr/bin/env python
## Networked Turret Controller
# acts as a server
from sys import stdout
from twisted.python.log import startLogging, err
from twisted.internet import reactor, task
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.application.internet import ClientService, backoffPolicy

from twisted.protocols.amp import Integer, Float, String, Boolean, Command
from twisted.protocols import amp

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-t", "--tilt", action="store", type=float)
    parser.add_argument("-p", "--pan", action="store", type=float)
    parser.add_argument("-f", "--fire", action="store_true", default=False)
    return parser.parse_args()

class TiltCommand(Command):
    arguments = [('speed', Float())]
    requiresAnswer = False

class PanCommand(Command):
    arguments = [('speed', Float())]
    requiresAnswer = False

class StopTiltCommand(Command):
    requiresAnswer = False

class StopPanCommand(Command):
    requiresAnswer = False

class FireCommand(Command):
    requiresAnswer = False

class KeepalivePing(Command):
    pass

def connect():
    endpoint = TCP4ClientEndpoint(reactor, '127.0.0.1', 8750)
    factory = Factory()
    factory.protocol = amp.AMP
    service = ClientService(endpoint, factory, retryPolicy=backoffPolicy(0.5, 15.0))
    service.startService()
    return service.whenConnected()

def keepalive(p):
    d = p.callRemote(KeepalivePing)

def start_keepalive(p):
    loop = task.LoopingCall(f=keepalive, a=p)
    loop.start(3)

def connected(p):
    args = parse_args()
    if args.tilt:
        p.callRemote(TiltCommand, speed=args.tilt)
    if args.pan:
        p.callRemote(PanCommand, speed=args.pan)
    if args.fire:
        p.callRemote(FireCommand)

    start_keepalive(p)
    reactor.callLater(13,reactor.stop)

def main():
    startLogging(stdout)

    d = connect()
    d.addCallback(connected)
    d.addErrback(err, 'connection failed')
    d.addErrback(lambda p: reactor.stop())

    reactor.run()
    

if __name__ == "__main__":
    main()
