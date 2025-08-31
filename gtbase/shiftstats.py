# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 08:18:35 2025

@author: RTB
"""

import numpy as np

from gtbase.speedstats import SpeedTest, get_distance
from gtbase.datacollector import VTACurve

#Basic idea is to create two acceleration traces, one for each style of shifting
#Then draw a plot to compare the differences

# blinkyrun = gtbeep.speedstats.tests[5].runs[0]
# blinkydistance = [get_distance(blinkyrun[0], p) for p in blinkyrun]
# blinkycurve = VTACurve(blinkyrun)

# beeprun = gtbeep.speedstats.tests[5].runs[0]
# beepdistance = [get_distance(beeprun[0], p) for p in beeprun]
# beepcurve = VTACurve(beeprun)

# beepinterp = np.interp(beepdistance, blinkydistance, blinkycurve.t)

# delta = beepinterp - blinkycurve.t[:-4]
# plt.plot(beepdistance, delta)

class ShiftStats ():
    BASE = [
             (80, 250,), (80, 250,)
           ]
    
    def __init__(self, config=None):
        self.activetest = 0
        self.tests = [SpeedTest(*entry, do_print=None) for entry in self.BASE]
    
    def reset(self):
        for test in self.tests:
            test.reset()
        self.activetest = 0
    
    def update(self, gtdp):
        finished = self.tests[self.activetest].update(gtdp)
        if finished:
            print("Test finished, swapping!")
            #if run finished, swap to next test
            self.activetest = (self.activetest+1) % len(self.tests)
            print(f'active test: {self.activetest}')
    
    def set_speeds(self, lower=80, upper=250):
        for test in self.tests:
            test.start.set(lower)
            test.end.set(upper)
    
