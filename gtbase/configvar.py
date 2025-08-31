# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 20:54:19 2023

@author: RTB
"""

from utility import Variable
from forzabase.configvar import (ToneOffset, Volume, RevlimitOffset, 
                                 RevlimitPercent, HysteresisPercent, 
                                 IncludeReplay, DynamicToneOffsetToggle)
from gtbase.carordinal import GroupData

class ToneOffset(ToneOffset):
    pass

class Volume(Volume):
    pass

class RevlimitOffset(RevlimitOffset):
    pass

class RevlimitPercent(RevlimitPercent):
    pass

class HysteresisPercent(HysteresisPercent):
    pass

class IncludeReplay(IncludeReplay):
    def test(self, gtdp):
        return (self.get() or gtdp.cars_on_track)

class DynamicToneOffsetToggle(DynamicToneOffsetToggle):
    pass

class StockCurveToggle(Variable):
    def __init__(self, config):
        super().__init__(defaultvalue=config.stock_curve_toggle)

class BoPCurveToggle(Variable):
    def __init__(self, config):
        super().__init__(defaultvalue=config.bop_curve_toggle)
        self.groupdata = GroupData()

    def car_in_grouplist(self, gtdp):
        return self.groupdata.is_considered_bop(gtdp.car_ordinal)