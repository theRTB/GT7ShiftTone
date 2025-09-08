# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 20:54:19 2023

@author: RTB
"""

from mttkinter import mtTkinter as tkinter

from forzagui.configvar import ( GUIRevlimitOffset, GUIRevlimitPercent,
                                 GUIHysteresisPercent, GUICheckButton, 
                                 GUIIncludeReplay, GUIDynamicToneOffsetToggle,
                                 GUIToneOffset, GUIRevlimit, GUIPeakPower, 
                                 GUIVolume, GUIConfigButton,
                                 GUIConfigWindow, GUIBluetoothKeepaliveToggle)

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
        self.label.grid(column=column, columnspan=1, sticky=tkinter.E, 
                                                               *args, **kwargs)
        self.entry.grid(column=column+1, columnspan=2, *args, **kwargs)
        self.unit.grid(column=column+3, columnspan=1, sticky=tkinter.W, 
                                                               *args, **kwargs)
    
    def set(self, value):
        self.tkvar.set(value)
        
    def reset(self):
        self.tkvar.set(self.defaultguivalue)
        self.grabbed_data = False
        
    def update(self, value):
        if not self.grabbed_data:
            self.set(f'{value*self.LOWER:5.0f} - {value*self.UPPER:5.0f}')
            self.grabbed_data = True

class GUIVMaxData():
    def __init__(self, root, defaultguivalue='N/A'):
        self.defaultguivalue = defaultguivalue
        
        self.tkvar = tkinter.StringVar(value=defaultguivalue)    
        
        self.label = tkinter.Label(root, text="'vmax'")        
        self.entry = tkinter.Entry(root, width=6, textvariable=self.tkvar,
                                   justify=tkinter.RIGHT, state='readonly')
        # self.unit = tkinter.Label(root, text='kph/mph')
        
        self.grabbed_data = False
    
    #sticky and columnspan are not forwarded to the grid function
    def grid(self, column, sticky='', columnspan=1, *args, **kwargs):
        self.label.grid(column=column, columnspan=1, sticky=tkinter.E, 
                                                               *args, **kwargs)
        self.entry.grid(column=column+1, columnspan=2, sticky=tkinter.W, 
                        *args, **kwargs)
        # self.unit.grid(column=column+3, columnspan=1, sticky=tkinter.W, 
        #                                                        *args, **kwargs)
    
    def set(self, value):
        self.tkvar.set(value)
        
    def reset(self):
        self.tkvar.set(self.defaultguivalue)
        self.grabbed_data = False
        
    def update(self, gtdp):
        value = gtdp.est_top_speed
        if not self.grabbed_data:
            # self.set(f'{value*self.LOWER:5.0f} - {value*self.UPPER:5.0f}')
            self.set(f'{value}')
            self.grabbed_data = True

class GUIRevlimitOffset(GUIRevlimitOffset):
    pass
        
class GUIRevlimitPercent(GUIRevlimitPercent):
    pass
    
class GUIHysteresisPercent(GUIHysteresisPercent):
    pass

class GUICheckButton(GUICheckButton):
    pass

class GUIIncludeReplay(GUIIncludeReplay):
    pass

class GUIDynamicToneOffsetToggle(GUIDynamicToneOffsetToggle):
    pass

class GUIBluetoothKeepaliveToggle(GUIBluetoothKeepaliveToggle):
    pass

class GUIToneOffset(GUIToneOffset):
    pass

class GUIRevlimit(GUIRevlimit):
    pass

class GUIPeakPower(GUIPeakPower):
    pass

#this class depends on how the volume steps in config are defined
class GUIVolume(GUIVolume):
    pass

class GUIConfigWindow(GUIConfigWindow):
    pass

class GUIStockCurveToggle(GUICheckButton):
    TEXT = 'Car is stock'

class GUIBoPCurveToggle(GUICheckButton):
    TEXT = 'Load group curves'

class GUIConfigWindow(GUIConfigWindow):
    TITLE='GT7ShiftTone: Settings'
    CLASSES = { 'hysteresis_percent': GUIHysteresisPercent,
                'revlimit_percent':   GUIRevlimitPercent,
                'revlimit_offset':    GUIRevlimitOffset,
                'dynamictoneoffset':  GUIDynamicToneOffsetToggle,
                'includereplay':      GUIIncludeReplay,
                'stock_curve_toggle': GUIStockCurveToggle,
                'bluetooth_keepalive': GUIBluetoothKeepaliveToggle,
               }

#enable button once we have a settings window
#adjustables is an array of Variables we can display to adjust
class GUIConfigButton(GUIConfigButton):
    def __init__(self, root, config, adjustables):
        self.button = tkinter.Button(root, text='Settings', command=self.open,
                                     borderwidth=3)

        self.configwindow = GUIConfigWindow(root, config, adjustables)

    @classmethod
    def get_names(cls):
        return GUIConfigWindow.get_names()