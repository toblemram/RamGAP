# -*- coding: utf-8 -*-
"""
Created on Sat Mar 29 14:06:41 2025

Main.py er et midlertidig script som oppfører seg som frontend. Her er hver level av applikasjonen vist i forskjellige funksjoner som kalles. 
Input og output til main, tilsvarer input og retur til/fra frontend

@author: KIAA
"""



# %% Import scripts
from level1_extractInfo import *
from level5_getData import *


# %% Input fra level 1 frontend 
port = 10000
passord = 'aB6h4mF+?DhW%C6A'


# %% Kjør level 1 frontend

Level1_Data = level1(port, passord) #Mottar Faser og structures i retur. 

    # # Access returned data
    # plate_names = Level1_Data["plates"]["names"]
    # plate_display = Level1_Data["plates"]["structkallenavn"]

    # phase_names = Level1_Data["phases"]

#Level 1 OK
# %% Kjør level 2, 3, 4 frontend


#Eksempel-data under som matcher Plaxis modell fra eksemplet

job = {
    "structures": {
        "plates": ['Spunt_venstre', 'Plate_2'],
        "fixed_end_anchors": [],
        "node_to_node_anchors": ["NodeToNodeAnchor_1"],
        "embedded_beams": [],
        "geogrids": []
    },

    "analysis": {

        "capacity_check": {
            "enabled": True,
            "phases": ["0.5 Utgraving traubunn -2", "0.5.2 Utpumping vann"]
        },

        "msf": {
            "enabled": True,
            "phases": ["0.5.1 FoS","0.5.2.1 FoS"]
        },

        "displacement": {
            "enabled": True,
            "phases": ["0.5 Utgraving traubunn -2", "0.5.2 Utpumping vann"],
            "component": "Uy"   # optional: Ux, Uy, Utotal
        }
    },
    "resultsPath": {
        "path": rf"C:\Users\KIAA\OneDrive - Ramboll\Geo Scripting\RamPAP\Automatisere uttak av spuntberegninger fra Plaxis\Plaxis-Script\Results"
        }
}


Level5_Data = level5(port, passord, job)




