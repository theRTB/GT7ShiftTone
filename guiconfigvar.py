# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 20:54:19 2023

@author: RTB
"""

import statistics
import numpy as np
from collections import deque
from mttkinter import mtTkinter as tkinter

from utility import (packets_to_ms, ms_to_packets, round_to,
                     factor_to_percent, percent_to_factor, Variable)

#maintain a rolling array of the time between beep and actual shift
#caps to the lower and upper limits of the tone_offset variable to avoid
#outliers such as 0 ms reaction time or a delay of seconds or more
#depends on ForzaBeep loop_test_for_shiftrpm and loop_beep
class DynamicToneOffset():
    DEQUE_MIN, DEQUE_MAX = 35, 75

    def __init__(self, tone_offset_var, config, *args, **kwargs):
        self.default_toneoffset = config.tone_offset
        self.offset_lower = config.tone_offset_lower
        self.offset_upper = config.tone_offset_upper
        self.offset_outlier = config.tone_offset_outlier
        
        self.counter = None
        self.offset = self.default_toneoffset
        self.deque = deque([self.default_toneoffset]*self.DEQUE_MIN,
                           maxlen=self.DEQUE_MAX)
        self.deque_min_counter = 0
        self.tone_offset_var = tone_offset_var

    def start_counter(self):
        #assert self.counter is None
        self.counter = 0

    def increment_counter(self):
        if self.counter is not None:
            self.counter += 1

    def decrement_counter(self):
        if self.counter is not None:
            self.counter -= 1

    def finish_counter(self):
        if self.counter is None:
            return
        
        if self.counter < 0:
            print(f'DynamicToneOffset: erronous {packets_to_ms(self.counter)} ms, discarded')
            self.reset_counter()
            return
            
        if self.counter > self.offset_outlier:
            print(f'DynamicToneOffset: outlier {packets_to_ms(self.counter)} ms, discarded')
            self.reset_counter()
            return

        if self.deque_min_counter <= self.DEQUE_MIN:
            self.deque.popleft()
        else:
            self.deque_min_counter += 1

        value = min(self.offset_upper, self.counter)
        value = max(self.offset_lower, value)

        self.deque.append(value)
        average = statistics.mean(self.deque)
        print(f'DynamicToneOffset: offset {self.offset:.1f} new average {average:.2f}')
        average = round(average, 1)
        if average != self.offset:
            self.offset = average
            self.apply_offset()
        self.reset_counter()

    def apply_offset(self):
        self.tone_offset_var.set(self.offset)

    def get_counter(self):
        return self.counter

    def reset_counter(self):
        self.counter = None

    def reset_to_current_value(self):
        self.offset = self.tone_offset_var.get()
        self.deque.clear()
        self.deque_min_counter = 0
        self.deque.extend([self.offset]*self.DEQUE_MIN)

class GUIConfigVariable(Variable):
    def __init__(self, root, name, value, unit, values, convert_from_gui,
                 convert_to_gui, *args, **kwargs):
        super().__init__(value, *args, **kwargs)
        gui_value = convert_to_gui(value)
        values_gui = list(map(convert_to_gui, values))
        self.convert_from_gui = convert_from_gui
        self.convert_to_gui = convert_to_gui

        self.label = tkinter.Label(root, text=name)
        self.unit = tkinter.Label(root, text=unit)

        self.tkvar = tkinter.IntVar()
        self.spinbox = tkinter.Spinbox(root, state='readonly', width=5,
                                       justify=tkinter.RIGHT,
                                       textvariable=self.tkvar,
                                       readonlybackground='#FFFFFF',
                                       disabledbackground='#FFFFFF',
                                       values=values_gui, command=self.update)
        self.tkvar.set(gui_value) #force spinbox to initial value

    def grid(self, row, column=0, *args, **kwargs):
        self.label.grid(  row=row, column=column,   sticky=tkinter.E)
        self.spinbox.grid(row=row, column=column+1)
        self.unit.grid(   row=row, column=column+2, sticky=tkinter.W)

    def config(self, *args, **kwargs):
        self.spinbox.config(*args, **kwargs)

    def gui_get(self):
        return self.spinbox.get()

    def gui_set(self, val):
        self.tkvar.set(val)

    def set(self, val):
        super().set(val)
        val_gui = self.convert_to_gui(val)
        self.gui_set(val_gui)

    def update(self):
        val_gui = self.gui_get()
        val_internal = self.convert_from_gui(val_gui)
        super().set(val_internal)

class GUIToneOffset(GUIConfigVariable, DynamicToneOffset):
    NAME = 'Tone offset'
    UNIT = 'ms'

    def __init__(self, root, config):
        LOWER, UPPER = config.tone_offset_lower, config.tone_offset_upper
        DEFAULTVALUE = config.tone_offset
        
        GUIConfigVariable.__init__(self, root=root, name=self.NAME, 
                         convert_from_gui=ms_to_packets, unit=self.UNIT,
                         convert_to_gui=packets_to_ms, value=DEFAULTVALUE,
                         values=range(LOWER, UPPER+1))
        DynamicToneOffset.__init__(self, tone_offset_var=self, config=config)

    def update(self):
        super().update()
        self.reset_to_current_value()
        print(f"DynamicToneOffset reset to {self.value}")

class GUIRevlimitOffset(GUIConfigVariable):
    NAME = 'Revlimit'
    UNIT = 'ms'

    def __init__(self, root, config):
        DEFAULTVALUE = config.revlimit_offset
        LOWER = config.revlimit_offset_lower
        UPPER = config.revlimit_offset_upper
        super().__init__(root=root, name=self.NAME, unit=self.UNIT,
                         convert_from_gui=ms_to_packets,
                         convert_to_gui=packets_to_ms, value=DEFAULTVALUE,
                         values=range(LOWER, UPPER+1))

class GUIRevlimitPercent(GUIConfigVariable):
    NAME = 'Revlimit'
    UNIT = '%'

    def __init__(self, root, config):
        DEFAULTVALUE = config.revlimit_percent
        LOWER = config.revlimit_percent_lower
        UPPER = config.revlimit_percent_upper
        super().__init__(root=root, name=self.NAME, unit=self.UNIT,
                         convert_from_gui=percent_to_factor,
                         convert_to_gui=factor_to_percent,
                         values=np.arange(LOWER, UPPER, 0.001),
                         value=DEFAULTVALUE)

class GUIHysteresisPercent(GUIConfigVariable):
    NAME = 'Hysteresis'
    UNIT = '%'

    def __init__(self, root, config):
        DEFAULTVALUE = config.hysteresis_percent
        LOWER = config.hysteresis_percent_lower
        UPPER = config.hysteresis_percent_upper
        super().__init__(root=root, name=self.NAME, unit=self.UNIT,
                         convert_from_gui=percent_to_factor,
                         convert_to_gui=factor_to_percent,
                         values=np.arange(LOWER, UPPER, 0.001),
                         value=DEFAULTVALUE)
    
    def as_rpm(self, fdp):
        return self.get() * fdp.engine_max_rpm

class GUIRevlimit(Variable):
    BG = {'initial':'#F0F0F0', #the possible background colors of the entry
          'guess':  '#FFFFFF', #'guess' is currently not used
          'curve':  '#CCDDCC'}
    def __init__(self, root, defaultguivalue='N/A', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaultguivalue = defaultguivalue
        self.tkvar = tkinter.StringVar(value=defaultguivalue)
        
        self.label = tkinter.Label(root, text='Revlimit')        
        self.entry = tkinter.Entry(root, width=6, textvariable=self.tkvar,
                                   justify=tkinter.RIGHT, state='readonly')
        self.unit = tkinter.Label(root, text='RPM')
    
    def grid(self, column, sticky='', *args, **kwargs):
        self.label.grid(column=column, sticky=tkinter.E, *args, **kwargs)
        self.entry.grid(column=column+1, sticky=sticky, *args, **kwargs)
        self.unit.grid(column=column+2, sticky=tkinter.W, *args, **kwargs)
        
    def set_bg(self, state):
        self.entry.configure(readonlybackground=self.BG.get(state))

    def set(self, value, bg_state='curve'):
        super().set(value)
        self.tkvar.set(int(value))
        self.set_bg(state=bg_state)
        
    def reset(self):
        super().reset()
        self.tkvar.set(self.defaultguivalue)
        self.set_bg(state='initial')

class GUITach():
    def __init__(self, root, defaultguivalue=0):
        self.defaultguivalue = defaultguivalue
        
        self.tkvar = tkinter.IntVar(value=defaultguivalue)    
        
        self.label = tkinter.Label(root, text='Tach')        
        self.entry = tkinter.Entry(root, width=6, textvariable=self.tkvar,
                                   justify=tkinter.RIGHT, state='readonly')
        self.unit = tkinter.Label(root, text='RPM')
        
        self.update_tach = True
    
    #sticky is not forwarded to the grid function
    def grid(self, column, sticky='', *args, **kwargs):
        self.label.grid(column=column, sticky=tkinter.E, *args, **kwargs)
        self.entry.grid(column=column+1, *args, **kwargs)
        self.unit.grid(column=column+2, sticky=tkinter.W, *args, **kwargs)
    
    def set(self, value):
        self.tkvar.set(round(value))
        
    def reset(self):
        self.tkvar.set(self.defaultguivalue)
        
    def update(self, value):
        if self.update_tach:
            self.set(value)
        self.update_tach = not self.update_tach

class GUIPeakPower():
    def __init__(self, root, defaultguivalue=''):
        self.defaultguivalue = defaultguivalue
        
        self.tkvar = tkinter.StringVar(value=defaultguivalue)
        
        self.label = tkinter.Label(root, text='Power')
        self.entry = tkinter.Entry(root, textvariable=self.tkvar, width=18,
                                   state='readonly')
    
    #sticky and columnspan are not forwarded to the grid function
    def grid(self, column, sticky='', columnspan=1, *args, **kwargs):
        self.label.grid(column=column, columnspan=1, 
                        sticky=tkinter.E, *args, **kwargs)    
        self.entry.grid(column=column+1, columnspan=4,
                        sticky=tkinter.W, *args, **kwargs) 

    def set(self, rpm, peakpower):
        # string = f'~{peakpower/10:>4.0f} kW at ~{round_to(rpm, 50):>5} RPM'
        string = f'peak at ~{round_to(rpm, 50):>5} RPM'
        self.tkvar.set(string)
        
    def reset(self):
        self.tkvar.set(self.defaultguivalue)

#this class depends on how the volume steps in config are defined
class GUIVolume():
    MIN, MAX, STEP = 0, 100, 25
    def __init__(self, root, value):
        frame = tkinter.Frame(root)
        self.frame = frame
        self.label = tkinter.Label(frame, text='Volume')
        
        self.tkvar = tkinter.IntVar(value=value)
        self.scale = tkinter.Scale(frame, orient=tkinter.VERTICAL, showvalue=1,
                                   from_=self.MAX, to=self.MIN, 
                                   resolution=self.STEP, variable=self.tkvar)
        
        self.label.pack()
        self.scale.pack(expand=True, fil=tkinter.X)

    #sticky and columnspan are not forwarded to the grid function
    def grid(self, row, column, *args, **kwargs):
        self.frame.grid(row=row, column=column, *args, **kwargs)

    def get(self):
        return self.tkvar.get()

    def set(self, value):
        if value in range(self.MIN, self.MAX+1, self.STEP):
            self.tkvar.set(value)

class GUIButtonStartStop():
    def __init__(self, root, command):
        self.tkvar = tkinter.StringVar(value='Start')
        self.button = tkinter.Button(root, borderwidth=3, 
                                         textvariable=self.tkvar, 
                                         command=command)

    def toggle(self, toggle):
        self.tkvar.set('Start' if toggle else 'Stop')

    def grid(self, row, column, *args, **kwargs):
        self.button.grid(row=row, column=column, *args, **kwargs)
    
    def pack(self, *args, **kwargs):
        self.button.pack(*args, **kwargs)
    
    def invoke(self):
        self.button.invoke()

class GUIButtonVarEdit():
    def __init__(self, root, command):
        self.tkvar = tkinter.IntVar(value=1)
        self.button = tkinter.Checkbutton(root, text='Edit', command=command,
                                          variable=self.tkvar)

    def grid(self, row, column, *args, **kwargs):
        self.button.grid(row=row, column=column, *args, **kwargs)

    def get(self):
        return self.tkvar.get()
    
    def invoke(self):
        self.button.invoke()

class GUIButtonDynamicToggle():
    def __init__(self, root, config):
        self.tkvar = tkinter.IntVar(value=config.dynamictoneoffset)
        self.button = tkinter.Checkbutton(root, text='Dynamic tone offset', 
                                          variable=self.tkvar)

    def grid(self, row, column, *args, **kwargs):
        self.button.grid(row=row, column=column, *args, **kwargs)

    def get(self):
        return self.tkvar.get()

#The in-game revbar scales off the revbar variable in telemetry:
    #Starts at 85% and starts blinking at 99%
class GUIRevbarData():
    LOWER, UPPER = 0.85, 0.99
    def __init__(self, root, defaultguivalue='N/A - N/A'):
        self.defaultguivalue = defaultguivalue
        
        self.tkvar = tkinter.StringVar(value=defaultguivalue)    
        
        self.label = tkinter.Label(root, text='Revbar')        
        self.entry = tkinter.Entry(root, width=12, textvariable=self.tkvar,
                                   justify=tkinter.RIGHT, state='readonly')
        self.unit = tkinter.Label(root, text='RPM')
        
        self.grabbed_data = False
    
    #sticky and columnspan are not forwarded to the grid function
    def grid(self, column, sticky='', columnspan=1, *args, **kwargs):
        self.label.grid(column=column, columnspan=1, sticky=tkinter.E, *args, **kwargs)
        self.entry.grid(column=column+1, columnspan=2, *args, **kwargs)
        self.unit.grid(column=column+3, columnspan=1, sticky=tkinter.W, *args, **kwargs)
    
    def set(self, value):
        self.tkvar.set(value)
        
    def reset(self):
        self.tkvar.set(self.defaultguivalue)
        self.grabbed_data = False
        
    def update(self, value):
        if not self.grabbed_data:
            self.set(f'{value*self.LOWER:5.0f} - {value*self.UPPER:5.0f}')
            self.grabbed_data = True

#TODO: update this class to use ipaddress library
class GUITargetIP():
    def __init__(self, root, defaultguivalue=''):
        self.defaultguivalue = defaultguivalue
        
        self.tkvar = tkinter.StringVar(value=defaultguivalue)    
        
        self.label = tkinter.Label(root, text='PS IP')        
        self.entry = tkinter.Entry(root, width=13, textvariable=self.tkvar,
                                   justify=tkinter.RIGHT)
        
        self.hide_ip = False
        self.label.bind('<Double-Button-1>', self.hide_ip_handler)
    
    #sticky and columnspan are not forwarded to the grid function
    def grid(self, column, sticky='', columnspan=1, *args, **kwargs):
        self.label.grid(column=column, sticky=tkinter.E, *args, **kwargs)
        self.entry.grid(column=column+1, sticky=tkinter.W, columnspan=2, 
                                                                *args,**kwargs)

    def toggle(self, toggle):
        state = tkinter.NORMAL if toggle else 'readonly'
        self.entry.config(state=state)

    def get(self):
        return self.tkvar.get()

    def hide_ip_handler(self, event=None):
        fg = '#000000' if self.hide_ip else '#F0F0F0'
        self.entry.config(fg=fg)
        self.hide_ip = not self.hide_ip
        
    def reset(self):
        self.tkvar.set(self.defaultguivalue)

class GUIStatus():
    def __init__(self, root, value):
        self.tkvar = tkinter.StringVar(value=value)            
        self.label = tkinter.Label(root, textvariable=self.tkvar, 
                                   relief=tkinter.GROOVE, width=12)    

    def grid(self, row, column, *args, **kwargs):
        self.label.grid(row=row, column=column, *args, **kwargs)
    
    def set(self, value):
        self.tkvar.set(value)

from gtudploop import GTUDPLoop
class GUIGTUDPLoop(GTUDPLoop):
    def __init__(self, root, config, loop_func=None):
        super().__init__(config.target_ip, loop_func=loop_func)
        self.state = 'Stopped'
        
        self.init_tkinter(root, config)        

    def init_tkinter(self, root, config):
        self.frame = tkinter.LabelFrame(root, text='Connection')
        
        self.buttonstartstop = GUIButtonStartStop(self.frame, 
                                                  self.startstop_handler)
        self.gui_ip = GUITargetIP(self.frame, config.target_ip)
        self.status = GUIStatus(self.frame, self.state)
        
        self.gui_ip.grid(         row=0, column=0)
        self.buttonstartstop.grid(row=1, column=0)
        self.status.grid(         row=1, column=1, columnspan=2)
    
    def grid(self, row, column, *args, **kwargs):
        self.frame.grid(row=row, column=column, *args, **kwargs)

    #convenience function
    def firststart(self):
        self.startstop_handler() #implied start, not explicit start

    def startstop_handler(self, event=None):
        if self.gui_ip.get() != '':
            self.buttonstartstop.toggle(self.is_running()) #toggle text
            self.gui_ip.toggle(self.is_running()) #toggle read-only
            self.set_target_ip(self.gui_ip.get()) #set loop IP before start
            self.toggle(True)
    
    def update_status(self, value):
        self.state = value
        self.status.set(self.state)
    
    #same logic as in GTUDPLoop toggle. We seem to be running into a race 
    #condition where self.isRunning is not updated yet to test for status
    #update after calling the base function in GTUDPLoop
    def toggle(self, toggle=None):
        if toggle and not self.isRunning:
            self.update_status('Started')
        else:
            self.update_status('Stopped')
    
        super().toggle(toggle)
        
    def send_heartbeat(self):
        if self.state in ['Started', 'Timeout']:
            self.update_status('Waiting')
            
        super().send_heartbeat()
        
    def nextGTdp(self):
        value = super().nextGTdp()
        
        if value is None and self.state in ['Waiting', 'Receiving']:
            self.update_status('Timeout')
        if value is not None and self.state in ['Waiting', 'Timeout']:
            self.update_status('Receiving')
        
        return value