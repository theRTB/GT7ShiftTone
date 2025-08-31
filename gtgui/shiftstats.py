# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 11:09:27 2025

@author: RTB
"""

from mttkinter import mtTkinter as tkinter

import matplotlib.pyplot as plt
plt.rcParams['savefig.dpi'] = 100

from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                                NavigationToolbar2Tk)

from gtbase.shiftstats import ShiftStats
# from gtbase.speedstats import get_distance
from gtgui.speedstats import GUISpeedTest

class GUIShiftTest(GUISpeedTest):
    MAXRUNS = 1
    def __init__(self, name, *args, **kwargs):
        self.name = tkinter.StringVar(value=name)
        super().__init__(*args, **kwargs)

#TODO:
    #add points where the upshift happens

#first is the slower run, second is the faster run
class ShiftStatsGraph():
    def __init__(self, first, second, fig=None, *args, **kwargs):
        self.first = first
        self.second = second

        distance, delta = self.derive_distance_timedelta(first, second)
        delta *= 1000 #from s to ms
        
        self.distance = distance
        self.delta = delta

        if plt_show := (fig is None):
            fig = plt.figure(*args, **kwargs)
            
        ax = fig.subplots(1)
        self.ax = ax
               
        ax.plot(distance, delta, label='beep faster than blinky')
        ax.grid()
        
        ax.set_ylabel('Delta (ms)')
        ax.set_xlabel('Distance (m)')
        
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        ax.set_xlim(0, xmax)
        ax.set_ylim(min(*delta, 0), ymax)
        
        self.plot_rpmnumbers(first, verticalalignment='top', color='C1',
                             horizontalalignment='left')
        self.plot_rpmnumbers(second, verticalalignment='bottom', color='C2',
                             horizontalalignment='right')

        plt.plot(0,0, label='Upshift RPM for blinky')
        plt.plot(0,0, label='Upshift RPM for beep')

        plt.legend()

        if plt_show:
            plt.show()
    
    def plot_rpmnumbers(self, run, *args, **kwargs):
        index = np.array([i for i in range(len(run)-1) 
                              if run[i].gear!=run[i+1].gear])
        for i in index:
            self.ax.scatter(self.distance[i], self.delta[i], s=8, color='green')
            for i_ in range(i, i-40, -1):
                if run[i_].throttle == 255:
                    break
            text = f'{run[i_].current_engine_rpm:.0f}'
            # color = f"C{run[i_].gear-1}"
            self.ax.scatter(self.distance[i_], self.delta[i_], s=8)
            self.ax.annotate(text, (self.distance[i_], self.delta[i_]),                
                  fontsize=12, *args, **kwargs)
            # print(f'we are here index {i}')
            
            for i_ in range(i, i+40):
                if run[i_].throttle == 255:
                    break    
            self.ax.scatter(self.distance[i_], self.delta[i_], s=8)
            # print(f"end point for {i} at {i_}: {self.distance[i_]}, {self.delta[i_]}")
                
    @classmethod
    def derive_distance_timedelta(cls, first, second, mode='trapz'):
        fstcurve = VTACurve(first)
        sndcurve = VTACurve(second)
    
        return get_plotdata(fstcurve, sndcurve, mode=mode)
        
    # #return x,y values where x is distance from the starting point and y is the 
    # #time delta between the two runs at that distance
    # #TODO: if the order of runs is switched, the end is not cut off correctly
    # #figure out where this error occurs and fix
    # @classmethod
    # def derive_distance_timedelta(cls, first, second):
    #     fstdistance = [get_distance(first[0], p) for p in first]
    #     fstcurve = VTACurve(first)
    
    #     snddistance = [get_distance(second[0], p) for p in second]
    #     sndcurve = VTACurve(second)
    
    #     sndinterp = np.interp(snddistance, fstdistance, fstcurve.t)
    
    #     delta = sndinterp[:len(fstcurve.t)] - fstcurve.t[:len(sndinterp)]
    #     return np.array(snddistance[:len(fstdistance)]), delta
    #     # plt.plot(beepdistance, delta)

import math
def get_distance(vtacurve):
    # return math.sqrt( (gtdp1.position_x - gtdp2.position_x)**2 + 
    #                   (gtdp1.position_y - gtdp2.position_y)**2 +
    #                   (gtdp1.position_z - gtdp2.position_z)**2)
    p0 = vtacurve.position_x[0], vtacurve.position_y[0], vtacurve.position_z[0]
    return [math.sqrt( (p0[0] - x)**2 + (p0[1] - y)**2 + (p0[2] - z)**2 ) 
                                         for x,y,z in zip(vtacurve.position_x, 
                                                          vtacurve.position_y, 
                                                          vtacurve.position_z)]

#original and modified are both VTACurves
def get_plotdata(original, modified, mode='trapz'):
    if mode == 'trapz':
        orig_distance = np.array([np.trapz(original.v[:i+1], original.t[:i+1]) 
                                             for i in range(len(original.a))])    
        mod_distance = np.array([np.trapz(modified.v[:i+1], modified.t[:i+1]) 
                                             for i in range(len(modified.a))])
    elif mode == 'position':
        orig_distance = get_distance(original)
        mod_distance = get_distance(modified)
    elif mode == 'avgspeed':
        orig_distance = [np.average(original.v[:i+1])*t 
                                             for i, t in enumerate(original.t)]
        mod_distance = [np.average(modified.v[:i+1])*t 
                                            for i, t in enumerate(modified.t)]
    
    modinterp = np.interp(mod_distance, orig_distance, original.t)
    # plt.plot(orig_distance, original.t)            
    # fig = plt.figure(layout='constrained')
    # ax = fig.subplots(1)
    # ax.scatter(mod_distance, modified.t, s=2)
    # ax.scatter(mod_distance, modinterp, s=2)
    delta = modinterp[:len(original.t)] - original.t[:len(modinterp)]
    return np.array(mod_distance[:len(orig_distance)]), delta

import numpy as np
from gtbase.datacollector import VTACurve
class ShiftSummaryGraph():
    def __init__(self, run, fig=None, ax=None, ax2=None, *args, **kwargs):
        if plt_show := (fig is None):
            fig, (ax, ax2) = plt.subplots(2,1, layout='constrained', 
                                          *args, **kwargs)
            #import cardata, get name from id in run?
            fig.suptitle("TODO ADD TITLE") 
        
        # run = gtbeep.shiftstats.tests[0].runs[0]
        index = np.array([i for i in range(len(run)-1) 
                                                if run[i].gear!=run[i+1].gear])

        lo, hi = -40, 100
        # tot = hi - lo

        shifts = [VTACurve(run[i+lo-1:i+hi-1]) for i in index]
                
        [ax.plot(run.t+lo/60, run.a, label=f'Gear {g}->{g+1}') 
                                     for g, run in enumerate(shifts, start=1)]
        # [ax.plot(shifts[0].t, 1-shifts[0].clutch, label='Clutch (1=engaged)')]
        ax.legend()
        ax.grid()

        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Acceleration (m/s²)')

        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        ax.set_xlim(lo/60, (hi-1)/60)

        # [ax2.plot(run.t+lo/60, run.boost, label=f'Gear {g}->{g+1}') 
        #                                      for g, run in enumerate(shifts, start=1)]
        [ax2.scatter(shifts[0].t+lo/60, 1-shifts[0].clutch, 
                     label='Clutch (1-2) (1=engaged)', s=6)]
        [ax2.plot(run.t+lo/60, run.throttle/255, 
                  label=f'Throttle ({g}->{g+1}) (1=full)') 
                                      for g, run in enumerate(shifts, start=1)]
        ax2.legend()
        ax2.grid()

        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Boost (bar)')

        xmin, xmax = ax2.get_xlim()
        ymin, ymax = ax2.get_ylim()
        ax2.set_xlim(lo/60, (hi-1)/60)
        
        if plt_show:
            plt.show()

class ShiftStatsWindow():
    TITLE = "GT7ShiftTone: Shift/distance statistics"
    
    #target width and height of the graph, not the window
    WIDTH, HEIGHT= 815, 682
    FIGURE_DPI = 72

    def __init__(self, root, config, plot_handler, reset_handler):
        self.root = root
        self.plot_handler = plot_handler
        self.reset_handler = reset_handler
        self.window = None
        self.active_prev = -1
        self.window_scalar = config.window_scalar

    #From: https://stackoverflow.com/questions/33231484/python-tkinter-how-do-i-get-the-window-size-including-borders-on-windows
    #Get x and y coordinates to place graph underneath the main window.
    #This may not scale arbitrarily with varying border sizes and title sizes
    def get_windowoffsets(self):
        root = self.root.winfo_toplevel()
        return (root.winfo_x() + root.winfo_width(),  
                root.winfo_y())
    
    #100% scaling is 96 dpi in Windows, matplotlib defaults to 72 dpi
    #window_scalar allows the user to scale the window up or down
    def get_scaledfigsize(self):
        screen_dpi = self.root.winfo_fpixels('1i')
        scaling = screen_dpi / 96
        graph_dpi = self.FIGURE_DPI * scaling
        width = self.window_scalar * self.WIDTH / graph_dpi
        height = self.window_scalar * self.HEIGHT / graph_dpi

        return (width, height)
    
    def init_window(self):
        self.window = tkinter.Toplevel(self.root)
        self.window.title(self.TITLE)
        self.window.protocol('WM_DELETE_WINDOW', self.close)

        #place window to the right of main window
        x, y = self.get_windowoffsets()
        self.window.geometry(f"+{x}+{y}")
    
    def set_active(self, number):
        if self.active_prev != number:
            self.active_prev = number
            for i, var in enumerate(self.active_tk):
                var.set(1 if i==number else 0)
    
    def init_content(self, tests):
        tkinter.Label(self.window, text='Start speed (KPH)').grid(row=0, column=0)
        tkinter.Label(self.window, text='End speed (KPH)').grid(row=1, column=0)
        
        tkinter.Entry(self.window, textvariable=tests[0].start, width=8, 
                      justify='right').grid(row=0, column=1)
        tkinter.Entry(self.window, textvariable=tests[0].end, width=8, 
                      justify='right').grid(row=1, column=1)
        
        tkinter.Button(self.window, text='Plot', 
                       command=self.plot_handler).grid(row=0, column=3)
         
        tkinter.Button(self.window, text='Reset', 
                       command=self.reset_handler).grid(row=1, column=3)
        
        columns = ['Active', 'Name', 'Distance']
        for column, label in enumerate(columns):
            tkinter.Label(self.window, text=label).grid(row=2, column=column)
        
        self.active_tk = [tkinter.IntVar(value=0) for _ in tests]
        for row, (test, active) in enumerate(zip(tests, self.active_tk), start=3):
            tkinter.Checkbutton(self.window, variable=active, 
                                onvalue=1, offvalue=0).grid(row=row, column=0)
            tkinter.Entry(self.window, textvariable=test.name, width=12, 
                          justify='right').grid(row=row, column=1)
            tkinter.Label(self.window, textvariable=test.distance, width=12, 
                          justify='right').grid(row=row, column=2)
        
        #From: https://stackoverflow.com/questions/16334588/create-a-figure-that-is-reference-counted/16337909#16337909
        #Creating a Figure avoids a memory leak on closing the window
        self.fig = Figure(figsize=self.get_scaledfigsize(), 
                          dpi=self.FIGURE_DPI, layout="constrained")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.get_tk_widget().grid(row=5, column=0, columnspan=4)
        # self.window.columconfigure(column=4, weight=999)

    def is_open(self):
        return self.window is not None

    def draw_plot(self, *args, **kwargs):
        self.fig.clear()
        ShiftStatsGraph(fig=self.fig, *args, **kwargs)
        self.canvas.draw_idle()

    def create(self, tests):
        if self.window is not None: #force existing window to front
            self.window.deiconify()
            self.window.lift()
            return
        self.init_window()
        self.init_content(tests)

    def reset(self):
        self.active_prev = -1
        if self.is_open():     
            self.fig.clear()
            self.canvas.draw_idle()

    def close(self):
        self.window.destroy()
        self.window = None

class GUIShiftStats(ShiftStats):
    BASE = [
             ('blinky', 80, 250,), ('beep', 80, 250,)
           ]
    def __init__(self, root, config):
        super().__init__(config)
        
        self.tests = [GUIShiftTest(*entry, do_print=None) 
                                                        for entry in self.BASE]
        for test in self.tests:
            test.start = self.tests[0].start
            test.end = self.tests[0].end            
        
        self.button = tkinter.Button(root, text='Shift\nStats', 
                                     borderwidth=3,
                                     command=self.create_window)
        self.window = ShiftStatsWindow(root, config, 
                         plot_handler=self.draw_plot, reset_handler=self.reset)

    #enable the button in the GUI
    def enable(self):
        self.button.config(state=tkinter.ACTIVE)

    #disable the button in the GUI
    def disable(self):
        self.button.config(state=tkinter.DISABLED)

    def is_disabled(self):
        return self.button.cget('state') == tkinter.DISABLED

    def update(self, gtdp):
        super().update(gtdp)
        if self.window.is_open():
            self.window.set_active(self.activetest)

    def reset(self):
        super().reset()
        self.window.reset()

    #pass through grid arguments to button
    def grid(self, *args, **kwargs):
        self.button.grid(*args, **kwargs)

    def draw_plot(self, _=None):
        if not (len(self.tests[0].runs) and len(self.tests[1].runs)):
            print("Plot button pressed with no data")
            return None
        # if not (data := self.get_plotdata()):
        #     print("Plot button pressed with no data")
        #     return
        self.window.draw_plot(self.tests[0].runs[0], 
                              self.tests[1].runs[0])

    def create_window(self, event=None):
        self.window.create(self.tests)
        self.window.set_active(self.activetest)
    
    # #Assumes first run is done with blinky, second with beep
    # def get_plotdata(self, first=0, second=1):
    #     if not (len(self.tests[first].runs) and len(self.tests[second].runs)):
    #         return None
    #     return derive_distance_timedelta(self.tests[first].runs[0], 
    #                                      self.tests[second].runs[0])
    
