"""Test with correct password including leading =."""
from plxscripting.easy import new_server

pwd = "=~Z3xH<D51<Bn3BG"
print(f"Password: {pwd!r}")

for port in [10000, 10001]:
    try:
        s, g = new_server('localhost', port, password=pwd)
        phases = list(g.Phases)
        print(f"  Port {port}: OK! {len(phases)} phases")
        for ph in phases:
            print(f"    {ph.Identification.value} ({ph.DeformCalcType})")
    except Exception as e:
        err = str(e)[:100]
        print(f"  Port {port}: FAIL - {err}")
