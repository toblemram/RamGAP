"""Test mesh generation."""
from plxscripting.easy import new_server

pwd = "=~Z3xH<D51<Bn3BG"
s_i, g_i = new_server('localhost', 10000, password=pwd)
print("Connected")

# Go to mesh mode
g_i.gotomesh()
print("In mesh mode")

# Try different mesh generation approaches
approaches = [
    ("g_i.mesh(0.06)", lambda: g_i.mesh(0.06)),
    ("g_i.mesh()", lambda: g_i.mesh()),
    ("g_i.mesh(0.1)", lambda: g_i.mesh(0.1)),
    ("g_i.meshd(0.06)", lambda: g_i.meshd(0.06)),
    ("g_i.generate()", lambda: g_i.generate()),
]

for desc, fn in approaches:
    try:
        print(f"\nTrying {desc}...")
        fn()
        print(f"  OK!")
        break
    except Exception as e:
        err = str(e)[:150]
        print(f"  Error: {err}")

# Check if mesh now exists
print("\nChecking mesh after generation...")
try:
    g_i.gotostages()
    print("gotostages() OK")
    g_i.calculate()
    print("calculate() OK - mesh is valid!")
except Exception as e:
    print(f"Still no mesh: {e}")
