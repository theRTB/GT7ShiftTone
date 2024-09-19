# -*- coding: utf-8 -*-
"""
Created on Sat Nov  4 14:50:56 2023

@author: RTB
"""

from mttkinter import mtTkinter as tkinter
#import tkinter
#import tkinter.ttk

#Change default DPI for when saving an image
import matplotlib.pyplot as plt
plt.rcParams['savefig.dpi'] = 100

from gtbase.enginecurve import EngineCurve
from forzagui.enginecurve import PowerGraph, PowerWindow, GenericGUIEngineCurve

#class responsible for creating a tkinter window for the power graph
class PowerWindow(PowerWindow):
    TITLE = "GTShiftTone: Power graph"

    def open_powergraph(self, curve, fig, revlimit_percent):
        PowerGraph(curve, fig, revlimit_percent, self.ROUND_RPM,
                   self.power_percentile, relative_power=True)

#class responsible for handling a tkinter button in the gui to display the
#power graph when it has been collected. The button is disabled until the user
#has collected a curve.
class GUIEngineCurve(GenericGUIEngineCurve, EngineCurve):
    TITLE = "GTShiftTone: Power graph"
    def __init__(self, root, handler, config):
        super().__init__(root, handler, config)
        self.root = root

        self.button = tkinter.Button(root, text='View\nPower\nGraph', 
                                     borderwidth=3,
                                     command=handler, state=tkinter.DISABLED)
        self.powerwindow = PowerWindow(root, config)