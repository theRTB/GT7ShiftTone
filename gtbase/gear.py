# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 20:46:58 2023

@author: RTB
"""

import json

from forzabase.gear import Gear, Gears, GearState

#Taken from ForzaShiftTone. GT7 telemetry officially goes up to 8 gears, but
#if a car has more than 8, it will overflow into other variables. This logic 
#has not been programmed in, so effectively only 8 gears. If we set this to 8
#the GUI doesn't align properly.
MAXGEARS = 10

class GearState(GearState):
    pass

with open('database/stock_ratios.json') as file:
    raw_ratios = json.load(file)
    stock_ratios = {int(k):v for k,v in raw_ratios.items()}

#class to hold all variables per individual gear
class Gear(Gear):
    #return True if we should play gear beep
    #gtdp currently unused, may be used for drivetrain analysis or gear ratio
    #derivation
    def update(self, gtdp, ratio=None): #prevgear):
        if self.state.at_initial():
            self.to_next_state()

        if self.state.at_least_locked():
            return False

        if ratio is None:
            return False
        
        self.set_ratio(ratio)

        self.to_next_state() #implied from reached to locked
        print(f'LOCKED {self.gear}: {ratio:.3f}')
        return True

#class to hold all gears up to the maximum of MAXGEARS
class Gears(Gears):
    GEARLIST = range(1, MAXGEARS+1)

    #first element is None to enable a 1:1 mapping of array to Gear number
    #it could be used as reverse gear but not in a usable manner anyway
    def __init__(self, config):
        self.gears = [None] + [Gear(g, config) for g in self.GEARLIST]
        self.highest = None

    def reset(self):
        super().reset()
        self.highest = None
        
    #Gear 1 - 8 are valid. Reverse is unknown, neutral is unknown.
    #Gear 9 - 10 gear ratios are not in the regular packets so will only update
    #the RPM display
    def is_valid(self, gtdp):
        gear = int(gtdp.gear)
        return 0 < gear <= 10
    
    def is_highest(self, gearnr):
        return self.highest == gearnr

    def get_ratios(self, gtdp, load_stock=False):
        if load_stock and gtdp.car_ordinal in stock_ratios.keys():
            print("Loaded ratios from file")
            return stock_ratios[gtdp.car_ordinal]['ratios']
        print("Using ratios from telemetry")
        return gtdp.gears[1:]

    #call update function of gear 1 to 8. We haven't updated the GUI display
    #because it messes up the available space
    def update(self, gtdp, load_stock=False):
        highest = 0
        ratios = self.get_ratios(gtdp, load_stock)
        for gear, ratio in zip(self.gears[1:-2], ratios):
            if (round(ratio, 3)) != 0.000:
                gear.update(gtdp, ratio)
                highest += 1
        if self.highest is None:
            self.highest = highest
            print(f'Highest gear: {self.highest}')