# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 20:54:19 2023

@author: RTB
"""

from forzabase.configvar import (ToneOffset, Volume, RevlimitOffset, 
                                 RevlimitPercent, HysteresisPercent, 
                                 IncludeReplay, DynamicToneOffsetToggle)

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