# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 10:48:30 2024

@author: RTB
"""

import numpy as np

from mttkinter import mtTkinter as tkinter
import tkinter.ttk #for tkinter.font? TODO: does this even make mttkinter work

EXPLANATION = '''Open WebPlotDigitizer-4.7-win32-x64/WebPlotDigitizer-4.7.exe
Load image (crop image to just the graph for ease of selecting points)
2D (X-Y) plot
Align Axes, Proceed
X1 at bottom left (zero point) of axis, RPM should be listed
X2 at bottom right of axis, RPM should be listed
Y1 at bottom left (zero point) of axis, should be 0
Y2 at peak power, number should be listed
Click Complete!

Enter points (keep log scale unticked)
Tick Assume axes are perfectly aligned

Under Automatic Extraction
Click Pen
Trace the power curve such that it is under the overlay drawn
Click the color block to the right of Color Foreground Color
Click Color Picker
Click on a pixel of the power curve line
Click Done

Choose algorithm X step (or play with X step w/ interpolation)
Delta x step should be 100, 125, 250, or 500 
Play with Distance (80?) and Line width (20?)
Click Run

Confirm the data points are accurately overlayed over the image

Click View Data
under Format, Number Formatting
Digits 1, set to Fixed
Click Format

Click Copy to Clipboard
Paste the data in here, overwriting this text

If the first and final point are missing, tick Edge points missing
Press Click to import graph'''

class ImportWindow():
    TITLE = "GT7ShiftTone: Import power curve"

    def __init__(self, root, handler, config):
        self.root = root
        self.external_handler = handler
        self.window = None

    #From: https://stackoverflow.com/questions/33231484/python-tkinter-how-do-i-get-the-window-size-including-borders-on-windows
    #Get x and y coordinates to place graph underneath the main window.
    #This may not scale arbitrarily with varying border sizes and title sizes
    def get_windowoffsets(self):
        root = self.root.winfo_toplevel()
        return (root.winfo_x() + root.winfo_width(),  
                root.winfo_y())
    
    def init_window(self):
        self.window = tkinter.Toplevel(self.root)
        self.window.title(self.TITLE)
        self.window.protocol('WM_DELETE_WINDOW', self.close)

        #place window to the right of main window
        x, y = self.get_windowoffsets()
        self.window.geometry(f"+{x}+{y}")
    
    def init_content(self):
        self.powercurve_text = tkinter.Label(self.window, text='Power curve:')
        
        self.textbox = tkinter.Text(self.window, height=38, width=70)
        self.textbox.insert("end-1c", EXPLANATION)
        
        text = 'Gear Ratios (optional, seperate by comma)'
        self.gearratios_var = tkinter.StringVar(value='')
        self.gearratios_text = tkinter.Label(self.window, text=text)
        self.gearratios = tkinter.Entry(self.window, width=60,
                                        textvariable=self.gearratios_var)
        
        self.buttonimport = tkinter.Button(self.window, borderwidth=3,
                                           text='Click to import Graph', 
                                           command=self.handle_import_data)
        
        self.edgesmissing_var = tkinter.IntVar(value=1)
        self.edgesmissing = tkinter.Checkbutton(
                             self.window, variable=self.edgesmissing_var,
                             text='Edge points missing (x step less than 500)')
        
        self.powercurve_text.pack()
        self.textbox.pack()
        self.edgesmissing.pack()
        self.gearratios_text.pack(fill='x')
        self.gearratios.pack(fill='x')
        self.buttonimport.pack()
        
    def create(self):
        if self.window is not None: #force existing window to front
            self.window.deiconify()
            self.window.lift()
            return
        self.init_window()
        self.init_content()

    #linear extrapolation based on two nearest points
    #assumes data points are rounded to 1 decimal
    def add_edges(self, array):
        minpoint = round(2*array[0] - array[1], 1)
        maxpoint = round(2*array[-1] - array[-2], 1)
        
        return [minpoint] + list(array) + [maxpoint]

    #Once user has pressed the button, clean up the import data by assuming
    #it is correct. This code takes no responsibility for wrong input data
    #ratios is always 11 items, padded with zeros and start with a 0 for gear 0
    def handle_import_data(self):
        data_graph = self.textbox.get("1.0",'end-1c').replace(' ', '')
        data_ratio = self.gearratios.get().replace(' ', '')
        
        #Data manipulation
        try:
            a = data_graph.split(sep='\n')
            b = [i.split(',') for i in a]
            if len(b[-1]) != 2: #in case of extra enter after last row
                b = b[:-1]
            c = [(float(x), float(y)) for x,y in b]
            rpm, power = zip(*c)
            
            if self.edgesmissing_var.get():    
                rpm = self.add_edges(rpm)        
                power = self.add_edges(power) 

            rpm = np.array(rpm)
            power = np.array(power)

            ratios = [0]*11
            if len(data_ratio):
                ratios = [0] + [float(x) for x in data_ratio.split(',')]
                ratios += [0]*(11-len(ratios))
        except BaseException as e:
            print(e)
            return None

        #ship data off to main class
        if self.external_handler is not None:
            self.external_handler(rpm, power, ratios)
            
    def close(self):
        self.window.destroy()
        self.window = None

#Class to open a text window with explanation on how to import power/rpm points
#from a plot digitizer applied to a screenshot/remote play of GT7 car settings
#Import instructions based off https://github.com/automeris-io/WebPlotDigitizer
class GUIImportGraph():
    def __init__(self, root, handler, config):
        self.button = tkinter.Button(root, text='Import', 
                                     borderwidth=3,
                                     font=tkinter.font.Font(size=8),
                                     command=self.create_window)
        self.importwindow = ImportWindow(root, handler, config)

    def reset(self):
        super().reset()

    #enable the button in the GUI
    def enable(self):
        self.button.config(state=tkinter.ACTIVE)

    #disable the button in the GUI
    def disable(self):
        self.button.config(state=tkinter.DISABLED)

    def is_disabled(self):
        return self.button.cget('state') == tkinter.DISABLED

    #pass through grid arguments to button
    def grid(self, *args, **kwargs):
        self.button.grid(*args, **kwargs)

    #is called by graphbutton_handler in gui if there is a curve
    #The window needs a curve with RPM, power, torque, revlimit% and carname
    #awkward call because this object is now the curve itself
    def create_window(self, event=None):
        self.importwindow.create()