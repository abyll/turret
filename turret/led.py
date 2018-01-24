#! /usr/bin/env python

class DimmerLED():
    def __init__(self, pwm, ch):
        self.pwm = pwm
        self.ch = ch
    
    def set_brightness(self, brightness):
        """ brightness being float from 0-1"""
        assert(0 <= brightness <= 1)
        self.pwm.set_pwm(self.ch, 0, int(brightness*4095))

class DimmerRGB():
    def __init__(self, pwm, ch_r, ch_g, ch_b):
        self.pwm = pwm
        self.ch_r = ch_r
        self.ch_g = ch_g
        self.ch_b = ch_b
    
    def set_color(self, r, g, b):
        """ brightness being float from 0-1"""
        assert(0 <= r <= 1)
        assert(0 <= g <= 1)
        assert(0 <= b <= 1)
        self.pwm.set_pwm(self.ch_r, 0, int(r*4095))
        self.pwm.set_pwm(self.ch_g, 0, int(g*4095))
        self.pwm.set_pwm(self.ch_b, 0, int(b*4095))