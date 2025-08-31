# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 21:56:24 2024

@author: RTB
"""

from mttkinter import mtTkinter as tkinter

from gtbase.speedstats import SpeedTest, SpeedStats

class GUISpeedTest(SpeedTest):
    varnames = ['start', 'end', 'min_distance', 'start_rpm', 'end_rpm', 
                'time', 'distance', 'fuel']
    def __init__(self, start, end, min_distance=0, start_rpm=0, end_rpm=0, 
                 *args, **kwargs):
        super().__init__(start, end, min_distance, start_rpm, end_rpm, 
                         *args, **kwargs)
        self.start = tkinter.IntVar(value=start)
        self.end = tkinter.IntVar(value=end)        
        self.min_distance = tkinter.IntVar(value=min_distance)
        
        self.start_rpm = tkinter.IntVar(value=start_rpm)
        self.end_rpm = tkinter.IntVar(value=end_rpm)
        
        self.time = tkinter.DoubleVar(value=0)
        self.distance = tkinter.DoubleVar(value=0)
        self.fuel = tkinter.DoubleVar(value=0)
        
    def reset(self):
        super().reset()
        
    # def update(self, gtdp):
    #     return super().update(gtdp)

class SpeedWindow():
    TITLE = "GT7ShiftTone: Speed statistics"

    def __init__(self, root, config):
        self.root = root
        # self.external_handler = handler
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
    
    def init_content(self, tests):
        columns = ['Start speed (kph)', 'End speed (kph)', 
                   'Minimum distance (m)', 'Start RPM', 'End RPM',
                   'Time (s)', 'Distance\nTraveled (m)', 'Fuel used (%)']
        for column, label in enumerate(columns):
            tkinter.Label(self.window, text=label).grid(row=0, column=column)
        
        for row, test in enumerate(tests, start=1):
            for column, name in enumerate(GUISpeedTest.varnames):
                tkinterfunc = tkinter.Entry
                if name in ['time', 'distance', 'fuel']:
                    tkinterfunc = tkinter.Label
                tkinterfunc(self.window, textvariable=getattr(test, name),
                         width=8, justify='right').grid(row=row, column=column)

    def create(self, tests):
        if self.window is not None: #force existing window to front
            self.window.deiconify()
            self.window.lift()
            return
        self.init_window()
        self.init_content(tests)

    def close(self):
        self.window.destroy()
        self.window = None

class GUISpeedStats(SpeedStats):
    def __init__(self, root, config):
        super().__init__(config)
        
        self.tests = [GUISpeedTest(*entry, do_print=self.do_print) 
                                                      for entry in self.BASE]
        
        #apply trickery to have a single start and end speed for all tests
        for test in self.tests[1:]:
            test.start = self.tests[0].start
            test.end = self.tests[0].end
        
        self.button = tkinter.Button(root, text='Speed\nStats', 
                                     borderwidth=3,
                                     command=self.create_window)
        self.importwindow = SpeedWindow(root, config)

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

    def create_window(self, event=None):
        self.importwindow.create(self.tests)