# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 13:52:52 2026

@author: KIAA
"""

from plxscripting.easy import *


    # Flatten material parameters
def flatten_material(mat):
    params = {}
    for attr in dir(mat):
        if attr.startswith('_') or callable(getattr(mat, attr)):
            continue
        try:
            value = getattr(mat, attr)
            # If nested object (like MohrCoulombPlasticity), flatten recursively
            if hasattr(value, '__dict__') or 'plxscripting.easy' in str(type(value)):
                nested_params = flatten_material(value)
                for k, v in nested_params.items():
                    params[f"{attr}.{k}"] = v
            else:
                params[attr] = value
        except:
            continue
    return params




def OptLevel2(port, password, data):
    """
    Returns all material parameters and polygon corner points for a soil material in Plaxis 2D.
    Works for all Plaxis versions and handles complex material models.
    
    Args:
        material_name (str): Name of the soil material.
    
    Returns:
        dict: {
            'material_params': dict of parameters (flattened),
            'polygon_points': list of list of tuples [(x1, y1), ...]
        }
    """
    
    material_name = data["KS_soil"]["name"][0]
    
    s_i, g_i = new_server('localhost', port, password=password)
    
    result = {'material_params': None, 'polygon_points': []}
    
    materials = g_i.Materials

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


    
    # Search for the material
    soil_material = None
    for mat in materials:
        type_name = getattr(mat, type_attr).value.lower()

        if "soil" in type_name:
            name_obj = getattr(mat, name_attr)
            if name_obj.value == material_name:
                soil_material = mat
                break

        

    
    if soil_material is None:
        raise ValueError(f"Material '{material_name}' not found.")

    result['material_params'] = flatten_material(soil_material)

    # Find all polygons using this material
    try:
        soil_polygons = [poly for poly in g_i.SoilPolygons if poly.Material.Name == material_name]
    except AttributeError:
        # Older versions might use g_i.Geometry.SoilPolygons
        soil_polygons = [poly for poly in g_i.Geometry.SoilPolygons if poly.Material.Name == material_name]

    # Extract corner points for each polygon
    for poly in soil_polygons:
        points = [(pt.X, pt.Y) for pt in poly.Points]
        result['polygon_points'].append(points)
    
    return result
