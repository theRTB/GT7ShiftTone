# -*- coding: utf-8 -*-
"""
Created on Sun May  7 19:35:24 2023

@author: RTB
"""

#replaced tkinter with supposed thread safe tkinter variant
#instead of freezing when the main thread isn't under control of tkinter,
#it now crashes instead. Theoretically, an improvement.
from mttkinter import mtTkinter as tkinter
#import tkinter
import tkinter.ttk

import math
from collections import deque

#tell Windows we are DPI aware
import ctypes
PROCESS_SYSTEM_DPI_AWARE = 1
PROCESS_PER_MONITOR_DPI_AWARE = 2
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_SYSTEM_DPI_AWARE)

from config import config, FILENAME_SETTINGS
config.load_from(FILENAME_SETTINGS)

from gear import Gears, GUIGears, MAXGEARS
# from curve import Curve
from lookahead import Lookahead
from datacollector import DataCollector
from gtudploop import GTUDPLoop
from utility import beep, multi_beep, packets_to_ms, Variable
from buttongraph import GUIButtonGraph
from guiconfigvar import (GUIRevlimitPercent, GUIRevlimitOffset, GUIToneOffset,
                          GUIHysteresisPercent, GUIRevlimit, GUIVolume, 
                          GUIPeakPower, GUITach, GUIButtonStartStop, 
                          GUIButtonVarEdit, GUITargetIP, GUIRevbarData,
                          GUIButtonDynamicToggle, GUIGTUDPLoop)
#TODO:
    #move Volume, start/reset buttons, PS5 IP into its own labelframe
    #Copy button: open Textbox with various stats pasted for copy and paste
    #Revbar runs from 85% to 99% of the revbar variable in telemetry
    #This can be used to provide guesstimates for shift points without a beep
    #Especially in the Copy section
    #The Transmission shift line is _NOT_ equal to revbar blinking if ECU or
    #Transmission are not stock. It can be be off by 100-400rpm depending 
    #on the combo used. Other parts may also affect the valid RPM range and not
    #update the revbar appropriately. It seems to stick to 100 rpm intervals.

