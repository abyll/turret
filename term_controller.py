#!/usr/bin/env python
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

import curses
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

def curses_check():
    c = stdscr.getch()
    if c == ord('q'):
       return 
    else:
        controls[c]()
    try:
        key = chr(c)
    except:
        key = str(c)
    stdscr.addstr(0,0, key)

def init_curses():
    global stdscr
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)

def end_curses():
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

def connected(p):
    input_loop = task.LoopingCall(f=curses_check, a=None)
    input_loop.start( 1 / 500)
    start_keepalive(p)


def main(stdscr):
    try:
        startLogging(stdout)
        init_curses()
        d = connect()
        d.addCallback(connected)
        d.addErrback(err, 'connection failed')
        d.addErrback(lambda p: reactor.stop())
        reactor.run()
    finally:
        end_curses()


    
def Up():
    turret.tilt(45)
def Down():
    turret.tilt(-45)
def Left():
    turret.pan_forever(-1)
def Right():
    turret.pan_forever(1)
    
def stop_all():
    myturret.StopTilt()
    myturret.StopPan()
        
controls = {curses.KEY_UP: Up,
            curses.KEY_DOWN: Down,
            curses.KEY_LEFT: Left,
            curses.KEY_RIGHT: Right,
            ord(' '): turret.fire,
            ord('w'): stop_all
            }
    


if __name__ == "__main__":
    curses.wrapper(main)
