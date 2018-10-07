#!/usr/bin/python
# Import required libraries
import sys
import time
import math
import RPi.GPIO as GPIO

# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)
from twisted.internet import task
from twisted.internet import reactor

class Stepper(object):
    def __init__(self):
        self.ratio = 4076 #measure of # of steps to a complete revolution (360 degrees)
        self.step_pins = [5, 6, 13, 19]
        self.seq = [[1,0,0,1],
               [1,0,0,0],
               [1,1,0,0],
               [0,1,0,0],
               [0,1,1,0],
               [0,0,1,0],
               [0,0,1,1],
               [0,0,0,1]]
        self.steps = len(self.seq)
        self.step_counter = 0 # start at initial position
        for pin in self.step_pins:
          GPIO.setup(pin,GPIO.OUT)
          GPIO.output(pin, 0)

        self.step_delay = 1.8 / 1000 #ms
        self.loop = None
        self.loop_count = 0
        self.loop_dir = 0
    
    def step(self, step_dir = 1):
        self.step_counter += step_dir
        for pin in range(0,4):
            io_pin=self.step_pins[pin]# Get GPIO
            GPIO.output(io_pin, self.seq[self.step_counter%self.steps][pin])   
    
    def stop(self):
        # TODO: deccelerate
        if self.loop:
            self.loop.stop()
            self.loop = None
        # leave motor coils off.
        for pin in self.step_pins:
            GPIO.output(pin, 0)
    
    def _step_loop(self):
        #TODO: accel
        if self.loop_count == "inf":
            self.step(self.loop_dir)
        else:
            if self.loop_count == 0:
                self.stop()
                return
            self.loop_count -= self.loop_dir
            self.step(self.loop_dir)
    
    def step_to_angle(self, angle):
        """ Initiate twisted loop to call step repeatedly, until angle is achieved."""
        if self.loop != None:
            self.loop.stop()
        self.loop_count = int(angle/360 * self.ratio)
        self.loop_dir = -1 if angle < 0 else 1 # direction to step
        self.loop = task.LoopingCall(f=self._step_loop)
        self.loop.start(self.step_delay)
    
    def step_forever(self, direction):
        self.loop_count = "inf"
        self.loop_dir = -1 if direction < 0 else 1 # direction to step
        if self.loop: self.stop()
        self.loop = task.LoopingCall(f=self._step_loop)
        self.loop.start(self.step_delay)
        

    def accel(self):
        # Acceleration loop
        while True:
            count += 1 
            d = abs(actualTime - WaitTime) / 3.0
            actualTime -= d
            if actualTime < WaitTime:
                actualTime = WaitTime
