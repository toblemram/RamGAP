"""Test different passwords against Plaxis servers."""
from plxscripting.easy import new_server

PASSWORDS = [
    r"~Z3xH<D51<Bn3BG",
    "~Z3xH<D51<Bn3BG",
    "",
    "password",
]

for pwd in PASSWORDS:
    print(f"\nTrying password: {pwd!r}")
    for port in [10000, 10001]:
        try:
            s, g = new_server('localhost', port, password=pwd)
            phases = list(g.Phases)
            print(f"  Port {port}: OK! {len(phases)} phases")
        except Exception as e:
            err = str(e)[:80]
            print(f"  Port {port}: FAIL - {err}")
