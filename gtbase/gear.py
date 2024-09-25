# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 20:46:58 2023

@author: RTB
"""

from forzabase.gear import Gear, Gears, GearState

#Taken from ForzaShiftTone. GT7 telemetry officially goes up to 8 gears, but
#if a car has more than 8, it will overflow into other variables. This logic 
#has not been programmed in, so effectively only 8 gears. If we set this to 8
#the GUI doesn't align properly.
MAXGEARS = 10

class GearState(GearState):
    pass

#class to hold all variables per individual gear
class Gear(Gear):
    #return True if we should play gear beep
    def update(self, gtdp, prevgear):
        if self.state.at_initial():
            self.to_next_state()

        if self.state.at_least_locked():
            return
        if not (ratio := round(gtdp.gears[self.gear], 3)):
            return
        
        self.set_ratio(ratio)
        
        #we use a reverse logic here because the gears are locked sequentially
        #1 is set then 2, then 3, etc
        #but we need the 'next gear' to get the relative ratio which is not set
        #yet at that point.
        if prevgear is not None and prevgear.state.at_least_locked():
            relratio =  prevgear.get_ratio() / ratio
            prevgear.set_relratio(relratio)
            
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
    def is_valid(self, fdp):
        gear = int(fdp.gear)
        return 0 < gear <= 10
    
    def is_highest(self, gearnr):
        return self.highest == gearnr

    #call update function of gear 1 to 8. We haven't updated the GUI display
    #because it messes up the available space
    #add the previous gear for relative ratio calculation
    def update(self, gtdp):
        highest = 0
        for gear, prevgear in zip(self.gears[1:-2], [None] + self.gears[1:-3]):
            if gtdp.gears[gear.gear] != 0.000:
                gear.update(gtdp, prevgear)
                highest += 1
        if not self.highest:
            self.highest = highest
            print(f'Highest gear: {self.highest}')