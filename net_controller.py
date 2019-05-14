#! /usr/bin/env python
## Networked Turret Controller
# acts as a server

from sys import stdout
from twisted.python.log import startLogging, err

from turret import Turret, TestTurret, ThreadTurret


from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint

from twisted.protocols.amp import Integer, Float, String, Boolean, Command
from twisted.protocols import amp


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

class TurretControlProtocol(amp.AMP):
    @TiltCommand.responder
    def tilt(self, speed):
        self.factory.Tilt(speed)
        return {"result": True}
    
    @PanCommand.responder
    def pan(self, speed):
        self.factory.Pan(speed)
        return {"result": True}
    
    @StopTiltCommand.responder
    def stop_tilt(self):
        self.factory.StopTilt()
        return {}
        
    @StopPanCommand.responder
    def stop_pan(self):
        self.factory.StopPan()
        return {}
    
    @FireCommand.responder
    def fire(self):
        self.factory.Fire()
        return {}

    @KeepalivePing.responder
    def keepalive(self):
        print("alive")
        return {}

    def logout(self):
        self.factory.disconnect()
    
    def login(self):
        self.factory.login()
    
    def connectionMade(self):
        self.factory.Calibrate()
        amp.AMP.connectionMade(self)
    
    def connectionLost(self, reason):
        amp.AMP.connectionLost(self, reason)
        if reason == "logout":
            self.factory.Logout()
        self.factory.StopAll()

class TurretControlFactory(Factory):
    def __init__(self, selected_turret):
        self.connected = False # flag to distinguish intentional and unintentional disconnections
        self.turret = selected_turret()
    
    def Tilt(self, speed):
        self.turret.tilt(speed)
    
    def Pan(self, speed):
        self.turret.pan_forever(speed)
    
    def StopTilt(self):
        self.turret.stop_tilt()
    
    def StopPan(self):
        self.turret.stop_pan()

    def StopAll(self):
        self.turret.stop_tilt()
        self.turret.stop_pan()

    def Fire(self):
        self.turret.fire()
    
    def Calibrate(self):
        if not self.connected:
            self.turret.calibrate()
    
    def disconnect(self):
        self.connected = False
    
    def login(self):
        self.connected = True

def main():
    startLogging(stdout)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--real", action="store_true") #Use test by default
    parser.add_argument("-t", "--thread", action="store_true") #Threadable turret; overrides Real
    args = parser.parse_args()
    
    if args.thread:
        turret = ThreadTurret
    elif args.real:
        turret = Turret
    else:
        turret = TestTurret
    
    factory = TurretControlFactory(turret)
    factory.protocol = TurretControlProtocol
    server_endpoint = TCP4ServerEndpoint(reactor, 8750)
    listening_port = server_endpoint.listen(factory)
    print("Running")
    reactor.run()
    

if __name__ == "__main__":
    main()
