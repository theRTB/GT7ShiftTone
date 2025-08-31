# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 19:59:17 2024

@author: RTB
"""

#replaced tkinter with supposed thread safe tkinter variant
#instead of freezing when the main thread isn't under control of tkinter,
#it now crashes instead. Theoretically, an improvement.
# from mttkinter import mtTkinter as tkinter
#import tkinter
# import tkinter.ttk

from gtbase.history import History
from forzagui.history import GenericGUIHistory

class GUIHistory(GenericGUIHistory, History):
    def __init__(self, root, config, maxlen=10):
        super().__init__(root, config, maxlen)