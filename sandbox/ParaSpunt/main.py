# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 12:15:02 2026

@author: KIAA
"""

# %% Import scripts
from level1_extractSoilinfo import *
from level2_ExtractSoilProp import *



# %% Input fra level 1 frontend 
port = 10000
passord = 'aB6h4mF+?DhW%C6A'


# %% Kjør level 1 frontend

Level1_Data = OptLevel1(port, passord) #Mottar navn på alle materialer i modellen i retur

data = {
    "KS_soil": {
        "name": ['KS_Su']
        }
    }

Level2_Data = OptLevel2(port,passord,data) #Sender navn på valgt KS-lag i modell



# job = {
#     "KS_soil": {
#         "name": ['KS_Su'],
#         "Current_xy": {
#             }
#     },

#     "Spunt_opt": {
#             "enabled": False,
#             "plates": ['Plate_1'],
#             "current_xy": [0,0]
#             "min_xy":[]
#             "phases": ["Opbygning3_ULS"]
#         },

#         "msf": {
#             "enabled": True,
#             "phases": ["FoS"]
#         },

#         "displacement": {
#             "enabled": True,
#             "phases": ["Opbygning3_SLS"],
#             "component": "Ux"   # optional: Ux, Uy, Utotal
#         }
#     },
#     "resultsPath": {
#         "path": rf"C:\Users\KIAA\OneDrive - Ramboll\Geo Scripting\RamPAP\Automatisere uttak av spuntberegninger fra Plaxis\Plaxis-Script\Results"
#         }
# }





