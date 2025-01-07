    # -*- coding: utf-8 -*-
"""
Created on Sun Dec 22 14:35:57 2024

@author: RTB
"""
import numpy as np
from mttkinter import mtTkinter as tkinter

from gtbase.datacollector import DataCollector

from utility import np_drag_fit

class GUIDataCollector(DataCollector):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = tkinter.StringVar(value=name)
        self.active = tkinter.IntVar(value=0)
        self.completed = tkinter.StringVar(value='No')

    def enable(self):
        self.active.set(1)
    
    def disable(self):
        self.active.set(0)
    
    def reset(self):
        super().reset()
        self.disable()
        self.completed.set('No')
        
    def update(self, gtdp):
        if self.active.get():
            super().update(gtdp)
        if self.is_run_completed() and self.completed.get() != 'Yes':
            self.completed.set('Yes')
            self.handle_run_completed()

    def handle_run_completed(self, relative=False, *args, **kwargs):
        #get rpm, power, torque from run, in absolute terms for comparison
        rpm, torque, power = np_drag_fit(self.accelrun, self.dragrun, 
                                         relative=relative, *args, **kwargs)
        
        run = self.accelrun
        
        #differentiate fuel with regards to time to get fuel usage per second
        fuel = run.fuel_level
        time = [num/60 for num, _ in enumerate(fuel)] #define time for the run array
        dfuel = np.gradient(fuel, time)
        
        #get rpm from the context of the run
        rpm_run = run.current_engine_rpm
        
        #get power values for the rpm values present in the run
        power_run = np.interp(rpm_run, rpm, power)
        
        #bsfc is defined as rate of fuel divided by power
        bsfc = dfuel / power_run
        
        #save the arrays to object
        self.rpm = rpm
        self.torque = torque
        self.power = power
        
        self.fuel = fuel
        self.dfuel = dfuel
        self.rpm_run = rpm_run
        self.power_run = power_run
        self.bsfc = bsfc

class FuelWindow():
    TITLE = "GT7ShiftTone: FM/Fuel statistics"

    def __init__(self, root, config):
        self.root = root
        # self.active_handler = handler
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
    
    def init_content(self, tests, handler):
        columns = ['Active', 'Name', 'Complete']
        for column, label in enumerate(columns):
            tkinter.Label(self.window, text=label).grid(row=0, column=column)
        
        for row, test in enumerate(tests, start=1):
            active = tkinter.Checkbutton(self.window, variable=test.active, 
                                         onvalue=1, command=handler, 
                                         offvalue=0)
            name = tkinter.Entry(self.window, textvariable=test.name, width=8, 
                                 justify='right')
            completed = tkinter.Label(self.window, textvariable=test.completed)
            
            active.grid(row=row, column=0)
            name.grid(row=row, column=1)
            completed.grid(row=row, column=2)

    def create(self, tests, handler):
        if self.window is not None: #force existing window to front
            self.window.deiconify()
            self.window.lift()
            return
        self.init_window()
        self.init_content(tests, handler)

    def close(self):
        self.window.destroy()
        self.window = None

class GUIFuelStats():
    DEFAULTNAMES = [f'FM{n}' for n in range(1,6+1)]
    def __init__(self, root, config):
        self.tests = [GUIDataCollector(name, config=config) 
                                              for name in self.DEFAULTNAMES]
        
        self.button = tkinter.Button(root, text='Fuel\nStats', borderwidth=3,
                                     command=self.create_window)
        self.importwindow = FuelWindow(root, config)

    def update(self, gtdp):
        for test in self.tests:
            test.update(gtdp)

    def reset(self):
        for test in self.tests:
            test.reset()
        self.tests[0].enable()

    #TODO: if triggered, check which toggle was enabled and disable the rest
    #do nothing on disable
    def active_handler(self, event=None):
        pass

    #pass through grid arguments to button
    def grid(self, *args, **kwargs):
        self.button.grid(*args, **kwargs)

    def create_window(self, event=None):
        self.importwindow.create(self.tests, self.active_handler)