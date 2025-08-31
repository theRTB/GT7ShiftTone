# -*- coding: utf-8 -*-
"""
Created on Sat Jul 20 15:15:00 2024

@author: RTB
"""

from forzabase.shiftdump import ShiftDump

#in GTBeep init_vars: self.shiftdump = ShiftDump(self.lookahead)
#in GTBeep loop_func funcs:  'loop_shiftdump',        #dump shift data
#in GTBeep functions:
    # def loop_shiftdump(self, gtdp):
    #     self.shiftdump.update(gtdp)

#maxlen preferred even
class ShiftDump(ShiftDump):
    gtdp_props = ['current_engine_rpm', 'throttle', 'in_gear', 'clutch', 
                  'clutch_rpm', 'boost', 'gear']
    columns = ['rpm', 'throttle', 'in_gear', 'clutch', 'clutch_rpm', 'boost', 
               'gear', ' slope', 'intercept', 'num']
    
    def make_point(self, gtdp):
        data = {prop:getattr(gtdp, prop) for prop in self.gtdp_props}
        data['slope'] = self.lookahead.slope
        data['intercept'] = self.lookahead.intercept
        
        for key in ['slope', 'intercept']:
            data[key] = 0 if data[key] is None else data[key]
        for key in ['current_engine_rpm', 'clutch_rpm']:
            data[key] = int(data[key])
        for key in ['clutch', 'boost', 'slope', 'intercept']:
            data[key] = round(data[key], 2)
        
        return data