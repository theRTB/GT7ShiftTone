# -*- coding: utf-8 -*-
"""
Created on Sun May  7 19:35:24 2023

@author: RTB
"""

# from gtbase.shiftbeep import ShiftBeep
from gtgui.shiftbeep import GUIShiftBeep
# from forzabase.shiftbeep import ShiftBeep
# from forzagui.shiftbeep import GUIShiftBeep

def main():
    global gtbeep #for debugging
    gtbeep = GUIShiftBeep()
    # gtbeep = ShiftBeep()

if __name__ == "__main__":
    main()