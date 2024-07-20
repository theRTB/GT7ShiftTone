# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 19:59:17 2024

@author: RTB
"""

from collections import deque

from utility import packets_to_ms

class History():
    COLUMNS = ['target', 'shiftrpm', 'gear', 'beep_distance']
    def __init__(self, config):
        self.log_basic_shiftdata = config.log_basic_shiftdata
        self.history = []
    
    def get_shiftpoint(self, target, shiftrpm, gear, beep_distance):
        data = ['N/A' if target == -1 else int(target),
              shiftrpm,
              gear,
              'N/A' if beep_distance is None else packets_to_ms(beep_distance)]
                    
        return dict(zip(self.COLUMNS, data))
    
    def add_shiftdata(self, point):
        self.history.append(point)
    
    def debug_log_basic_shiftdata(self, target, shiftrpm, gear, 
                                  beep_distance):
        # target = self.debug_target_rpm
        difference = 'N/A' if target == -1 else f'{shiftrpm - target:4.0f}'
        beep_distance_ms = 'N/A'
        if beep_distance is not None:
            beep_distance_ms = packets_to_ms(beep_distance)
        print(f"gear {gear-1}-{gear}: {shiftrpm:.0f} actual shiftrpm, {target:.0f} target, {difference} difference, {beep_distance_ms} ms distance to beep")
        print("-"*50)
    
    def update(self, target, shiftrpm, gear, beep_distance):
        point = self.get_shiftpoint(target, shiftrpm, gear, beep_distance)
        self.add_shiftdata(point)
        if self.log_basic_shiftdata:
            self.debug_log_basic_shiftdata(target, shiftrpm, gear, 
                                           beep_distance)

    def reset(self):
        self.history.clear()
    
    #display statistics on difference between target and actual
    #distance between expected and actual distance between beep and shift
    def statistics(self):
        pass
    
#replaced tkinter with supposed thread safe tkinter variant
#instead of freezing when the main thread isn't under control of tkinter,
#it now crashes instead. Theoretically, an improvement.
from mttkinter import mtTkinter as tkinter
#import tkinter
import tkinter.ttk

#tell Windows we are DPI aware
import ctypes
PROCESS_SYSTEM_DPI_AWARE = 1
PROCESS_PER_MONITOR_DPI_AWARE = 2
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_SYSTEM_DPI_AWARE)

#Setting maxlen>10 requires a manual window height adjustment
class GUIHistory (History):
    TITLE = "GTShiftTone: Shift history"
    COLUMNNAMES = ['Target', 'Shift RPM', 'Gear', 'Time']
    def __init__(self, root, config, maxlen=10):
        super().__init__(config)
        self.rows = deque(maxlen=maxlen)
        self.maxlen = maxlen
        self.init_tkinter(root, config)
        self.root = root
        self.window = None
        self.tree = None

    def init_tkinter(self, root, config):
        self.button = tkinter.Button(root, text='Shift\nHistory', 
                                     command=self.create_window, borderwidth=3)

    #pass through grid arguments to button
    def grid(self, *args, **kwargs):
        self.button.grid(*args, **kwargs)

    #From: https://stackoverflow.com/questions/33231484/python-tkinter-how-do-i-get-the-window-size-including-borders-on-windows
    #Get x and y coordinates to place graph underneath the main window.
    #This may not scale arbitrarily with varying border sizes and title sizes
    def get_windowoffsets(self):
        return (self.root.winfo_x() + self.root.winfo_width(),  
                self.root.winfo_y())

    def create_table(self):
        HEADER_SIZE, ROW_SIZE = 15, 13
        
        style = tkinter.ttk.Style()
        style.configure("Treeview.Heading", font=(None, HEADER_SIZE),
                        rowheight=int(HEADER_SIZE*2.5))
        style.configure("Treeview", font=(None, ROW_SIZE),
                        rowheight=int(ROW_SIZE*2.5))
            
        columns = dict(zip(self.COLUMNS, self.COLUMNNAMES))
        
        tree = tkinter.ttk.Treeview(self.window, show='headings',
                                    columns=self.COLUMNS, selectmode='none')        
        
        tree.tag_configure('f', background='#FFFFFF')
        tree.tag_configure('0', background='#F0F0F0')
        tree.tag_configure('1', background='#BBBBBB')
        
        for name, value in zip(self.COLUMNS, self.COLUMNNAMES):
            tree.heading(name, text=value)
            tree.column(name, width=150, anchor='center')
        
        blank = ['']*len(columns)
        for x in range(self.maxlen):
            row = tree.insert('', tkinter.END, values=blank, 
                              tags=(f'{x%2}' if x !=0 else 'f'))
            self.rows.append(row)
        
        tree.pack(expand=True, fill=tkinter.BOTH)
        self.tree = tree

    #Get up to the last (maxlen) shifts and re-add them to the GUI
    def restore_history(self):
        length = min(len(self.history), self.maxlen)
        for item in self.history[-length:]:
            self.gui_add_shiftdata(item)

    def gui_add_shiftdata(self, point):
        if self.window is None:
            return
        
        self.rows.rotate()
        
        #swap tag for alternating rows as we move the bottom row to above top
        for i, x in enumerate(self.rows):
            self.tree.item(x, tags=(f'{i%2}'))
        
        self.tree.item(self.rows[0], values=list(point.values()), tags=('f'))
        self.tree.move(self.rows[0], '', 0)

    def add_shiftdata(self, point):
        super().add_shiftdata(point)
        
        self.gui_add_shiftdata(point)
        
    def create_window(self):
        if self.window is not None:
            return
        self.window = tkinter.Toplevel(self.root)
        self.window.title(self.TITLE)
        self.window.protocol('WM_DELETE_WINDOW', self.close)

        #place window to the right of main window
        x, y = self.get_windowoffsets()
        self.window.geometry(f"+{x}+{y}")
        
        self.create_table()
        self.restore_history()
    
    def reset(self):
        super().reset()
        
        blank = dict(zip(self.COLUMNNAMES, ['']*len(self.COLUMNNAMES)))
        for _ in range(self.maxlen):
            self.gui_add_shiftdata(blank)
    
    def close(self):
        self.window.destroy()
        self.window = None