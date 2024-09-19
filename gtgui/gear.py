# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 20:46:58 2023

@author: RTB
"""

from gtbase.gear import Gear, GearState, Gears
from forzagui.gear import GenericGUIGear, GenericGUIGears

#class for GUI display of class Gear
#TODO: remove variance from Gear and GUIGear for GT7, it's unused
class GUIGear(GenericGUIGear, Gear):    
    FG_DEFAULT = '#000000'
    BG_UNUSED  = '#F0F0F0'
    BG_REACHED = '#FFFFFF'
    BG_LOCKED  = '#CCDDCC'
    #                             tuple of (shiftpm_fg, shiftrpm_bg),
    #                                      (entry_fg    entry_bg)
    ENTRY_COLORS = {GearState.UNUSED:     ((BG_UNUSED,  BG_UNUSED),
                                           (BG_UNUSED,  BG_UNUSED)),
                    GearState.REACHED:    ((BG_UNUSED,  BG_UNUSED),
                                           (BG_UNUSED,  BG_UNUSED)),
                    GearState.LOCKED:     ((BG_REACHED, BG_REACHED),
                                           (FG_DEFAULT, BG_LOCKED)),
                    GearState.CALCULATED: ((FG_DEFAULT, BG_LOCKED),
                                           (FG_DEFAULT, BG_LOCKED))}
    for key, (t1, t2) in ENTRY_COLORS.items():
        ENTRY_COLORS[key] = (dict(zip(['fg', 'readonlybackground'], t1)), 
                             dict(zip(['fg', 'readonlybackground'], t2)))
        
    def __init__(self, number, root, config):
        super().__init__(number, root, config)

    #override to skip gridding of variance
    def init_grid(self, column=None, starting_row=0):
        super().init_grid(column, starting_row)
        self.variance_entry.grid_remove() #force remove variance afterwards

    def reset(self):
        super().reset()
        self.var_bound = None
        self.update_entry_colors()
        self.variance_entry.grid_remove() #force remove variance afterwards

    def to_next_state(self):
        super().to_next_state()
        self.update_entry_colors()
        # if self.state.at_final():
        #     self.variance_entry.grid_remove()

    def update(self, gtdp, prevgear):
        if self.var_bound is None:
            self.var_bound = 1e-5 #self.VAR_BOUNDS[fdp.drivetrain_type]
        return super().update(gtdp, prevgear)

class GUIGears(GenericGUIGears, Gears):
    def __init__(self, root, config):
        self.gears = [None] + [GUIGear(g, root, config) for g in self.GEARLIST]
        
        self.init_window(root)