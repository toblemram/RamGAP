# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 16:04:09 2026

@author: KIAA
"""



# ------------------------------------------------
# Detect getresults signature (once) getresults-funksjonen varerer basert på Plaxis versjon. Finner riktig. 
# ------------------------------------------------

def detect_getresults_signature(g_o, sample_obj, sample_phase, sample_result, location):

    # Try object-first
    try:
        g_o.getresults(sample_obj, sample_phase, sample_result, location)
        return "object_first"
    except:
        pass

    # Try object-last
    try:
        g_o.getresults(sample_phase, sample_result, location, sample_obj)
        return "object_last"
    except:
        pass

    # Try no-object
    try:
        g_o.getresults(sample_phase, sample_result, location)
        return "no_object"
    except:
        pass

    raise RuntimeError("Unsupported getresults() signature.")


def safe_getresults(g_o, signature, obj, phase, result_type, location):

    if result_type is None:
        return None

    if signature == "object_first":
        return g_o.getresults(obj, phase, result_type, location)

    if signature == "object_last":
        return g_o.getresults(phase, result_type, location, obj)

    if signature == "no_object":
        return g_o.getresults(phase, result_type, location)

    raise RuntimeError("Invalid getresults signature.")




#Finner riktig attribute (varierer basert på hvilken plaxis versjon man bruker)

def get_first_existing(obj, candidates):
    for name in candidates:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def get_embedded_beam_group(g_o):

    if hasattr(g_o.ResultTypes, "EmbeddedBeamRow"):
        return g_o.ResultTypes.EmbeddedBeamRow

    if hasattr(g_o.ResultTypes, "EmbeddedBeam"):
        return g_o.ResultTypes.EmbeddedBeam

    return None



#Bygger result config basert på plaxis-versjon OBS: print(dir(g_o.ResultTypes)) gir nyttig info
def build_result_config(g_o):

    config = {}

    # ------------------------------------------------
    # Plates
    # ------------------------------------------------
    if hasattr(g_o.ResultTypes, "Plate"):
        plate = g_o.ResultTypes.Plate

        config["plates"] = {
            "location": "node",
            "results": {
                "Nx": get_first_existing(plate, ["Nx2D", "N","Nx"]),
                "Q":  get_first_existing(plate, ["Q2D","Q","Qx"]),
                "M":  get_first_existing(plate, ["M2D","M", "Mx"]),
                "Ux": get_first_existing(plate, ["Ux","Ux2D"]),
                "Uy": get_first_existing(plate, ["Uy","Uy2D"]), 
                "Utotal": get_first_existing(plate, ["Utot","Utotal","Utot2D"])
            }
        }

    # ------------------------------------------------
    # Embedded Beams
    # ------------------------------------------------
    embedded = get_embedded_beam_group(g_o)
    if embedded:
        config["embedded_beams"] = {
            "location": "node",
            "results": {
                "Nx": get_first_existing(embedded, ["Nx2D", "N","Nx"]),
                "Q":  get_first_existing(embedded, ["Q2D","Q","Qx"]),
                "M":  get_first_existing(embedded, ["M2D","M", "Mx"]),
                "Ux": get_first_existing(embedded, ["Ux","Ux2D"]),
                "Uy": get_first_existing(embedded, ["Uy","Uy2D"]), 
                "Utotal": get_first_existing(embedded, ["Utot","Utotal","Utot2D"])
            }
        }

    # ------------------------------------------------
    # Geogrids
    # ------------------------------------------------
    if hasattr(g_o.ResultTypes, "Geogrid"):
        geogrid = g_o.ResultTypes.Geogrid

        config["geogrids"] = {
            "location": "node",
            "results": {
                "N":    get_first_existing(geogrid, ["Nx2D","N", "Nx"]),
                "Nmax": get_first_existing(geogrid, ["NEnvelopeMax","NEnvelopeMax2D", "NxEnvelopeMax2D"]),
                "Ux": get_first_existing(geogrid, ["Ux","Ux2D"]),
                "Uy": get_first_existing(geogrid, ["Uy","Uy2D"]), 
                "Utotal": get_first_existing(geogrid, ["Utot","Utotal","Utot2D"])
            }
        }

    # ------------------------------------------------
    # Node to Node Anchors
    # ------------------------------------------------
    if hasattr(g_o.ResultTypes, "NodeToNodeAnchor"):
        anchor = g_o.ResultTypes.NodeToNodeAnchor

        config["node_to_node_anchors"] = {
            "location": "node",
            "results": {
                "N":    get_first_existing(anchor, ["N", "Nx","Nx2D"]),
                "Nmax": get_first_existing(anchor, ["NEnvelopeMax","NEnvelopeMax2D", "NxEnvelopeMax2D"]),
                "Ux": get_first_existing(anchor, ["Ux","Ux2D"]),
                "Uy": get_first_existing(anchor, ["Uy","Uy2D"]), 
                "Utotal": get_first_existing(anchor, ["Utot","Utotal","Utot2D"])
            }
        }

    # ------------------------------------------------
    # Fixed End Anchors
    # ------------------------------------------------
    if hasattr(g_o.ResultTypes, "FixedEndAnchor"):
        fea = g_o.ResultTypes.FixedEndAnchor

        config["fixed_end_anchors"] = {
            "location": "node",
            "results": {
                "N":    get_first_existing(fea, ["N", "Nx","Nx2D"]),
                "Nmax": get_first_existing(fea, ["NEnvelopeMax","NEnvelopeMax2D", "NxEnvelopeMax2D"]),
                "Ux": get_first_existing(fea, ["Ux","Ux2D"]),
                "Uy": get_first_existing(fea, ["Uy","Uy2D"]), 
                "Utotal": get_first_existing(fea, ["Utot","Utotal","Utot2D"])
            }
        }

    return config




def run_capacity(g_o, selected_structures, phases):
    """
    Extracts maximum absolute structural forces
    for selected structures in selected phases.
    Location (node/element) is automatically selected
    per structure type.
    """

    results = {}

    # ------------------------------------------------
    # Result type + location map per structure type
    # ------------------------------------------------

    result_config = build_result_config(g_o)    




    # ----------------------------------------
    # Detect getresults signature once
    # ----------------------------------------

    signature = None

    # Find first valid sample combination
    for struct_type, objects in selected_structures.items():
        if objects and struct_type in result_config:
            sample_obj = objects[0]
            sample_phase = phases[0]
            sample_result = next(
                (r for r in result_config[struct_type]["results"].values() if r),
                None
            )
            location = result_config[struct_type]["location"]

            if sample_result:
                signature = detect_getresults_signature(
                    g_o,
                    sample_obj,
                    sample_phase,
                    sample_result,
                    location
                )
                break

    if signature is None:
        raise RuntimeError("Could not detect getresults signature.")


    # ------------------------------------------------
    # Extraction loop
    # ------------------------------------------------

    for struct_type, objects in selected_structures.items():

        if not objects:
            continue

        results[struct_type] = {}

        location = result_config[struct_type]["location"]
        result_types = result_config[struct_type]["results"]

        for obj in objects:

            obj_name = obj.Name.value
            results[struct_type][obj_name] = {}

            for phase in phases:

                phase_name = phase.Identification.value
                results[struct_type][obj_name][phase_name] = {}

                for force_name, result_type in result_types.items():
                    
                    try: 
                        values = safe_getresults(g_o,signature,obj,phase,result_type,location)


                        if values:
                            max_force = max(abs(v) for v in values)
                        else:
                            max_force = None

                    except Exception:
                        max_force = None

                    results[struct_type][obj_name][phase_name][force_name] = max_force

    return results


# ------------------------------------------------
# MSF extraction (robust + supports SumMsf)
# ------------------------------------------------

def detect_msf_accessor(sample_phase):
    """
    Detects where the final MSF is stored in this PLAXIS version.
    Returns a callable that extracts MSF.
    """

    # Most modern structure
    if hasattr(sample_phase, "Reached"):
        reached = sample_phase.Reached

        if hasattr(reached, "SumMsf"):
            return lambda phase: phase.Reached.SumMsf.value

        if hasattr(reached, "MsfReached"):
            return lambda phase: phase.Reached.MsfReached.value

        if hasattr(reached, "Msf"):
            return lambda phase: phase.Reached.Msf.value

    # Alternative safety containers
    if hasattr(sample_phase, "DeformCalcSafety"):
        safety = sample_phase.DeformCalcSafety
        if hasattr(safety, "MsfReached"):
            return lambda phase: phase.DeformCalcSafety.MsfReached.value

    if hasattr(sample_phase, "SafetyCalculation"):
        safety = sample_phase.SafetyCalculation
        if hasattr(safety, "MsfReached"):
            return lambda phase: phase.SafetyCalculation.MsfReached.value

    raise RuntimeError("Could not locate MSF property in this PLAXIS version.")


def run_msf(g_o, phases):

    if not phases:
        return {}

    results = {}

    # Detect accessor once
    msf_accessor = detect_msf_accessor(phases[0])

    for phase in phases:

        phase_name = phase.Identification.value

        try:
            msf_value = msf_accessor(phase)
        except Exception:
            msf_value = None

        results[phase_name] = msf_value

    return results



# ------------------------------------------------
# Displacement extraction
# ------------------------------------------------

def run_displacement(g_o, selected_structures, phases, component):

    results = {}
    result_config = build_result_config(g_o)

    if not phases:
        return results

    # ----------------------------------------
    # Detect signature once (reuse capacity logic)
    # ----------------------------------------

    signature = None

    for struct_type, objects in selected_structures.items():
        if objects and struct_type in result_config:
            sample_obj = objects[0]
            sample_phase = phases[0]
            sample_result = result_config[struct_type]["results"].get(component)
            location = result_config[struct_type]["location"]

            if sample_result:
                signature = detect_getresults_signature(
                    g_o,
                    sample_obj,
                    sample_phase,
                    sample_result,
                    location
                )
                break

    if signature is None:
        return results

    # ----------------------------------------
    # Extraction loop
    # ----------------------------------------

    for struct_type, objects in selected_structures.items():

        if not objects or struct_type not in result_config:
            continue

        location = result_config[struct_type]["location"]
        result_type = result_config[struct_type]["results"].get(component)

        if not result_type:
            continue

        results[struct_type] = {}

        for obj in objects:

            obj_name = obj.Name.value
            results[struct_type][obj_name] = {}

            for phase in phases:

                phase_name = phase.Identification.value

                try:
                    values = safe_getresults(
                        g_o,
                        signature,
                        obj,
                        phase,
                        result_type,
                        location
                    )

                    if values:
                        max_disp = max(abs(v) for v in values)
                    else:
                        max_disp = None

                except Exception:
                    max_disp = None

                results[struct_type][obj_name][phase_name] = max_disp

    return results
