# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 22:33:15 2024

@author: RTB
"""

import numpy as np
from os.path import exists

from forzabase.enginecurve import EngineCurve

from utility import np_drag_fit

#Create stock folder within curves if it doesn't exist
#This shouldn't happen on a default installation
from os import makedirs
makedirs('curves/stock/', exist_ok=True)

#poorly named: does not extend Curve
#Given an array of consecutive rpm/accel points at full throttle and an array
#of consecutive accel points with the clutch disengaged we can derive a torque
#curve and thus a power curve.
#TODO: Do we round revlimit? It is generally above true revlimit.
#At stock, revlimit is a multiple of 100, but upgrades can be things like 3%
#more revs and make it a random number.
class EngineCurve(EngineCurve):
    DECIMALS = 2 #save power/torque shape to 2 decimals accuracy
    def init_from_run(self, *args, **kwargs):
        accelrun = kwargs.get('accelrun', None)
        if accelrun is None: # and len(args) > 0: #TODO defensive programming
            accelrun = args[0]
        result = np_drag_fit(*args, **kwargs)
        self.revlimit = accelrun.revlimit
        self.rpm, self.torque, self.power = result
        
        # self.correct_final_point()

    #TODO: consider rewriting to use path library
    #If file exists in base curves folder, it takes precedence over stock
    def file_exists(self, gtdp):
        if gtdp is None:
            return False

        filename_stock = f'{EngineCurve.FOLDER}/stock/{gtdp.car_ordinal}.tsv'

        return super().file_exists(gtdp) or exists(filename_stock)

    #gtdp is assumed to not be None here because files_exist tests for this
    def init_from_file(self, gtdp, load_stock=False, *args, **kwargs):
        super().init_from_file(gtdp)
        if self.curve_state:
            return

        if not load_stock:
            print("Stock curve toggle or BoP curve toggle forbids loading of curve")
            return

        filename_stock = f'{EngineCurve.FOLDER}/stock/{gtdp.car_ordinal}.tsv'
        if exists(filename_stock):
            self.load(filename_stock)
            print(f'Loaded stock curve from {filename_stock}')
            self.curve_state = True
            return

        print(f'init_from_file called but {self.FILENAME(gtdp)} and {filename_stock} do not exist')

    def correct_final_point(self):
        x1, x2 = self.rpm[-2:]
        # print(f'x1 {x1:.3f} x2 {x2:.3f} revlimit {self.revlimit}')
        np.append(self.rpm, self.revlimit)
        self.rpm = np.append(self.rpm, self.revlimit)
        for name in ['power', 'torque']: #,'boost']:
            array = getattr(self, name)
            y1, y2 = array[-2:]
            ynew = (y2 - y1) / (x2 - x1) * (self.revlimit - x2) + y2
            setattr(self, name, np.append(array, ynew))
            # print(f'y1 {y1:.3f} y2 {y2:.3f} ynew {ynew:.3f}')