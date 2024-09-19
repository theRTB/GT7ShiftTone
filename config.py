# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 20:36:24 2023

@author: RTB
"""
import json
from os.path import exists

FILENAME_SETTINGS = 'config.json'

class config():
    target_ip = ''
    port = 12350
    packet_format = None
    
    sound_file = 'audio/audiocheck.net_sin_1000Hz_-3dBFS_0.1s.wav'
    sound_files = {100:'audio/audiocheck.net_sin_1000Hz_-3dBFS_0.1s.wav',
                    75:'audio/audiocheck.net_sin_1000Hz_-13dBFS_0.1s.wav',
                    50:'audio/audiocheck.net_sin_1000Hz_-23dBFS_0.1s.wav',
                    25:'audio/audiocheck.net_sin_1000Hz_-33dBFS_0.1s.wav' }
    
    notification_file = 'audio/audiocheck.net_sin_1500Hz_-13dBFS_0.05s.wav'
    notification_file_duration = 0.05 #must equal duration (s) of audio file
    notification_gear_enabled = True
    notification_gear_count = 2
    notification_gear_delay = 0.06
    notification_power_enabled = True
    notification_power_count = 3
    notification_power_delay = 0.08
    
    volume = 75 #default volume
    
    window_scalar = 1 #scale window by this factor
    window_x = None
    window_y = None
    
    #initial revlimit = engine_limit - guess
    #distance between engine_limit and revlimit has not been investigated for
    #GT7, so disabled due to having little to no benefit anyway
    revlimit_guess = -1
    
    beep_counter_max = 30 #minimum number of frames between beeps = 0.5ms
    beep_rpm_pct = 0.75 #counter resets below this percentage of beep rpm
    min_throttle_for_beep = 255 #only test if at or above throttle amount

    dynamictoneoffset = 1 #1 is true, 0 is false
    tone_offset = 17 #if specified rpm predicted to be hit in x packets: beep
    tone_offset_lower =  9
    tone_offset_upper = 25
    tone_offset_outlier = 30 #discard for dynamic tone if above this distance
    
    revlimit_percent = 0.98 #respected rev limit for trigger revlimit as pct%
    revlimit_percent_lower = 0.900
    revlimit_percent_upper = 0.999 #only meant to display the full graph
    
    revlimit_offset = 6 #additional buffer in x packets for revlimit
    revlimit_offset_lower = 3
    revlimit_offset_upper = 10
        
    hysteresis_percent = 0.005
    hysteresis_percent_lower = 0.00
    hysteresis_percent_upper = 0.051 #up to 0.05
    
    log_full_shiftdata = False
    log_basic_shiftdata = True
    we_beep_max = 30 #print previous packets for up to x packets after shift
    
    runcollector_minlen = 30
    runcollector_minlen_lock = 180
    #first few points are a ramp up to proper power, so they can negatively
    #affect shift rpm calculations slightly
    runcollector_remove_initial = 5
    #power curve has a minimum boost of 50% of maximum boost
    #points below this will be discarded
    runcollector_pct_lower_limit_boost = .5
    
    #as rpm ~ speed, and speed ~ tanh, linear regression + extrapolation 
    #overestimates slope and intercept. Keeping the deque short limits this
    linreg_len_min = 15
    linreg_len_max = 20
    
    #draw underfill of >=x% of peak power in the power graph
    graph_power_percentile = 0.9
    
    #TODO: are these still in use?
    revlimit_round = 50
    revlimit_round_offset = 10
    
    #round displayed shift RPM in GUI up to nearest x
    shiftrpm_round = 25
    
    #determine if cars_on_track is considered or not when testing to skip loop
    includereplay = False
        
    @classmethod
    def get_dict(cls):
        blocklist = ['update', 'get_dict', 'load_from', 'write_to']
        return {k:v for k,v in cls.__dict__.items() 
                                        if k not in blocklist and k[0] != '_'}

    @classmethod
    def load_from(cls, filename):
        if not exists(filename):
            return
        with open(filename) as file:
            file_config = json.load(file)
            for k,v in file_config.items(): 
                if k == 'sound_files': #json saves keys as string, force to int
                    v = {int(key):(value if value[:6] == 'audio/' 
                                   else f'audio/{value}')
                                                  for key, value in v.items()}
                #update old sound location to new audio folder
                if k == 'sound_file' and v[:6] != 'audio/':
                    v = f'audio/{v}'
                    
                setattr(cls, k, v)
    
    @classmethod
    def write_to(cls, filename):
        with open(filename, 'w') as file:
            json.dump(cls.get_dict(), file, indent=4)
