# -*- coding: utf-8 -*-
"""
Created on Sun Jul 21 13:53:13 2024

@author: RTB
"""

import csv
from os.path import exists
from mttkinter import mtTkinter as tkinter

from utility import Variable

#as_integer array of column names to be converted to integer
#index is the column name to use as key
def load_csv(filename, index, as_integer=[]):
    data = {}
    if not exists(filename):
        print(f'file {filename} does not exist')
        return None
    
    with open(filename, encoding='ISO-8859-1') as rawcsv:
        csvobject = csv.DictReader(rawcsv, delimiter=',')
        for row in csvobject:
            if row[index] == '':
                print(f'missing ordinal: {row}')
                continue
            for k, v in row.items():
                row[k] = int(v) if (k in as_integer and v != '') else v
            data[row[index]] = row
    return data
    
class CarData():
    FILENAME_CAR = 'data\cars.csv'
    FILENAME_MAKER = 'data\maker.csv'
    AS_INTEGER = ['ID', 'Maker']
    INDEX = 'ID'
    
    cardata = load_csv(FILENAME_CAR, INDEX, AS_INTEGER)
    makerdata = load_csv(FILENAME_MAKER, INDEX, AS_INTEGER)
    
    @classmethod
    def get_name(cls, car_ordinal):
        car = cls.cardata.get(car_ordinal, {})
        if car is None:
            return f'Unknown car (o{car_ordinal})'
        name = cls.cardata[car_ordinal]['ShortName']
        maker_id = cls.cardata[car_ordinal]['Maker']
        maker = cls.makerdata.get(maker_id, {}).get('Name', '')
        return f'{maker} {name} (o{car_ordinal})'
        
class CarOrdinal(Variable):
    def test(self, value):
        if self.get() != value:
            return True
        return False

class GUICarOrdinal(CarOrdinal):
    def __init__(self, root, defaultguivalue=''):
        super().__init__()
        self.defaultguivalue = defaultguivalue
        
        self.tkvar = tkinter.StringVar(value=defaultguivalue)
        
        self.label = tkinter.Label(root, text='Car ID')
        self.entry = tkinter.Entry(root, textvariable=self.tkvar, width=6,
                                   state='readonly', justify=tkinter.RIGHT)
    
    #sticky and columnspan are not forwarded to the grid function
    def grid(self, column, sticky='', columnspan=1, *args, **kwargs):
        self.label.grid(column=column, columnspan=1, 
                        sticky=tkinter.E, *args, **kwargs)    
        self.entry.grid(column=column+1, columnspan=1,
                        sticky=tkinter.W, *args, **kwargs) 

    def gui_get(self):
        return self.tkvar.get()

    def get_name(self):
        return CarData.get_name(self.get())

    def set(self, value):
        super().set(value)
        gui_value = value #CarData.get_name(value)
        self.tkvar.set(gui_value)
        
    def reset(self):
        super().reset()
        self.tkvar.set(self.defaultguivalue)