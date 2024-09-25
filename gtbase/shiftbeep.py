# -*- coding: utf-8 -*-
"""
Created on Sun Aug 18 10:45:28 2024

@author: RTB
"""

from collections import deque

from config import config, FILENAME_SETTINGS
config.load_from(FILENAME_SETTINGS)

from forzabase.shiftbeep import ShiftBeep

from gtbase.gtudploop import GTUDPLoop
from gtbase.rpm import RPM
from gtbase.history import History
from gtbase.carordinal import CarOrdinal
from gtbase.gear import Gears, MAXGEARS
from gtbase.enginecurve import EngineCurve
from gtbase.configvar import (HysteresisPercent, DynamicToneOffsetToggle, Volume,
                            RevlimitPercent, RevlimitOffset, ToneOffset, 
                            IncludeReplay)
from gtbase.lookahead import Lookahead
from gtbase.datacollector import DataCollector

from utility import beep, multi_beep, Variable

#TODO:
    #Save gearing
    #drag fit now outputs a curve with 100 point intervals (changable)
    # this is through nearest point interpolation, without any using regression
    # this could be improved, but has a rolling average built in

    #Create an acceleration curve per gear for a more accurate prediction
    #  using the Lookahead slope_factor which is currently used for torque only
    #  This will depend on slip ratio because engine rpm and velocity are not
    #  strictly linear
    #Write script to download csv files for database
    #Automatically determine PS IP through socket or brute force?
    #Investigate y axis on Special Route X: is it really flat?
    
    # Test the duration of coasting required for accurate values
        #The [1,2] exponent gives an arbitrarily good fit with coasting
        #Tests indicate a midrange speed works better than just high speed
        #add a beep once enough coasting has been done?
            # preferably speed based because we depend on having an accurate
            # interval to fit a polynomial to

#NOTES:
    #The Transmission shift line in the Tuning page is _NOT_ equal to revbar 
    #blinking if ECU or Transmission are not stock. It can be be off by 
    #100-400rpm depending on the combo used. Other parts may also affect the 
    #valid RPM range and not update the revbar appropriately. 
    #The revbar maximum seems to stick to 100 rpm intervals, rounded down from
    #the Transmission shift line if there are upgrades.

    #Revbar runs from 85% to 99% of the revbar variable in telemetry
    #This can be used to provide guesstimates for shift points without a beep
    #Especially in the Copy section
    #Turbo boolean can be used to imply to shift a little beyond the given
    #shift points. Maybe detect maximum boost? The higher the boost the worse
    #the penalty to shifting.


