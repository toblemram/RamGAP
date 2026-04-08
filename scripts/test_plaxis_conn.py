"""Quick test script to debug Plaxis connection."""
from plxscripting.easy import new_server
import json

PASSWORD = r"~Z3xH<D51<Bn3BG"

# Try different port combos
for port, label in [(10000, "Input"), (10001, "Output")]:
    print(f"\n--- Testing port {port} ({label}) ---")
    try:
        s, g = new_server('localhost', port, password=PASSWORD)
        print(f"  TCP connect OK")
        try:
            # Try a simple command
            phases = list(g.Phases)
            print(f"  Commands work! Found {len(phases)} phases")
            for ph in phases:
                print(f"    Phase: {ph.Identification.value}")
        except Exception as e:
            err = str(e)[:100]
            print(f"  Command failed: {err}")
            # Try without password
            try:
                s2, g2 = new_server('localhost', port, password='')
                phases2 = list(g2.Phases)
                print(f"  ** Works with EMPTY password! {len(phases2)} phases")
            except:
                pass
    except Exception as e:
        print(f"  Connection failed: {e}")

# Check mode
try:
    mode = g_i.Mode.value if hasattr(g_i, 'Mode') else 'unknown'
    print(f"Current mode: {mode}")
except Exception as e:
    print(f"Mode check: {e}")

# Try gotostages
try:
    g_i.gotostages()
    print("gotostages() OK")
except Exception as e:
    print(f"gotostages() error: {e}")

# Check if calculate works
try:
    has_calc = hasattr(g_i, 'calculate')
    print(f"Has calculate attr: {has_calc}")
except Exception as e:
    print(f"calculate attr check: {e}")

# List phases
try:
    for ph in g_i.Phases:
        ct_name = ""
        try:
            ct_name = str(ph.DeformCalcType)
        except:
            pass
        print(f"  Phase: {ph.Identification.value} ({ct_name})")
except Exception as e:
    print(f"Phases error: {e}")

# List materials
try:
    for mat in g_i.Materials:
        try:
            name = mat.Identification.value
            tn = ""
            try:
                tn = mat.TypeName.value
            except:
                pass
            print(f"  Material: {name} (type={tn})")
        except:
            pass
except Exception as e:
    print(f"Materials error: {e}")

# Test output server
try:
    s_o, g_o = new_server('localhost', 10001, password=PASSWORD)
    print("Connected to Output OK")
except Exception as e:
    print(f"Output connection error: {e}")

print("\nDone.")
