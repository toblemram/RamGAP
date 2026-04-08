"""Test exact parametric workflow against live Plaxis model."""
from plxscripting.easy import new_server
import json

pwd = "=~Z3xH<D51<Bn3BG"
s_i, g_i = new_server('localhost', 10000, password=pwd)
print("Connected")

# Step 1: Check current state - what mode are we in?
print("\n--- Step 1: Checking model state ---")
try:
    phases = list(g_i.Phases)
    print(f"Phases: {len(phases)}")
except Exception as e:
    print(f"Phases check: {e}")

# Step 2: Check mesh status
print("\n--- Step 2: Checking mesh ---")
try:
    g_i.gotomesh()
    print("gotomesh() OK")
    # Check if mesh exists
    try:
        nnodes = g_i.MeshNodes
        print(f"Mesh nodes accessible")
    except Exception as e:
        print(f"Mesh nodes check: {e}")
except Exception as e:
    print(f"gotomesh() error: {e}")

# Step 3: Try gotostages and calculate without modifying anything
print("\n--- Step 3: gotostages + calculate (no changes) ---")
try:
    g_i.gotostages()
    print("gotostages() OK")
except Exception as e:
    print(f"gotostages() error: {e}")

try:
    g_i.calculate()
    print("calculate() OK")
except Exception as e:
    print(f"calculate() error: {e}")

# Step 4: Now try the full parametric workflow
print("\n--- Step 4: Full parametric workflow ---")

# 4a: Find material 
print("Finding KS_Su material...")
material = None
for mat in g_i.Materials:
    try:
        if mat.Identification.value == 'KS_Su':
            material = mat
            print(f"  Found: {mat.Identification.value}")
            break
    except:
        pass

if material:
    # 4b: Check Su attributes
    for attr in ('sURef', 'SuRef', 'su_ref', 'cRef', 'cref'):
        if hasattr(material, attr):
            try:
                val = getattr(material, attr).value
                print(f"  Current {attr} = {val}")
            except:
                print(f"  Has {attr} but can't read value")

    # 4c: Try to set Su
    print("Setting Su to 15.0...")
    su_set = False
    for attr in ('sURef', 'SuRef', 'su_ref'):
        if hasattr(material, attr):
            try:
                getattr(material, attr).set(15.0)
                su_set = True
                print(f"  Set {attr} = 15.0 OK")
                break
            except Exception as e:
                print(f"  Set {attr} failed: {e}")
    if not su_set:
        try:
            material.setproperties("sURef", 15.0)
            print("  setproperties OK")
        except Exception as e:
            print(f"  setproperties failed: {e}")

# 4d: Now try calculate
print("\n--- Step 5: Calculate after material change ---")
try:
    g_i.gotostages()
    print("gotostages() OK")
except Exception as e:
    print(f"gotostages() error: {e}")

try:
    g_i.calculate()
    print("calculate() OK!")
except Exception as e:
    print(f"calculate() error: {e}")
    
    # Try mesh regeneration first
    print("\nTrying: gotomesh -> mesh -> gotostages -> calculate ...")
    try:
        g_i.gotomesh()
        print("  gotomesh() OK")
        g_i.mesh(0.06)
        print("  mesh() OK")
        g_i.gotostages()
        print("  gotostages() OK")
        g_i.calculate()
        print("  calculate() OK!")
    except Exception as e2:
        print(f"  Still failed: {e2}")

print("\nDone.")
