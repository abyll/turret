#! /usr/bin/env python
# Simple demo of of the PCA9685 PWM servo/LED controller library.
# This will move channel 0 from min to max position repeatedly.
# Author: Tony DiCola
# License: Public Domain


def clamp(a, low, high):
    return max(low, min(high, a))

# Uncomment to enable debug output.
#import logging
#logging.basicConfig(level=logging.DEBUG)

# Initialise the PCA9685 using the default address (0x40).

# Alternatively specify a different address and/or bus:
#pwm = Adafruit_PCA9685.PCA9685(address=0x41, busnum=2)
class Servo():
    # Configure min and max servo pulse lengths
    pulse_length = 1000000 // 60 // 4096 # 1,000,000 us per second, 60 Hz, 12 bits of resolution to a pulse
    pulse_min = 150  # Min pulse length out of 4096 - 0 degrees for a servo
    pulse_max = 600  # Max pulse length out of 4096 - 180 degrees for a servo
    servo_freq = 60
    def __init__(self, pwm, channel, min, max):
        # angle limits
        self.min_angle = min
        self.max_angle = max
        self.channel = channel
        self.pwm = pwm
        self.pwm.set_pwm_freq(self.servo_freq)
    
    # Helper function to make setting a servo pulse width simpler.
    def _set_servo_pulse(self, pulse):
        self.pwm.set_pwm(self.channel, 0, int(pulse))
    
    def set_angle(self, angle):
        #clamp angle
        angle = clamp(angle, self.min_angle, self.max_angle)
        print("angle: {}".format(angle))
        #map angle to pulse width
        pulse = (self.pulse_max-self.pulse_min) * (angle / 180.0) + self.pulse_min
        pulse = clamp(pulse, self.pulse_min, self.pulse_max) #safety limit
        print("pulse: {}".format(pulse))
        self._set_servo_pulse(pulse)

class ServoPair():
    """ Encapsulates a pair of servos, where one is mirrored and working in tandem"""
    def __init__(self, pwm, chan_a, chan_b, min, max):
        self.ch_a = chan_a
        self.ch_b = chan_b
        self.min_angle = min
        self.max_angle = max
        
        self.a = Servo(pwm, chan_a, min, max)
        self.b = Servo(pwm, chan_b, 180-max, 180-min)
    
    def set_angle(self, angle):
        self.a.set_angle(angle)
        self.b.set_angle(180-angle)
    

if __name__ == "__main__":
    chA = 0
    chB = 1

    import time
    import Adafruit_PCA9685
    pwm = Adafruit_PCA9685.PCA9685()
    # define range of PITCH
    a = Servo(pwm, chA, 70, 110)
    b = Servo(pwm, chB, 70, 110) # note: reversed servo's angles need to be accounted for

    pause = 1
    print('Moving servos, press Ctrl-C to quit...')
    try:
      while True:
        # Move servo on channel O between extremes.
        a.set_angle(70)
        b.set_angle(110)
        time.sleep(pause)
        a.set_angle(110)
        b.set_angle(70)
        time.sleep(pause)
    finally:
        a.set_angle(90)
        b.set_angle(90)