#main class for ForzaShiftTone
#it is responsible for creating and managing the tkinter window
#and maintains the loop logic
#splitting these two has resulted in the window not responding for several
#seconds after launching, despite the back-end still updating
class GTBeep():
    TITLE = "GTShiftTone: Dynamic shift tone for Gran Turismo 7"
    WIDTH, HEIGHT = 813, 289 #most recent dump of size at 150% scaling
    
    def __init__(self):
        self.init_vars()
        self.init_tkinter()
        self.init_gui_vars()
        self.init_gui_grid()
        
        self.loop.firststart() #trigger start of loop given IP address
        self.root.mainloop()

    #variables are defined again in init_gui_vars, purpose is to split baseline
    #and gui eventually
    def init_vars(self):
        self.loop = GTUDPLoop(target_ip=config.target_ip, 
                              loop_func=self.loop_func)
        self.gears = Gears()
        self.datacollector = DataCollector(config=config)
        self.lookahead = Lookahead(config.linreg_len_min,
                                   config.linreg_len_max)
        self.we_beeped = 0
        self.beep_counter = 0
        self.debug_target_rpm = -1
        self.revlimit = Variable(defaultvalue=-1)
        self.rpm_hysteresis = 0
        
        self.curve = None

        self.shiftdelay_deque = deque(maxlen=120)

        self.car_ordinal = None

    def init_tkinter(self):
        self.root = tkinter.Tk()
        self.root.title(self.TITLE)
        
        #100% scaling is ~96 dpi in Windows, tkinter assumes ~72 dpi
        #window_scalar allows the user to scale the window up or down
        #the UI was designed at 150% scaling or ~144 dpi
        #we have to fudge width a bit if scaling is 100%
        screen_dpi = self.root.winfo_fpixels('1i')
        dpi_factor = (96/72) * (screen_dpi / 96) * config.window_scalar
        size_factor = screen_dpi / 144 * config.window_scalar
        width = math.ceil(self.WIDTH * size_factor)
        height = math.ceil(self.HEIGHT * size_factor)
        if screen_dpi <= 96.0:
            width += 40 #hack for 100% size scaling in Windows
        
        # self.root.geometry(f"{width}x{height}") #not required
        if config.window_x is not None and config.window_y is not None:
            self.root.geometry(f'+{config.window_x}+{config.window_y}')
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.resizable(False, False)
        self.root.tk.call('tk', 'scaling', dpi_factor)
        # self.root.attributes('-toolwindow', True) #force on top

    def init_gui_varframe(self):
        frame = tkinter.LabelFrame(self.root, text='Variables')
        self.varframe = frame
        
        self.tone_offset = GUIToneOffset(frame, config)
        self.hysteresis_percent = GUIHysteresisPercent(frame, config)
        self.revlimit_percent = GUIRevlimitPercent(frame, config)
        self.revlimit_offset = GUIRevlimitOffset(frame, config)
        self.buttonvaredit = GUIButtonVarEdit(frame, self.edit_handler)
        self.dynamictoneoffset = GUIButtonDynamicToggle(frame, config)
        self.buttonvaredit.invoke() #trigger disabling of var boxes

    def init_gui_vars(self):
        root = self.root
        self.loop = GUIGTUDPLoop(root, config, loop_func=self.loop_func)
        self.gears = GUIGears(root)
        self.revlimit = GUIRevlimit(root, defaultvalue=-1)
        self.volume = GUIVolume(root, value=config.volume)
        self.peakpower = GUIPeakPower(root)
        self.revbardata = GUIRevbarData(root)
        self.tach = GUITach(root)
        
        self.buttonreset = tkinter.Button(root, text='Reset', borderwidth=3, 
                                          command=self.reset)
        
        self.buttongraph = GUIButtonGraph(root, self.buttongraph_handler, 
                                          config)
        
        self.init_gui_varframe()

    def init_gui_varframe_grid(self):
        self.tone_offset.grid(       row=0, column=0)
        self.hysteresis_percent.grid(row=1, column=0)
        self.revlimit_percent.grid(  row=2, column=0)
        self.revlimit_offset.grid(   row=3, column=0)
        
        self.buttonvaredit.grid(     row=0, column=3)
        self.dynamictoneoffset.grid( row=5, column=0, columnspan=3)

    def init_gui_grid(self):
        self.gears.init_grid()
        row = GUIGears.ROW_COUNT #start from row below gear display
        
        #force minimum row size for other rows
        self.root.rowconfigure(index=row+3, weight=1000)
        
        self.volume.grid(     row=0,     column=12, rowspan=4)         
       
        self.revlimit.grid(   row=row,   column=0)    
        self.revbardata.grid( row=row,   column=3)
        self.varframe.grid(   row=row,   column=7, rowspan=5, columnspan=4, 
                                                            sticky=tkinter.EW)
        
        self.peakpower.grid(  row=row+1, column=0)   
        self.loop.grid(       row=row+1, column=4, rowspan=3, columnspan=3,
                                                             sticky=tkinter.EW)
        self.buttongraph.grid(row=row+1, column=12, rowspan=3)
                
        self.buttonreset.grid(row=row+3, column=2)
        self.tach.grid(       row=row+4, column=0)

        self.init_gui_varframe_grid()

    def buttongraph_handler(self, event=None):
        self.buttongraph.create_window(self.curve, self.revlimit_percent.get())

    #enable or disable modification of the four listed variable spinboxes
    def edit_handler(self):
        state = 'readonly' if self.buttonvaredit.get() else tkinter.DISABLED
        for var in [self.revlimit_offset, self.revlimit_percent,
                    self.tone_offset, self.hysteresis_percent]:
            var.config(state=state)

    def reset(self, *args):
        self.datacollector.reset()
        self.lookahead.reset()

        self.we_beeped = 0
        self.beep_counter = 0
        self.debug_target_rpm = -1
        self.curve = None
        
        self.car_ordinal = None

        self.tach.reset()
        self.revlimit.reset()
        self.peakpower.reset()
        self.revbardata.reset()
        self.buttongraph.reset()

        self.shiftdelay_deque.clear()
        self.tone_offset.reset_counter()
        self.rpm_hysteresis = 0

        self.gears.reset()

    #reset if the car_ordinal or the PI changes
    #if a car has more than 8 gears, the packet won't contain the ordinal as
    #the 9th gear will overflow into the car ordinal location
    def loop_test_car_changed(self, gtdp):
        if gtdp.car_ordinal == 0 or gtdp.car_ordinal > 1e5:
            return
        if (self.car_ordinal != gtdp.car_ordinal):
            self.reset()
            self.car_ordinal = gtdp.car_ordinal
            print(f'New ordinal {self.car_ordinal}, PI Unknown: resetting!')
            print(f'Hysteresis: {self.hysteresis_percent.as_rpm(gtdp):.1f} rpm')
            print(f'Engine: Unknown min rpm, {gtdp.engine_max_rpm:.0f} max rpm')
            #TODO:
                #Find and load the appropriately named json file for data

    def loop_update_revbar(self, gtdp):
        self.revbardata.update(gtdp.upshift_rpm)

    #update internal rpm taking the hysteresis value into account:
    #only update if the difference between previous and current rpm is large
    def loop_update_rpm(self, gtdp):
        rpm = gtdp.current_engine_rpm
        
        hysteresis = self.hysteresis_percent.as_rpm(gtdp)
        if abs(rpm - self.rpm_hysteresis) >= hysteresis:
            self.rpm_hysteresis = rpm

        self.tach.update(rpm)

    #Not currently used
    def loop_guess_revlimit(self, gtdp):
        if config.revlimit_guess != -1 and self.revlimit.get() == -1:
            self.revlimit.set(gtdp.engine_max_rpm - config.revlimit_guess, 
                              state='guess')
            print(f'guess revlimit: {self.revlimit.get()}')    

    def loop_linreg(self, gtdp):
        self.lookahead.add(self.rpm_hysteresis) #update linear regresion

    def loop_datacollector_setcurve(self):
        self.curve = self.datacollector.get_curve()
        self.revlimit.set(self.curve.get_revlimit())
        self.peakpower.set(*self.curve.get_peakpower_tuple())
        self.buttongraph.enable()
        
        if config.notification_power_enabled:
            multi_beep(config.notification_file,
                       config.notification_file_duration,
                       config.notification_power_count,
                       config.notification_power_delay)
            
    #grab curve if we collected a complete run
    def loop_datacollector(self, gtdp):
        self.datacollector.update(gtdp)

        if not self.datacollector.is_run_completed():
            return

        if self.curve is None:
            self.loop_datacollector_setcurve()
            self.gears.calculate_shiftrpms(self.curve.rpm, self.curve.power)

    def loop_update_gear(self, gtdp):
        self.gears.update(gtdp)

    # def loop_calculate_shiftrpms(self):
    #     if self.curve is None:
    #         return
    #     self.gears.calculate_shiftrpms(self.curve.rpm, self.curve.power)

    def debug_log_basic_shiftdata(self, shiftrpm, gear, beep_distance):
        target = self.debug_target_rpm
        difference = 'N/A' if target == -1 else f'{shiftrpm - target:4.0f}'
        beep_distance_ms = 'N/A'
        if beep_distance is not None:
            beep_distance_ms = packets_to_ms(beep_distance)
        print(f"gear {gear-1}-{gear}: {shiftrpm:.0f} actual shiftrpm, {target:.0f} target, {difference} difference, {beep_distance_ms} ms distance to beep")
        print("-"*50)

    #Function to derive the rpm the player initiated an upshift
    #GT7 has a convenient boolean if we are in gear. Therefore any time we are
    #not in gear and there is an increase in the gear number, there has been
    #an upshift. We assume the packet before in_gear turns false is the frame
    #the player pressed upshift.
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
        for packet in self.shiftdelay_deque:
            if packet.throttle == 0:
                break
            # if prev_packet.power < 0 and packet.power >= 0:
            if not prev_packet.in_gear and packet.in_gear:
                shiftrpm = packet.current_engine_rpm
                break
            prev_packet = packet
            self.tone_offset.decrement_counter()
        if shiftrpm is not None:
            counter = self.tone_offset.get_counter()
            if self.dynamictoneoffset.get():
                self.tone_offset.finish_counter() #update dynamic offset logic
            if config.log_basic_shiftdata:
                self.debug_log_basic_shiftdata(shiftrpm, gtdp.gear, counter)
        self.we_beeped = 0
        self.debug_target_rpm = -1
        self.shiftdelay_deque.clear()
        self.tone_offset.reset_counter()

    #play beep depending on volume. If volume is zero, skip beep
    def do_beep(self):
        if volume_level := self.volume.get():
            beep(filename=config.sound_files[volume_level])

    def loop_beep(self, gtdp):
        rpm = gtdp.current_engine_rpm
        beep_rpm = self.gears.get_shiftrpm_of(gtdp.gear)
        if self.beep_counter <= 0:
            if self.test_for_beep(beep_rpm, gtdp):
                self.beep_counter = config.beep_counter_max
                self.we_beeped = config.we_beep_max
                self.tone_offset.start_counter()
                self.do_beep()
            elif rpm < math.ceil(beep_rpm*config.beep_rpm_pct):
                self.beep_counter = 0
        elif (self.beep_counter > 0 and (rpm < beep_rpm or beep_rpm == -1)):
            self.beep_counter -= 1

    def debug_log_full_shiftdata(self, gtdp):
        if self.we_beeped > 0 and config.log_full_shiftdata:
            print(f'rpm {gtdp.rpm:.0f} torque N/A slope {self.lookahead.slope:.2f} intercept {self.lookahead.intercept:.2f} count {config.we_beep_max-self.we_beeped+1}')
            self.we_beeped -= 1

    def loop_func(self, gtdp):        
        #skip if not racing or gear number outside valid range
        if not(gtdp.cars_on_track and (1 <= int(gtdp.gear) <= MAXGEARS)):
            return

        self.loop_test_car_changed(gtdp) #reset if car ordinal/PI changes
        self.loop_update_revbar(gtdp) #set revbar min/max rpm
        self.loop_update_rpm(gtdp) #update tach and hysteresis rpm
        self.loop_guess_revlimit(gtdp) #guess revlimit if not defined yet
        self.loop_linreg(gtdp) #update lookahead with hysteresis rpm
        self.loop_datacollector(gtdp) #add data point for curve collecting
        self.loop_update_gear(gtdp) #update gear ratio and state of gear
        # self.loop_calculate_shiftrpms() #derive shift rpm if possible
        self.loop_test_for_shiftrpm(gtdp) #test if we have shifted
        self.loop_beep(gtdp) #test if we need to beep

        self.debug_log_full_shiftdata(gtdp)

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
        torque_ratio = 1
        if self.curve is not None:
            gtdp_torque = self.curve.torque_at_rpm(gtdp.current_engine_rpm)
            if gtdp_torque == 0:
                return
            target_torque = self.curve.torque_at_rpm(target_rpm)
            torque_ratio = target_torque / gtdp_torque

        return (self.lookahead.test(target_rpm, offset, torque_ratio),
                torque_ratio)

    #make sure the target_rpm is the lowest rpm trigger of all triggered beeps
    def update_target_rpm(self, val):
        if self.debug_target_rpm == -1:
            self.debug_target_rpm = val
        else:
            self.debug_target_rpm = min(self.debug_target_rpm, val)

    #test for the three beep triggers:
        #if shiftrpm of gear will be hit in x time (from_gear)
        #if revlimit will be hit in x+y time
        #if percentage of revlimit will be hit in x time
    def test_for_beep(self, shiftrpm, gtdp):
        #enforce minimum throttle for beep to occur
        if gtdp.throttle < config.min_throttle_for_beep:
            return False
        tone_offset = self.tone_offset.get()
        revlimit = self.revlimit.get()

        from_gear, from_gear_ratio = self.torque_ratio_test(shiftrpm,
                                                            tone_offset, gtdp)
        
        #possible idea: Always enable revlimit beep regardless of throttle
        #This may help shifting while getting on the power gradually
        #from_gear = from_gear and gtdp.throttle >= constants.min_throttle_for_beep

        revlimit_pct, revlimit_pct_ratio = self.torque_ratio_test(
            revlimit*self.revlimit_percent.get(), tone_offset, gtdp)
        revlimit_time, revlimit_time_ratio = self.torque_ratio_test(
            revlimit, (tone_offset + self.revlimit_offset.get()), gtdp)

        if from_gear:
            self.update_target_rpm(shiftrpm)            
        if revlimit_pct:
            rpm_revlimit_pct = revlimit*self.revlimit_percent.get()
            self.update_target_rpm(rpm_revlimit_pct)            
        if revlimit_time:
            slope, intercept = self.lookahead.slope, self.lookahead.intercept
            rpm_revlimit_time = intercept + slope*tone_offset
            self.update_target_rpm(rpm_revlimit_time)
        
        if from_gear and config.log_full_shiftdata:
            print(f'beep from_gear: {shiftrpm:.0f}, gear {gtdp.gear} rpm {gtdp.rpm:.0f} torque N/A trq_ratio {from_gear_ratio:.2f} slope {self.lookahead.slope:.2f} intercept {self.lookahead.intercept:.2f}')
        if revlimit_pct and config.log_full_shiftdata:
            print(f'beep revlimit_pct: {rpm_revlimit_pct:.0f}, gear {gtdp.gear} rpm {gtdp.rpm:.0f} torque N/A trq_ratio {revlimit_pct_ratio:.2f} slope {self.lookahead.slope:.2f} intercept {self.lookahead.intercept:.2f}')
        if revlimit_time and config.log_full_shiftdata:
            print(f'beep revlimit_time: {rpm_revlimit_time:.0f}, gear {gtdp.gear} rpm {gtdp.rpm:.0f} torque N/A trq_ratio {revlimit_time_ratio:.2f} slope {self.lookahead.slope:.2f} intercept {self.lookahead.intercept:.2f}')

        return from_gear or revlimit_pct or revlimit_time

    #write all GUI configurable settings to the config file
    def config_writeback(self):
        #grab x,y position to save as window_x and window_y
        self.window_x = Variable(self.root.winfo_x())
        self.window_y = Variable(self.root.winfo_y())
                
        #hack to get ip from loop
        self.target_ip = self.loop.gui_ip
        
        try:
            gui_vars = ['revlimit_percent', 'revlimit_offset', 'tone_offset',
                        'hysteresis_percent', 'volume', 'target_ip', 
                        'window_x', 'window_y', 'dynamictoneoffset']
            for variable in gui_vars:
                setattr(config, variable, getattr(self, variable).get())
            config.write_to(FILENAME_SETTINGS)
        except Exception as e: 
            print(e)
            print("Failed to write GUI variables to config file")

    def close(self):
        self.loop.close()
        self.config_writeback()
        self.root.destroy()

def main():
    global gtbeep #for debugging
    gtbeep = GTBeep()

if __name__ == "__main__":
    main()