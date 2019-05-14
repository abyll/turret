#! /usr/bin/env python
from servo import *
from stepper import Stepper
from led import DimmerRGB
import Adafruit_PCA9685
import RPi.GPIO as IO
import threading
import time

from twisted.internet import task

class Turret(object):
    left = 1
    right = -1
    def __init__(self, tilt_min=0, tilt_max=180):
        self.min_angle = tilt_min
        self.max_angle = tilt_max
        self._init_servos()
        self._init_stepper()
        self._init_led()
    
    def _init_servos(self):
        #init global PWM
        self.pwm = Adafruit_PCA9685.PCA9685()
        #init servos
        self.servos = ServoPair(self.pwm, chan_a=0, chan_b=1, min=self.min_angle, max=self.max_angle)
        
        #calibrate
        self.servos.set_angle(90)
        self.tilt_angle = 90
        self.tilt_speed = 45 # Default tilt speed, in degrees per second
        self.tilt_delay = 1.0/60.0 # time between step increments; servo pulses are only 60hz
        self.tilt_loop = None
        self.tilt_dir = 0 # Angle increment per step
        
    def _init_stepper(self):
        #init steppers
        self.stepper = Stepper()
        self.pan_angle = 0 # angle
    
    def _init_led(self):
        self.status_led = DimmerRGB(self.pwm, 8,9,10)
        self.status_led.set_color(1,.4,0)
        
    def tilt_to(self, angle):
        self.tilt_angle = max(self.min_angle, min(self.max_angle, angle))
        print("tilt:{}".format(self.tilt_angle))
        self.servos.set_angle(self.tilt_angle)
        return self.tilt_angle == self.max_angle or self.tilt_angle == self.min_angle
    
    def pan(self, d_angle):
        self.pan_angle += d_angle
        self.pan_angle %= 360
        self.stepper.step_to_angle(d_angle)
    
    def pan_forever(self, direction):
        """ Direction is 1 or -1 """
        self.stepper.step_forever(-direction)
    
    def stop_pan(self):
        print("pan:{}".format(self.pan_angle))
        self.stepper.stop()
    
    def _tilt_loop(self):
        maxed = self.tilt_to(self.tilt_angle-self.tilt_dir)
        if maxed:
            self.stop_tilt()
    
    def tilt(self, speed=None):
        """ Tilt up until told to stop
        
        """
        if speed == None: speed = self.tilt_speed
        self.tilt_dir = speed * self.tilt_delay
        if self.tilt_loop: self.stop_tilt()
        self.tilt_loop = task.LoopingCall(f=self._tilt_loop)
        self.tilt_loop.start(self.tilt_delay)
    
    def tilt_down(self, speed=None):
        if speed == None: speed = self.tilt_speed
        self.tilt(-speed)
    
    def stop_tilt(self):
        try:
            self.tilt_loop.stop()
        except:
            pass
        self.tilt_loop = None
    
    def fire(self):
        print("bang")
    
    def calibrate(self):
        print("Calibrating... DING")
    
    def __del__(self):
        IO.cleanup()

class TestTurret(Turret):
    
    def _init_servos(self):
        self.tilt_angle = 90
        self.tilt_speed = 45 # Default tilt speed, in degrees per second
        self.tilt_delay = 1.0/20.0 # time between step increments; servo pulses are only 60hz
        self.tilt_loop = None
        self.tilt_dir = 0 # Angle increment per step

    def _init_stepper(self):
        self.pan_angle = 0
    
    def _init_led(self):
        pass
    
    def tilt_to(self, angle):
        self.tilt_angle = max(self.min_angle, min(self.max_angle, angle))
        print("tilt:{}".format(self.tilt_angle))
        return self.tilt_angle == self.max_angle or self.tilt_angle == self.min_angle
    
    def pan(self, d_angle):
        self.pan_angle += d_angle
        self.pan_angle %= 360
        print("pan angle: {}".format(d_angle))
    
    def pan_forever(self, direction):
        """ Direction is 1 or -1 """
        print("panning forever %s" %direction)
    
    def stop_pan(self):
        print("stopped pan")
    
    def _tilt_loop(self):
        try:
            maxed = self.tilt_to(self.tilt_angle+self.tilt_dir)
            if maxed:
                self.stop_tilt()
        except Exception as e:
            print("ERR: {}".format(e))
            
    
    def tilt(self, speed=None):
        """ Tilt up until told to stop
        
        """
        if speed == 0:
            self.stop_tilt()
            return
        if speed == None: speed = self.tilt_speed
        self.tilt_dir = speed * self.tilt_delay
        print("tilting forever at {}".format(self.tilt_dir))
        if self.tilt_loop: self.stop_tilt()
        self.tilt_loop = task.LoopingCall(f=self._tilt_loop)
        self.tilt_loop.start(self.tilt_delay)
    
    def tilt_down(self, speed=None):
        if speed == None: speed = self.tilt_speed
        self.tilt(-speed)
    
    def stop_tilt(self):
        print("stopped at {}".format(self.tilt_angle))
        try:
            self.tilt_loop.stop()
        except Exception as e:
            print("ERR: {}".format(e))
        self.tilt_loop = None
    
    def fire(self):
        print("bang")
    
    def __del__(self):
        #IO.cleanup()
        pass

class ThreadTurret(Turret):
    def __init__(self, tilt_min=-90, tilt_max = 90):
            super(Turret, self).__init__(tilt_min, tilt_max)
            self._tilt_thread = None
            self.tilt_loop = False

    def _tilt_worker(self):
        self.tilt_loop = True
        while(self.tilt_loop):
            self._tilt_loop()
            time.sleep(self.tilt_delay)
        self._tilt_thread = None

    def tilt(self, speed=None):
        if speed == 0:
            self.stop_tilt()
            return
        if speed == None: speed = self.tilt_speed
        self.tilt_dir = speed * self.tilt_delay
        if self._tilt_thread:
            self.stop_tilt()
        self._tilt_thread = threading.Thread(target=self._tilt_worker)
        self._tilt_thread.start()

    def stop_tilt(self):
        print("Stopping tilt at {}".format(self.tilt_angle))
        if self._tilt_thread:
            self.tilt_loop = False



"""
panLeft()
panRight()
panStop()

tiltUp(speed)
start moving up and continue 'indefinitely' 
if limit hit, stop
Optionally, move up at given speed

If another tilt was already executing, interrupt its direction and speed with current speed.

tiltDown()
tiltStop()
stop servo at current position
"""