#main class for ForzaShiftTone
#it is responsible for the main loop
class ShiftBeep(ShiftBeep):
    LOOP_FUNCS = [
         'loop_test_car_changed', #reset if car ordinal/PI changes
         'loop_update_revbar',    #set revbar min/max rpm
         'loop_update_rpm',       #update tach and hysteresis rpm
         # 'loop_guess_revlimit',   #guess revlimit if not defined yet
         'loop_linreg',           #update lookahead with hysteresis rpm
         'loop_datacollector',    #add data point for curve collecting
         # 'loop_update_gear',      #update gear ratio and state of gear
       #  'loop_calculate_shiftrpms',#derive shift rpm if possible
         'loop_test_for_shiftrpm',#test if we have shifted
         'loop_beep',             #test if we need to beep
         'debug_log_full_shiftdata'             
            ]
    def __init__(self):
        self.init_vars()     
        self.loop.firststart() #trigger start of loop given IP address

    #variables are defined again in init_gui_vars, purpose is to split baseline
    #and gui eventually
    def init_vars(self):
        self.loop = GTUDPLoop(config, loop_func=self.loop_func)
        self.gears = Gears(config)
        self.datacollector = DataCollector(config)
        self.lookahead = Lookahead(config)
        self.history = History(config)
        
        self.car_ordinal = CarOrdinal()
        
        self.tone_offset = ToneOffset(config)
        self.hysteresis_percent = HysteresisPercent(config)
        self.revlimit_percent = RevlimitPercent(config)
        self.revlimit_offset = RevlimitOffset(config)
        self.dynamictoneoffset = DynamicToneOffsetToggle(config)
        self.includereplay = IncludeReplay(config)
        
        self.rpm = RPM(hysteresis_percent=self.hysteresis_percent)
        self.volume = Volume(config)
        
        self.we_beeped = 0
        self.beep_counter = 0
        self.debug_target_rpm = -1
        self.revlimit = Variable(defaultvalue=-1)
        
        self.curve = EngineCurve(config)

        self.shiftdelay_deque = deque(maxlen=120)

    def reset(self, *args):
        super().reset()
    
    #called when car ordinal changes or data collector finishes a run
    def handle_curve_change(self, gtdp, *args, **kwargs):
        print("Updating gears")
        self.gears.update(gtdp)
        super().handle_curve_change(gtdp, *args, **kwargs)

    #called when the car id has changed from loop_test_car_changed
    def print_car_changed(self, gtdp):
        print(f'New ordinal {self.car_ordinal.get()}, resetting!')
        print(f'New car: {self.car_ordinal.get_name()}')
        print(f'Hysteresis: {self.hysteresis_percent.as_rpm(gtdp):.1f} rpm')
        print(f'Engine: {gtdp.engine_max_rpm:.0f} max rpm')

    #reset if the car_ordinal changes
    #if a car has more than 8 gears, the packet won't contain the ordinal as
    #the 9th gear will overflow into the cr ordinal location
    def loop_test_car_changed(self, gtdp):
        super().loop_test_car_changed(gtdp)

    def loop_update_revbar(self, gtdp):
        self.revbardata.update(gtdp.upshift_rpm)
        
    #update internal rpm taking the hysteresis value into account:
    #only update if the difference between previous and current rpm is large
    def loop_update_rpm(self, gtdp):
        super().loop_update_rpm(gtdp)

    def loop_linreg(self, gtdp):
        super().loop_linreg(gtdp)

    #set curve with drag data if we collected a complete run
    def loop_datacollector(self, gtdp):
        super().loop_datacollector(gtdp)

    # def loop_update_gear(self, gtdp):
    #     self.gears.update(gtdp)

    #Function to derive the rpm the player started an upshift at full throttle
    #GT7 has a convenient boolean if we are in gear. Therefore any time we are
    #not in gear and there is an increase in the gear number, there has been
    #an upshift. 
    #We then run back to the first full throttle packet, because GT7 first 
    #drops power before disengaging the clutch and swapping gear
    #This is not actually visible in telemetry: Clutch is binary instead of
    #a 0 - 1 floating point range.
    def loop_test_for_shiftrpm(self, gtdp):
        #case gear is the same in new gtdp or we start from zero
        if (len(self.shiftdelay_deque) == 0 or 
                                   self.shiftdelay_deque[0].gear == gtdp.gear):
            self.shiftdelay_deque.appendleft(gtdp)
            self.tone_offset.increment_counter()
            return
        #case gear has gone down: reset
        if self.shiftdelay_deque[0].gear > gtdp.gear:
            self.shiftdelay_deque.clear()
            self.tone_offset.reset_counter()
            self.debug_target_rpm = -1 #reset target rpm
            return
        #case gear has gone up
        prev_packet = gtdp
        shiftrpm = None
        gear_change = False
        for packet in self.shiftdelay_deque:
            if packet.throttle == 0: #TODO: is this useful?
                break
            if (not prev_packet.in_gear and packet.in_gear):
                gear_change = True
            if (gear_change and 
                (prev_packet.throttle < 255 and packet.throttle == 255)):
                shiftrpm = packet.current_engine_rpm
                break
            prev_packet = packet
            self.tone_offset.decrement_counter()
            
        if shiftrpm is not None: #gtdp.gear is the upshifted gear, one too high
            self.history.update(self.debug_target_rpm, shiftrpm, gtdp.gear-1, 
                                self.tone_offset.get_counter())
            if self.dynamictoneoffset.get():
                self.tone_offset.finish_counter() #update dynamic offset logic
        self.we_beeped = 0
        self.debug_target_rpm = -1
        self.shiftdelay_deque.clear()
        self.tone_offset.reset_counter()

    #play beep depending on volume. If volume is zero, skip beep
    def do_beep(self):
        super().do_beep()

    def loop_beep(self, gtdp):
        super().loop_beep(gtdp)

    def debug_log_full_shiftdata(self, gtdp):
        super().debug_log_full_shiftdata(gtdp)

    def loop_test_skip(self, gtdp):
        return not(self.includereplay.test(gtdp) and 
               (1 <= int(gtdp.gear) <= MAXGEARS) and
               not gtdp.loading and not gtdp.paused)
        
    #this function is called by the loop whenever a new packet arrives
    def loop_func(self, gtdp):
        super().loop_func(gtdp)

    #TODO: Move the torque ratio function to PowerCurve
    #to account for torque not being flat, we take a linear approach
    #we take the ratio of the current torque and the torque at the shift rpm
    # if < 1: the overall acceleration will be lower than a naive guess
    #         therefore, scale the slope down: trigger will happen later
    # if > 1: the car will accelerate more. This generally cannot happen unless
    # there is partial throttle.
    # Returns a boolean if target_rpm is predicted to be hit in 'offset' number
    # of packets (assumed at 60hz) and the above factor for debug printing
    def torque_ratio_test(self, target_rpm, offset, gtdp):
        return super().torque_ratio_test(target_rpm, offset, gtdp)

    #make sure the target_rpm is the lowest rpm trigger of all triggered beeps
    #used for debug logging
    def update_target_rpm(self, val):
        super().update_target_rpm(val)

    #test for the three beep triggers:
        #if shiftrpm of gear will be hit in x time (from_gear)
        #if revlimit will be hit in x+y time
        #if percentage of revlimit will be hit in x time
    def test_for_beep(self, shiftrpm, gtdp):
        return super().test_for_beep(shiftrpm, gtdp)

    #write all settings that can change to the config file
    def config_writeback(self, varlist=['tone_offset']):        
        super().config_writeback(varlist)

    def close(self):
        super().close()

def main():
    global gtbeep #for debugging
    gtbeep = ShiftBeep()

if __name__ == "__main__":
    main()