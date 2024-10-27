# -*- coding: utf-8 -*-
"""
Created on Sun Aug 18 10:36:50 2024

@author: RTB
"""

#replaced tkinter with supposed thread safe tkinter variant
#instead of freezing when the main thread isn't under control of tkinter,
#it now crashes instead. Theoretically, an improvement.
from mttkinter import mtTkinter as tkinter
#import tkinter
import tkinter.ttk

#tell Windows we are DPI aware
import ctypes
PROCESS_SYSTEM_DPI_AWARE = 1
PROCESS_PER_MONITOR_DPI_AWARE = 2
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_SYSTEM_DPI_AWARE)

#TODO: is there an alternative way to use config?
from config import config, FILENAME_SETTINGS
config.load_from(FILENAME_SETTINGS)

from forzagui.shiftbeep import GenericGUIShiftBeep
from gtbase.shiftbeep import ShiftBeep

from gtgui.gtudploop import GUIGTUDPLoop
from gtgui.rpm import GUIRPM
from gtgui.history import GUIHistory
from gtgui.carordinal import GUICarOrdinal
from gtgui.gear import GUIGears
from gtgui.configvar import (GUIPeakPower, GUIToneOffset, GUIRevbarData,
                           GUIRevlimit, GUIVolume, GUIConfigButton)
from gtgui.enginecurve import GUIEngineCurve
from gtgui.importgraph import GUIImportGraph

# from utility import Variable

#TODO:
    # hide 0.00 rel ratio on final gear: add finalgear option somehow
    # rework row display on shift history: it visibles rotates due to slowness
    # move to labels instead
    #Grey out gear 9 and 10: non-functional for GT7
    #Maybe phase out Settings window to extend main window to the right?
    #Grid variables into those
    #Brief shift history of the last 5 shifts or so in main window?
    
    #Add Bluetooth keepalive with (near) silent audio file
    
    #Copy button: open Textbox with various stats pasted for copy and paste
    
    # Test if window scalar config variable works as expected
    # Test if changing dpi works as expected
    
#tkinter GUI wrapper around GTBeep
class GUIShiftBeep(GenericGUIShiftBeep, ShiftBeep):
    TITLE = "GTShiftTone: Dynamic shift tone for Gran Turismo 7"
    WRITEBACK_VARS = GenericGUIShiftBeep.WRITEBACK_VARS #+ ['target_ip']
    
    LOOP_FUNCS = [
         'loop_test_car_changed', #reset if car ordinal/PI changes
         'loop_update_revbar',    #set revbar min/max rpm
         'loop_update_rpm',       #update tach and hysteresis rpm
          # 'loop_guess_revlimit',   #guess revlimit if not defined yet
         'loop_linreg',           #update lookahead with hysteresis rpm
         'loop_datacollector',    #add data point for curve collecting
          # 'loop_update_gear',      #update gear ratio and state of gear
          # 'loop_calculate_shiftrpms',#derive shift rpm if possible
         'loop_test_for_shiftrpm',#test if we have shifted
         'loop_beep',             #test if we need to beep
         'debug_log_full_shiftdata'             
                ]

    def __init__(self):
        super().__init__()

    def init_gui_buttonframe(self):
        frame = tkinter.Frame(self.root)
        
        adjustables = { name:getattr(self, name) 
                                      for name in GUIConfigButton.get_names() }
        self.buttonconfig = GUIConfigButton(frame, config, adjustables)
        self.history = GUIHistory(frame, config=config)
        
        self.powerimport = GUIImportGraph(frame, self.powerimport_handler, 
                                          config)
        
        self.buttonframe = frame
        
    def init_gui_vars(self):
        root = self.root
        self.loop = GUIGTUDPLoop(root, config, loop_func=self.loop_func)
        
        self.gears = GUIGears(root, config)
        self.revlimit = GUIRevlimit(root, defaultvalue=-1)
        
        self.tone_offset = GUIToneOffset(root, config)
        
        self.rpm = GUIRPM(root, hysteresis_percent=self.hysteresis_percent)
        self.volume = GUIVolume(root, config)
        self.peakpower = GUIPeakPower(root)
        self.revbardata = GUIRevbarData(root)
        self.car_ordinal = GUICarOrdinal(root)
        
        self.curve = GUIEngineCurve(root, self.buttongraph_handler, 
                                          config)
        
        self.buttonreset = tkinter.Button(root, text='Reset', borderwidth=3, 
                                          font= tkinter.font.Font(size= 8),
                                          command=self.reset)
        self.init_gui_buttonframe()

    def init_gui_grid_buttonframe(self):
        super().init_gui_grid_buttonframe()
        self.powerimport.grid(row=0, column=2)
        
    def init_gui_grid(self):
        super().init_gui_grid()
        
        row = GUIGears.ROW_COUNT #start from row below gear display
        self.revbardata.grid(  row=row,   column=3)

    #called by self.importgraph once user presses the button to import data
    def powerimport_handler(self, rpm, power, ratios):
        # gtdp = None
        class FakePacket():
            def __init__(self_):
                self_.car_ordinal = self.car_ordinal.get()
                self_.gears = ratios
        gtdp = FakePacket()
        
        #dictionary approach because it depends on kwargs to interpret data
        self.handle_curve_change(gtdp, rpm=rpm, power=power)
        
    def loop_update_revbar(self, gtdp):
        self.revbardata.update(gtdp.upshift_rpm)

    def reset(self):
        super().reset()
        self.revbardata.reset()

    #write all GUI configurable settings to the config file
    def config_writeback(self, varlist=WRITEBACK_VARS):        
        #hack to get ip from loop
        #self.target_ip = Variable(self.loop.get_target_ip())
        
        super().config_writeback(varlist)

def main():
    global gtbeep #for debugging
    gtbeep = GUIShiftBeep()

if __name__ == "__main__":
    main()