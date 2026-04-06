# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 12:17:30 2026

@author: KIAA
"""





from plxscripting.easy import *




def OptLevel1(port: int, password: str) -> dict:
    s_i, g_i = new_server('localhost', port, password=password)
    
    g_i.gotostructures()    
    
    materials = g_i.Materials

    soil_names = []

    # --- Detect attributes ONCE using first valid material ---
    type_attr = None
    name_attr = None

    for mat in materials:
        # Detect type attribute
        try:
            _ = mat.TypeName.value
            type_attr = "TypeName"
        except:
            continue

        # Detect name attribute
        if hasattr(mat, "Identification"):
            name_attr = "Identification"
        elif hasattr(mat, "Name"):
            name_attr = "Name"        
        

        # Stop once both are found
        if type_attr and name_attr:
            break

    # --- Main loop (fast, no try/except inside) ---
    for mat in materials:
        type_name = getattr(mat, type_attr).value.lower()

        if "soil" in type_name:
            name_obj = getattr(mat, name_attr)
            soil_names.append(name_obj.value)

    return {"soil_names": soil_names}