"""Restore plates and recalculate all phases."""
import time
from plxscripting.easy import new_server

s, g = new_server('localhost', 10000, password='=~Z3xH<D51<Bn3BG')

# 1. Verify plates are restored
g.gotostructures()
for p in g.Plates:
    name = p.Name.value
    pt1, pt2 = p.Parent.First, p.Parent.Second
    length = abs(pt1.y.value - pt2.y.value)
    print(f"{name}: ({pt1.x.value}, {pt1.y.value}) -> ({pt2.x.value}, {pt2.y.value})  L={length:.3f}")

# 2. Regenerate mesh
print("\nGenerating mesh...")
g.gotomesh()
g.mesh(0.06)
print("Mesh OK")

# 3. Calculate all phases (skip orphaned Phase_9/10/11)
g.gotostages()
for ph in g.Phases:
    name = ph.Identification.value
    if name.startswith("Phase_"):
        ph.ShouldCalculate = False

print("\nCalculating all phases (this may take a few minutes)...")
t0 = time.time()
g.calculate()
elapsed = time.time() - t0
print(f"Done in {elapsed:.0f}s")

# 4. Print results
print("\n=== RESULTS ===")
for ph in g.Phases:
    name = ph.Identification.value
    cr = ph.CalculationResult.value
    msf_str = ""
    if ph.DeformCalcType.value == 7:  # Safety
        try:
            msf_str = f", SumMsf={ph.Reached.SumMsf.value:.4f}"
        except:
            try:
                msf_str = f", SumMsf={ph.SumMsf.value:.4f}"
            except:
                msf_str = ", SumMsf=N/A"
    print(f"  {name}: CalcResult={cr}{msf_str}")
