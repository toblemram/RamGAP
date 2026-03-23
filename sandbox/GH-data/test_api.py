"""
Quick API test — creates a new modeling activity and uploads GH-data files.
Run from any directory: python sandbox/GH-data/test_api.py
"""
import json
import pathlib
import requests

BASE = "http://localhost:5050"
GH   = pathlib.Path(__file__).parent   # sandbox/GH-data/

# ---------------------------------------------------------------------------
# 1. Create new modeling activity
# ---------------------------------------------------------------------------
print("=== 1. Create activity ===")
r = requests.post(f"{BASE}/api/modeling/activities", json={
    "project_id": 2,
    "name": "GH Test — RetainingWall b476858f",
    "username": "TBLM",
})
print(f"  Status: {r.status_code}")
if r.status_code not in (200, 201):
    print("  ERROR:", r.text); raise SystemExit(1)

act = r.json()["activity"]
print(json.dumps(act, indent=2))
aid = act["id"]
print(f"  --> activity_id = {aid}")

# ---------------------------------------------------------------------------
# 2. Upload Excel (segment_000.xlsx)
# ---------------------------------------------------------------------------
print("\n=== 2. Upload Excel ===")
xlsx = GH / "segment_000.xlsx"
with xlsx.open("rb") as fh:
    r2 = requests.post(
        f"{BASE}/api/modeling/activities/{aid}/upload/excel",
        files={"file": (xlsx.name, fh,
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet")},
    )
print(f"  Status: {r2.status_code}")
d2 = r2.json()
print(f"  success={d2.get('success')}  blob={d2.get('blob_name')}  error={d2.get('error','')}")

# ---------------------------------------------------------------------------
# 3. Upload GH results (report + summary)
# ---------------------------------------------------------------------------
print("\n=== 3. Upload results ===")
report_path  = GH / "run-report.json"
summary_path = GH / "run-summary.md"

files = {
    "report": ("run-report.json", report_path.read_bytes(), "application/json"),
}
if summary_path.exists():
    files["summary"] = ("run-summary.md", summary_path.read_bytes(), "text/markdown")

r3 = requests.post(
    f"{BASE}/api/modeling/activities/{aid}/upload/results",
    files=files,
)
print(f"  Status: {r3.status_code}")
print(json.dumps(r3.json(), indent=2))

# ---------------------------------------------------------------------------
# 4. Verify — fetch the activity back
# ---------------------------------------------------------------------------
print("\n=== 4. Verify activity ===")
r4 = requests.get(f"{BASE}/api/modeling/activities/{aid}")
print(f"  Status: {r4.status_code}")
print(json.dumps(r4.json(), indent=2))
