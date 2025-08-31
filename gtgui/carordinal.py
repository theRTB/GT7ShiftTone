# -*- coding: utf-8 -*-
"""
Created on Sun Jul 21 13:53:13 2024

@author: RTB
"""

from forzagui.carordinal import GenericGUICarOrdinal
from gtbase.carordinal import CarOrdinal

class GUICarOrdinal(GenericGUICarOrdinal, CarOrdinal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)