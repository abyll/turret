#!/usr/bin/env python
## Piped turret controller
# stands as a process reading stdin for actions

from sys import stdin, stdout
import argparse
from turret import Turret, TestTurret, ThreadTurret
import time
import RPi.GPIO as GPIO

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

class PipeController:
    def __init__(self, turret):
        self.turret = turret();
        self.controls = {"UP": self.Up, "!UP": self.turret.stop_tilt,
            "DOWN": self.Down, "!DOWN": self.turret.stop_tilt,
            "LEFT": self.Left, "!LEFT": self.turret.stop_pan,
            "RIGHT": self.Right, "!RIGHT": self.turret.stop_pan,
            "FIRE": self.Fire, "!FIRE": self.Fire
            }
    
    def Up(self):
        self.turret.tilt(45)
    def Down(self):
        self.turret.tilt(-45)
    def Left(self):
        self.turret.pan_forever(-1)
    def Right(self):
        self.turret.pan_forever(1)
    def Fire(self):
        self.turret.fire()
    
    def stop_all(self):
        self.turret.stop_tilt()
        self.turret.stop_pan()
    
    def run(self):
        print("Starting")
        try:
          while True:
            action = stdin.readline().strip()
            #print(action)
            if action in self.controls:
                self.controls[action]()
            time.sleep(0.001)
        finally:
            GPIO.cleanup()


if __name__ == "__main__":
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--real", action="store_true") #Use test by default
    args = parser.parse_args()
    
    if args.real:
        turret = Turret
    else:
        turret = ThreadTurret
    
    pipeturret = PipeController(turret)
    pipeturret.run()
