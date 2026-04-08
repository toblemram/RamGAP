"""Test that _find_phase matching works with output server phase names."""
from plxscripting.easy import new_server
import json, sys

try:
    s_o, g_o = new_server('localhost', 10001, password='=~Z3xH<D51<Bn3BG')
    
    # List all phases from output
    print("=== Output server phases ===")
    for ph in g_o.Phases:
        print(f"  {ph.Identification.value!r}")
    
    # Test matching with startswith
    targets = ['0.5.1 FoS', '0.5.2 Utpumping vann', '0.5.2.1 FoS']
    for target in targets:
        found = None
        for ph in g_o.Phases:
            ph_name = ph.Identification.value
            if ph_name == target or ph_name.startswith(target + ' [') or ph_name.startswith(target + '['):
                found = ph
                break
        if found:
            print(f"\nMatched '{target}' -> '{found.Identification.value}'")
            try:
                msf = found.Reached.SumMsf.value
                print(f"  SumMsf = {msf}")
            except:
                print(f"  (no SumMsf)")
        else:
            print(f"\nNO MATCH for '{target}'")
    
    # Test plate matching
    print("\n=== Output server plates ===")
    for p in g_o.Plates:
        print(f"  {p.Name.value!r}")
    
    target_plate = 'Spunt_venstre'
    found_plate = None
    for p in g_o.Plates:
        p_name = p.Name.value
        if p_name == target_plate or p_name.startswith(target_plate + ' ['):
            found_plate = p
            break
    
    if found_plate:
        print(f"\nMatched plate '{target_plate}' -> '{found_plate.Name.value}'")
        
        # Try getting Ux results from a phase
        disp_phase = None
        for ph in g_o.Phases:
            ph_name = ph.Identification.value
            if ph_name.startswith('0.5.2 Utpumping vann'):
                disp_phase = ph
                break
        
        if disp_phase:
            print(f"Disp phase: {disp_phase.Identification.value}")
            # Try ResultTypes
            print(f"Has ResultTypes.Plate: {hasattr(g_o.ResultTypes, 'Plate')}")
            if hasattr(g_o.ResultTypes, 'Plate'):
                rt = g_o.ResultTypes.Plate
                for attr in ['Ux', 'Ux2D', 'Utot']:
                    has = hasattr(rt, attr)
                    print(f"  Has {attr}: {has}")
                    if has:
                        rtype = getattr(rt, attr)
                        try:
                            vals = g_o.getresults(found_plate, disp_phase, rtype, 'node')
                            if vals:
                                print(f"  {attr} max = {max(abs(v) for v in vals):.4f}")
                            else:
                                print(f"  {attr} returned empty")
                        except Exception as e:
                            print(f"  {attr} getresults failed: {e}")
    else:
        print(f"\nNO MATCH for plate '{target_plate}'")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
