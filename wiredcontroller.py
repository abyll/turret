#!/usr/bin/env python
import RPi.GPIO as GPIO

from sys import stdout

from turret import Turret, TestTurret
from twisted.python.log import startLogging, err
from twisted.internet import reactor, task

import yaml
config = yaml.load(open("config.yml").read())
pinconfig = config["pinconfig"]
buttons = config["buttons"]

def add_fn(pin, bounce, fn, release=None):
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    def call(ch):
        if(GPIO.input(pin)):
            fn()
        else:
            if release:
                release()
    GPIO.add_event_detect(pin, GPIO.BOTH, callback=call, bouncetime=bounce)


def main():
    startLogging(stdout)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", action="store_false")
    args = parser.parse_args()
    
    if args.test:
        turret = TestTurret()
    else:
        turret = Turret()
    
    GPIO.setmode(GPIO.BCM)
    print("Running")
    bounce = pinconfig["bouncetime"]
    def Up():
        turret.tilt(45)
    def Down():
        turret.tilt(-45)
    def Left():
        turret.pan_forever(-1)
    def Right():
        turret.pan_forever(1)
    
    add_fn(buttons["up"], bounce, Up, turret.stop_tilt)
    add_fn(buttons["down"], bounce, Down, turret.stop_tilt)
    add_fn(buttons["left"], bounce, Left, turret.stop_pan)
    add_fn(buttons["right"], bounce, Right, turret.stop_pan)
    add_fn(buttons["fire"], bounce, turret.fire)
    
    reactor.run()
    

if __name__ == "__main__":
    try:
        main()
    finally:
        GPIO.cleanup()
