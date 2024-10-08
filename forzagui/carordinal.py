# -*- coding: utf-8 -*-
"""
Created on Sun Jul 21 13:53:13 2024

@author: RTB
"""
from mttkinter import mtTkinter as tkinter

from forzabase.carordinal import CarOrdinal

class GenericGUICarOrdinal():
    def __init__(self, root, defaultguivalue='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaultguivalue = defaultguivalue
        
        self.tkvar = tkinter.StringVar(value=defaultguivalue)
        
        self.label = tkinter.Label(root, text='Car ID')
        self.entry = tkinter.Entry(root, textvariable=self.tkvar, width=6,
                                   state='readonly', justify=tkinter.RIGHT)
    
    #sticky and columnspan are not forwarded to the grid function
    def grid(self, column, sticky='', columnspan=1, *args, **kwargs):
        self.label.grid(column=column, columnspan=1, 
                        sticky=tkinter.E, *args, **kwargs)    
        self.entry.grid(column=column+1, columnspan=1,
                        sticky=tkinter.W, *args, **kwargs) 

    def gui_get(self):
        return self.tkvar.get()

    def set(self, value):
        super().set(value)
        gui_value = value #CarData.get_name(value)
        self.tkvar.set(gui_value)
        
    def reset(self):
        super().reset()
        self.tkvar.set(self.defaultguivalue) 

class GUICarOrdinal(GenericGUICarOrdinal, CarOrdinal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        