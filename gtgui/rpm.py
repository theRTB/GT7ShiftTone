# -*- coding: utf-8 -*-
"""
Created on Fri Aug  2 21:01:24 2024

@author: RTB
"""

#replaced tkinter with supposed thread safe tkinter variant
#instead of freezing when the main thread isn't under control of tkinter,
#it now crashes instead. Theoretically, an improvement.
# from mttkinter import mtTkinter as tkinter
#import tkinter
# import tkinter.ttk

from gtbase.rpm import RPM
from forzagui.rpm import GenericGUIRPM

class GUIRPM(GenericGUIRPM, RPM):
    def __init__(self, root, hysteresis_percent):
        super().__init__(root, hysteresis_percent)