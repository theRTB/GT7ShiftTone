# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 11:23:10 2024

@author: RTB
"""

import math
from collections import deque

from utility import Variable

def get_distance(gtdp1, gtdp2):
    return math.sqrt( (gtdp1.position_x - gtdp2.position_x)**2 + 
                      (gtdp1.position_y - gtdp2.position_y)**2 +
                      (gtdp1.position_z - gtdp2.position_z)**2)

class SpeedTest():
    INITIAL, WAIT, RUNNING, FINISHED = 0,1,2,3
    MAXRUNS = 1
    #do_print is None, all
    #default is print result
    #all is print entire packet
    def __init__(self, start, end, min_distance=0, start_rpm=0, end_rpm=0, 
                 do_print='full'):
        self.start = Variable(start)
        self.end = Variable(end)
        self.min_distance = Variable(min_distance)
        
        self.start_rpm = Variable(start_rpm)
        self.end_rpm = Variable(end_rpm)
        
        self.use_revlimit = end_rpm == -1
        
        self.time = Variable(0)
        self.distance = Variable(0)
        
        self.packets = []
        self.runs = deque(maxlen=self.MAXRUNS)
        
        self.state = self.INITIAL
        
        self.do_print = do_print
        
        if do_print == 'full':
            print (f"Initialized to {start} - {end} dist {min_distance} "
                   f"RPM {start_rpm} - {end_rpm}")
        
    def reset(self):
        self.use_revlimit = self.end_rpm.get() == -1
        if self.use_revlimit:
            self.end_rpm.set(-1)
        
        self.packets.clear()
        self.runs.clear()
        
        self.time.set(0)
        self.distance.set(0)
        
        self.state = self.INITIAL
    
    def start_condition(self, gtdp):
        return (gtdp.speed > self.start.get()/3.6 and 
                gtdp.current_engine_rpm > self.start_rpm.get())
    
    def end_condition(self, gtdp):
        return (gtdp.speed >= self.end.get()/3.6 and 
                get_distance(self.packets[0], gtdp) >= self.min_distance.get() 
                and gtdp.current_engine_rpm >= self.end_rpm.get())
    
    #data to track
    # gtdp.:
        #position x y z
        #current engine rpm
        #speed
        #boost
        #packet id
        #gear
        #throttle
        #brake
        #handbrake
        #tire rotation speed (for slip ratio), not tracked packet yet
    
    #single print:
        #gtdp.
        #car ordinal
        #upshift rpm
        #gears
    #speed in m/s: self.start in kph
    def update(self, gtdp):
        # print(f'state {self.state} throttle {gtdp.throttle} speed {gtdp.speed} - {self.start.get()/3.6}')
        if self.state == self.INITIAL:
            # print(f"INITIAL {gtdp.throttle == 0} {gtdp.speed < self.start.get()/3.6}")
            if gtdp.throttle == 0 and not self.start_condition(gtdp):
                self.state = self.WAIT
                # print("INITIAL TO WAIT")
                
        if self.state == self.WAIT:
            if (gtdp.throttle > 0 and (not gtdp.handbrake) #and gtdp.brake == 0 
                and self.start_condition(gtdp)):
                self.packets.clear()
                self.state = self.RUNNING
                # print("WAIT TO RUNNING")
                
        if self.state == self.RUNNING:   #(gtdp.throttle == 0 and gtdp.in_gear) or #does not work: upshifts affect throttle outside of being in gear
            if (gtdp.handbrake #or gtdp.brake != 0
                or not self.start_condition(gtdp)): #gtdp.speed < self.start.get()/3.6):
                # print(f'{gtdp.brake} or {gtdp.handbrake}'
                #         f' or {gtdp.speed} < {self.start.get()/3.6}')
                # print("RESET RUNNING")
                self.reset()
                return
            self.packets.append(gtdp)        

            if self.end_condition(gtdp):
                self.time.set(len(self.packets) / 60)
                self.distance.set(get_distance(self.packets[0], gtdp))
                self.state = self.FINISHED
        
        if self.state == self.FINISHED:
            self.run_finished()
            self.state = self.INITIAL
            
    def run_finished(self):
        if self.do_print is None:
            return
        
        if self.do_print == 'full':
            pass
            #print the whole packet array
        
        start, end = self.packets[0].speed*3.6, self.packets[-1].speed*3.6
        
        #case print result
        print(f'Start {self.start.get()} End {self.end.get()} Min Dist {self.min_distance.get()}\n'
              f'Speeds: {start:.1f} - {end:.1f}, distance: {self.distance.get():.0f}, time: {self.time.get():.2f}\n')

        #Most recent run is always first element
        self.runs.appendleft(self.packets.copy())

class SpeedStats():
    BASE = [
             (0, 97,), (0, 161,), #0-60mph, 0-100 mph
             (100, 150,),  #speed
             (0, 0, 400),                            #distance
             (0, 0, 1000),
             (0, 0, 0, 1500, -1) #RPM based
           ]
    
    def __init__(self, config):
        self.do_print = config.speedstats_do_print
        self.tests = [SpeedTest(*entry, do_print=self.do_print) 
                                                      for entry in self.BASE]
    
    def set_revlimit(self, revlimit):
        for test in self.tests:
            if test.end_rpm.get() == -1:
                test.end_rpm.set(revlimit)
    
    def reset(self):
        for test in self.tests:
            test.reset()
    
    def update(self, gtdp):
        for test in self.tests:
            test.update(gtdp)