# -*- coding: utf-8 -*-
"""
Created on Sun May  7 19:35:24 2023

@author: RTB
"""

#TODO:
    # update car but not beep during menu?
        #If car is changed in the middle of the menu telemetry is not updated
        #Telemetry only updates if at race
    # check if maximum speed is in telemetry and use that?
        # added vmax, but vmax does not include hybrid or DRS
    # check accuracy of the upshift speed (add column in shift history?)
    # wheel size is in telemetry
    # make bug report for gt7 car list
    # fix hysteresis -> code runs on a fixed packet buffer now but only updates
    # rpm if it is above hysteresis. This isn't correct

    # hide 0.00 rel ratio on final gear: add finalgear option somehow
    # rework row display on shift history: it visibly rotates due to slowness
    # move to labels instead
    
    # Grey out gear 9 and 10: non-functional for GT7
    
    #Settings:
        #Toggle import graph button
        #Toggle speed stats button and update speed
        #Move Tone Offset to settings to hide it?
    # Maybe phase out Settings window to extend main window to the right?
    # Grid variables into those
    
    # Brief shift history of the last 5 shifts or so in main window?
        
    #Copy button: open Textbox with various stats pasted for copy and paste
    #get final drive from telemetry?
    
    # Test if window scalar config variable works as expected
    # Test if changing dpi works as expected
    
    #split config.py into base and gui variants
    
    #Check nonlinearity of RPM with an RPM over time graph
    
    #Add logger for enhanced logging (debug, error, warning, etc)
    
from gtbase.shiftbeep import ShiftBeep
from gtgui.shiftbeep import GUIShiftBeep
# from forzabase.shiftbeep import ShiftBeep
# from forzagui.shiftbeep import GUIShiftBeep

def main():
    global gtbeep #for debugging
    gtbeep = GUIShiftBeep()
    # gtbeep = ShiftBeep()

if __name__ == "__main__":
    main()