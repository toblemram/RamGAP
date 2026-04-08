"""Test gotostages + calculate availability."""
from plxscripting.easy import new_server

pwd = "=~Z3xH<D51<Bn3BG"
s_i, g_i = new_server('localhost', 10000, password=pwd)
print("Connected to Input")

# Test gotostages
try:
    g_i.gotostages()
    print("gotostages() OK")
except Exception as e:
    print(f"gotostages() error: {e}")

# Check calculate availability
try:
    # Just check attribute presence without running
    print(f"calculate available: {hasattr(g_i, 'calculate')}")
except Exception as e:
    print(f"calculate check error: {e}")

# List materials
print("\nMaterials:")
try:
    for mat in g_i.Materials:
        try:
            name = mat.Identification.value
            tn = ""
            try:
                tn = mat.TypeName.value
            except:
                pass
            print(f"  {name} (type={tn})")
        except:
            pass
except Exception as e:
    print(f"Materials error: {e}")

# Try gotostages again after Materials (which may switch mode)
try:
    g_i.gotostages()
    print("\ngotostages() after Materials: OK")
except Exception as e:
    print(f"\ngotostages() after Materials error: {e}")

# Check calculate again
try:
    print(f"calculate still available: {hasattr(g_i, 'calculate')}")
except Exception as e:
    print(f"calculate recheck error: {e}")

print("\nDone.")
