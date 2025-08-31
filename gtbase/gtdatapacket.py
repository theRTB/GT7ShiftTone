# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 21:21:57 2024

@author: RTB
"""

import struct

from salsa20 import Salsa20_xor

#Alternatives for packet data:
# https://github.com/cybercic/GT7toMoTeC/blob/main/stm/gt7/packet.py
# https://github.com/RaceCrewAI/gt-telem/blob/main/gt_telem/models/telemetry.py
# https://github.com/Bornhall/gt7telemetry/blob/main/gt7telemetry.py
# https://github.com/snipem/gt7dashboard/blob/main/gt7dashboard/gt7communication.py
# https://github.com/zetetos/gt-telemetry/blob/main/internal/gttelemetry/gran_turismo_telemetry.go

#For our purposes we only need a small number of variables from the packet
class GTDataPacket():
    FLAGNAMES = ['cars_on_track', 'paused', 'loading', 'in_gear', 'turbo',
                 'overrev', 'handbrake', 'lights_active', 'high_beams', 
                 'low_beams', 'asm_active', 'tcs_active', 
                 'unknown1', 'unknown2', 'unknown3', 'unknown4']
    PROPS = ['position_x', 'position_y', 'position_z', 'speed_x', 'speed_y',
             'speed_z', 'ride_height', 'current_engine_rpm',
             'fuel_level', 'fuel_capacity', 'speed', 'boost',
             'tiretempFL', 'tiretempFR', 'tiretempRL', 'tiretempRR',
             'packet_id',
             'upshift_rpm', 'engine_max_rpm', 'est_top_speed', #FLAGNAMES
             'gear', 'throttle', 'brake', 
             'tirerotFL', 'tirerotFR', 'tirerotRL', 'tirerotRR',
             'tireradiusFL', 'tireradiusFR', 'tireradiusRL', 'tireradiusRR', 
             'clutch', 'clutch_in', 'clutch_rpm',
             'gears', 'car_ordinal']

    def __init__(self, data):
        ddata = GTDataPacket.decrypt(data)
        self.ddata = ddata
        if not len(ddata):
            print("Packet did not pass magic number check")
            return
        # print("".join("{:02x}".format(ord(c)) for c in rawdata))

        #self.header = struct.unpack('i', ddata[0x04:0x04 + 4])[0]

        self.position_x = struct.unpack('f', ddata[0x04:0x04 + 4])[0]
        self.position_y = struct.unpack('f', ddata[0x08:0x08 + 4])[0]
        self.position_z = struct.unpack('f', ddata[0x0C:0x0C + 4])[0]

        self.speed_x = struct.unpack('f', ddata[0x10:0x10 + 4])[0]
        self.speed_y = struct.unpack('f', ddata[0x14:0x14 + 4])[0]
        self.speed_z = struct.unpack('f', ddata[0x18:0x18 + 4])[0]

        # sway
        # heave
        # surge

        #self.header = struct.unpack('f', ddata[0xZZ:0xZZ + 4])[0]

        #angularvelocityvector? 3 floats?

        self.ride_height = struct.unpack('f', ddata[0x38:0x38 + 4])[0]

        self.current_engine_rpm = struct.unpack('f', ddata[0x3C:0x3C + 4])[0]  # rpm

        #0x40 - 0x44 0iv for decryption

        self.fuel_level = struct.unpack('f', ddata[0x44:0x44 + 4])[0]

        self.fuel_capacity = struct.unpack('f', ddata[0x48:0x48 + 4])[0]
       
        self.speed = struct.unpack('f', ddata[0x4C:0x4C + 4])[0] #ground speed?
        self.boost = struct.unpack('f', ddata[0x50:0x50+4])[0] #no -1

        self.oilpressure = struct.unpack('f', ddata[0x54:0x54+4])[0]
        self.waterpressure = struct.unpack('f', ddata[0x58:0x58+4])[0]
        self.oiltemperature =struct.unpack('f', ddata[0x5C:0x5C+4])[0]

        #Always in Celsius or region dependent?
        self.tiretempFL = struct.unpack('f', ddata[0x60:0x60+4])[0]
        self.tiretempFR = struct.unpack('f', ddata[0x64:0x64+4])[0]
        self.tiretempRL = struct.unpack('f', ddata[0x68:0x68+4])[0]
        self.tiretempRR = struct.unpack('f', ddata[0x6C:0x6C+4])[0]

        self.packet_id = struct.unpack('i', ddata[0x70:0x70 + 4])[0]
            
        self.upshift_rpm = struct.unpack('H', ddata[0x88:0x88 + 2])[0]
        self.engine_max_rpm = struct.unpack('H', ddata[0x8A:0x8A + 2])[0]
        
        #Note: may be in mph or kph according to comments
        self.est_top_speed = struct.unpack('h', ddata[0x8C:0x8C+2])[0]
        
        flags = struct.unpack('B', ddata[0x8E:0x8E + 1])[0]
        for i, varname in enumerate(self.FLAGNAMES):
            flag = bool(1<<i & flags)
            setattr(self, f'{varname}', flag)
            
        self.gear = struct.unpack('B', ddata[0x90:0x90 + 1])[0] & 0b00001111
        self.throttleoutput = struct.unpack('B', ddata[0x91:0x91 + 1])[0]
        self.brakeinput = struct.unpack('B', ddata[0x92:0x92 + 1])[0]
        
        #In radians
        self.tirerotFL = struct.unpack('f', ddata[0xA4:0xA4+4])[0] 
        self.tirerotFR = struct.unpack('f', ddata[0xA8:0xA8+4])[0] 
        self.tirerotRL = struct.unpack('f', ddata[0xAC:0xAC+4])[0] 
        self.tirerotRR = struct.unpack('f', ddata[0xB0:0xB0+4])[0] 
        
        #These appear to be constants
        self.tireradiusFL = struct.unpack('f', ddata[0xB4:0xB4+4])[0] 
        self.tireradiusFR = struct.unpack('f', ddata[0xB8:0xB8+4])[0] 
        self.tireradiusRL = struct.unpack('f', ddata[0xBC:0xBC+4])[0] 
        self.tireradiusRR = struct.unpack('f', ddata[0xC0:0xC0+4])[0] 
        
        #Clutch appears to be binary without a real life shifter
        self.clutch = struct.unpack('f', ddata[0xF4:0xF4 + 4])[0]
        self.clutch_in = struct.unpack('f', ddata[0xF8:0xF8 + 4])[0]
        self.clutch_rpm = struct.unpack('f', ddata[0xFC:0xFC + 4])[0]
                
        #potentially drivetrain ratio for best theoretical top speed?
        #unlisted, may be wrong. Used to be reverse ratio
        self.top_speed_ratio = struct.unpack('f', ddata[0x100:0x100 + 4])[0]
        
        #None as gear 0 for a 1:1 mapping for gear number
        gears = list(struct.unpack('8f', ddata[0x104:0x124]))
        self.gears = [None] + [round(g, 3) for g in gears]
        
        #Is overwritten if car has >8 gears
        self.car_id = struct.unpack('i', ddata[0x124:0x124 + 4])[0]
        
        #aliases
        self.throttle = self.throttleoutput
        self.brake = self.brakeinput
        self.accel = self.throttle
        self.rpm =  self.current_engine_rpm
        self.car_ordinal = self.car_id

        # packetlength = len(ddata)
        # if   packetlength == 296:
        #     self.packettype = 'A'
        # elif packetlength == 316:
        #     self.packettype = 'B'
        #
        #     self.steer = struct.unpack('f', ddata[0x128:0x128 + 4])[0]
        #     self.ffb = struct.unpack('f', ddata[0x12C:0x12C + 4])[0]
        #     self.sway2 = struct.unpack('f', ddata[0x120:0x120 + 4])[0]
        #     self.heave2 = struct.unpack('f', ddata[0x124:0x124 + 4])[0]
        #     self.surge2 = struct.unpack('f', ddata[0x128:0x128 + 4])[0]
        # elif packetlength == 344:
        #     self.packettype = '~'
        #
        #     self.throttleinput = struct.unpack('B', ddata[0x13C:0x13C + 1])[0]
        #     self.brakeoutput = struct.unpack('B', ddata[0x13D:0x13D + 1])[0]
        #
        #     self.unkn3_bitfield = struct.unpack('B', ddata[0x13E:0x13E + 1])[0]
        #     self.unkn4_bitfield = struct.unpack('B', ddata[0x13F:0x13F + 1])[0]
        #
        #     #related to torque vectoring
        #     self.unkn4_vector1 = struct.unpack('f', ddata[0x140:0x140 + 4])[0]
        #     self.unkn4_vector2 = struct.unpack('f', ddata[0x144:0x144 + 4])[0]
        #     self.unkn4_vector3 = struct.unpack('f', ddata[0x148:0x148 + 4])[0]
        #     self.unkn4_vector4 = struct.unpack('f', ddata[0x14C:0x14C + 4])[0]
        #
        #     self.energyrecovery = struct.unpack('f', ddata[0x150:0x150 + 4])[0]
        #
        #     self.unkn7_float = struct.unpack('f', ddata[0x154:0x154 + 4])[0]
        # else:
        #     self.packettype = '?'
    
    def print(self):
        print(self.ddata)
    
    @classmethod
    def get_props(cls):
        # flags = [self.get_flag(name) for name in self.FLAGNAMES]
        # props = [(name, getattr(self, name)) for name in self.PROPS]
        # flagnames = [f'{name}' for name in self.FLAGNAMES]
        return cls.FLAGNAMES + cls.PROPS
    
    #From https://github.com/snipem/gt7dashboard/blob/main/gt7dashboard/gt7communication.py
    #TODO: implement B and ~ packets with their key and magic number
    @staticmethod
    def decrypt(dat):
        KEY = b'Simulator Interface Packet GT7 ver 0.0'
        oiv = dat[0x40:0x44]
        iv1 = int.from_bytes(oiv, byteorder='little')
        iv2 = iv1 ^ 0xDEADBEAF 
        IV = bytearray()
        IV.extend(iv2.to_bytes(4, 'little'))
        IV.extend(iv1.to_bytes(4, 'little'))
        ddata = Salsa20_xor(dat, bytes(IV), KEY[0:32])
    
        #check magic number
        magic = int.from_bytes(ddata[0:4], byteorder='little')
        if magic != 0x47375330:
            return bytearray(b'')
        return ddata