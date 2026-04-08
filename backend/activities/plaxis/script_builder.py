# -*- coding: utf-8 -*-
"""
Plaxis Script Builder
=====================
Generates Python source code strings that PlaxisWorker executes
on the user's local machine using Plaxis's own python.exe.

Each function returns a complete, self-contained Python script that:
  1. Imports only stdlib + plxscripting (both available in Plaxis python.exe)
  2. Does the work against a locally-running Plaxis instance
  3. Prints a single JSON object to stdout as the result

The backend sends these scripts to the PlaxisWorker via the job queue.
PlaxisWorker never needs updating — all logic lives here.
"""

import json
from typing import Any, Dict, List, Optional


def _wrap(body: str) -> str:
    """Wrap script body with imports and JSON output."""
    return (
        "import json, sys\n"
        "from plxscripting.easy import new_server\n"
        "\n"
        "def main():\n"
        "    try:\n"
        + _indent(body, 8)
        + "\n"
        "    except Exception as exc:\n"
        "        print(json.dumps({'success': False, 'error': str(exc)}))\n"
        "        sys.exit(0)\n"
        "\n"
        "main()\n"
    )


def _indent(text: str, spaces: int) -> str:
    """Indent each line of *text* by *spaces* spaces."""
    prefix = ' ' * spaces
    return '\n'.join(prefix + line if line.strip() else line for line in text.splitlines())


def build_connect_script(host: str, port: int, password: str) -> str:
    """Script that connects and returns model info (structures + phases + geometry)."""
    body = f"""\
s_i, g_i = new_server({host!r}, {port}, password={password!r})

# Extract phases
phases = []
for ph in g_i.Phases:
    ct_id = None
    ct_name = ''
    try:
        ct_id = ph.DeformCalcType.value
    except Exception:
        pass
    try:
        ct_name = str(ph.DeformCalcType)
    except Exception:
        pass
    prev = ''
    try:
        prev = ph.PreviousPhase.Identification.value
    except Exception:
        pass
    phases.append({{
        'id': ph.Number.value,
        'number': ph.Number.value,
        'name': ph.Identification.value,
        'calc_type': ct_name,
        'calc_type_id': ct_id,
        'previous': prev,
    }})

# Extract structures
g_i.gotostructures()
structures = {{'plates': [], 'embedded_beams': [], 'node_to_node_anchors': [],
               'fixed_end_anchors': [], 'geogrids': []}}

if hasattr(g_i, 'Plates'):
    for plate in g_i.Plates:
        x1 = plate.Parent.First.x.value
        y1 = plate.Parent.First.y.value
        x2 = plate.Parent.Second.x.value
        y2 = plate.Parent.Second.y.value
        length = ((x2-x1)**2 + (y2-y1)**2)**0.5
        entry = {{'name': plate.Name.value, 'x1': x1, 'y1': y1,
                  'x2': x2, 'y2': y2, 'length': round(length, 2),
                  'type': 'plate', 'x': x1}}
        try:
            m = plate.Material
            mat = {{'name': m.Identification.value}}
            for p in ('EA1','EA2','EI','d','w','nu'):
                try: mat[p] = getattr(m, p).value
                except: pass
            entry['material'] = mat
        except:
            pass
        structures['plates'].append(entry)

if hasattr(g_i, 'EmbeddedBeamRows'):
    for ebr in g_i.EmbeddedBeamRows:
        x1 = ebr.Parent.First.x.value
        y1 = ebr.Parent.First.y.value
        x2 = ebr.Parent.Second.x.value
        y2 = ebr.Parent.Second.y.value
        length = ((x2-x1)**2 + (y2-y1)**2)**0.5
        structures['embedded_beams'].append({{
            'name': ebr.Name.value, 'x1': x1, 'y1': y1,
            'x2': x2, 'y2': y2, 'length': round(length, 2),
        }})

if hasattr(g_i, 'NodeToNodeAnchors'):
    for anc in g_i.NodeToNodeAnchors:
        x1 = anc.Parent.First.x.value
        y1 = anc.Parent.First.y.value
        x2 = anc.Parent.Second.x.value
        y2 = anc.Parent.Second.y.value
        length = ((x2-x1)**2 + (y2-y1)**2)**0.5
        entry = {{'name': anc.Name.value, 'type': 'node_to_node_anchor',
                  'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                  'length': round(length, 2)}}
        try:
            m = anc.Material
            mat = {{'name': m.Identification.value}}
            for p in ('EA','Lspacing'):
                try: mat[p] = getattr(m, p).value
                except: pass
            entry['material'] = mat
        except:
            pass
        structures['node_to_node_anchors'].append(entry)

if hasattr(g_i, 'FixedEndAnchors'):
    for fea in g_i.FixedEndAnchors:
        x = fea.Parent.x.value
        y = fea.Parent.y.value
        entry = {{'name': fea.Name.value, 'type': 'fixed_end_anchor',
                  'x': x, 'y': y}}
        try:
            m = fea.Material
            mat = {{'name': m.Identification.value}}
            for p in ('EA','Lspacing'):
                try: mat[p] = getattr(m, p).value
                except: pass
            entry['material'] = mat
        except:
            pass
        structures['fixed_end_anchors'].append(entry)

# Extract geometry (soil layers, water head, model extents)
geometry = {{'soil_layers': [], 'water_head': None,
            'xmin': None, 'xmax': None, 'ymin': None, 'ymax': None}}
try:
    g_i.gotosoil()
    for bh in g_i.Boreholes:
        try:
            geometry['water_head'] = bh.Head.value
        except:
            pass
        break
except:
    pass

try:
    g_i.gotosoil()
    for bh in g_i.Boreholes:
        layers_raw = []
        for sl in bh.Soillayers:
            top = sl.Top.value
            bot = sl.Bottom.value
            mat_name = ''
            try:
                mat_name = sl.Soil.Identification.value
            except:
                pass
            layers_raw.append({{'name': f'Layer {{len(layers_raw)+1}}',
                              'material': mat_name, 'top': top, 'bottom': bot}})
        geometry['soil_layers'] = layers_raw
        break
except:
    pass

try:
    geometry['xmin'] = g_i.SoilContour.xmin.value
    geometry['xmax'] = g_i.SoilContour.xmax.value
    geometry['ymin'] = g_i.SoilContour.ymin.value
    geometry['ymax'] = g_i.SoilContour.ymax.value
except:
    pass

print(json.dumps({{
    'success': True,
    'structures': structures,
    'phases': phases,
    'geometry': geometry,
}}))"""
    return _wrap(body)


def build_run_script(
    host: str, port: int, password: str,
    output_port: Optional[int], output_password: Optional[str],
    job: Dict[str, Any],
) -> str:
    """Script that runs a full extraction (capacity, MSF, displacement)."""
    job_json = json.dumps(job)
    body = f"""\
import json as _json
job = _json.loads({job_json!r})

s_i, g_i = new_server({host!r}, {port}, password={password!r})

# Open Output
output_port = {output_port!r}
output_password = {output_password!r} or {password!r}
if output_port:
    s_o, g_o = new_server({host!r}, int(output_port), password=output_password)
else:
    port_out = g_i.view(g_i.Phases[0])
    s_o, g_o = new_server({host!r}, port_out, password=output_password)

# Resolve structures by name
selected = {{}}
_MAP = {{'plates': 'Plates', 'embedded_beams': 'EmbeddedBeamRows',
         'node_to_node_anchors': 'NodeToNodeAnchors',
         'fixed_end_anchors': 'FixedEndAnchors', 'geogrids': 'Geogrids'}}
for job_key, plaxis_attr in _MAP.items():
    selected[job_key] = []
    names = job.get('structures', {{}}).get(job_key, [])
    if names and hasattr(g_o, plaxis_attr):
        for obj in getattr(g_o, plaxis_attr):
            if obj.Name.value in names:
                selected[job_key].append(obj)

# Resolve phases by name
def _resolve_phases(phase_names):
    resolved = []
    for ph in g_o.Phases:
        pid = ph.Identification.value
        for target in phase_names:
            if pid.startswith(target):
                resolved.append(ph)
                break
    return resolved

analysis = job.get('analysis', {{}})
results = {{'success': False, 'capacity': {{}}, 'msf': {{}}, 'displacement': {{}}}}

# MSF
if analysis.get('msf', {{}}).get('enabled'):
    msf_phases = _resolve_phases(analysis['msf']['phases'])
    msf_results = {{}}
    for ph in msf_phases:
        val = None
        for accessor in (
            lambda p=ph: p.Reached.SumMsf.value,
            lambda p=ph: p.Reached.MsfReached.value,
            lambda p=ph: p.Reached.Msf.value,
        ):
            try:
                val = accessor()
                break
            except:
                pass
        msf_results[ph.Identification.value] = val
    results['msf'] = msf_results

# Capacity
if analysis.get('capacity_check', {{}}).get('enabled'):
    cap_phases = _resolve_phases(analysis['capacity_check']['phases'])
    cap_results = {{}}
    for stype, objs in selected.items():
        if not objs:
            continue
        cap_results[stype] = {{}}
        for obj in objs:
            cap_results[stype][obj.Name.value] = {{}}
            for ph in cap_phases:
                forces = {{}}
                rt = None
                if hasattr(g_o.ResultTypes, 'Plate'):
                    rt = g_o.ResultTypes.Plate
                for fname, candidates in [('Nx', ['Nx2D','N','Nx']), ('Q', ['Q2D','Q','Qx']), ('M', ['M2D','M','Mx'])]:
                    rtype = None
                    if rt:
                        for c in candidates:
                            if hasattr(rt, c):
                                rtype = getattr(rt, c)
                                break
                    if rtype:
                        try:
                            vals = g_o.getresults(obj, ph, rtype, 'node')
                            forces[fname] = max(abs(v) for v in vals) if vals else None
                        except:
                            try:
                                vals = g_o.getresults(ph, rtype, 'node', obj)
                                forces[fname] = max(abs(v) for v in vals) if vals else None
                            except:
                                forces[fname] = None
                cap_results[stype][obj.Name.value][ph.Identification.value] = forces
    results['capacity'] = cap_results

# Displacement
if analysis.get('displacement', {{}}).get('enabled'):
    disp_phases = _resolve_phases(analysis['displacement']['phases'])
    component = analysis['displacement'].get('component', 'Ux')
    disp_results = {{}}
    for stype, objs in selected.items():
        if not objs:
            continue
        disp_results[stype] = {{}}
        rt = None
        if hasattr(g_o.ResultTypes, 'Plate'):
            rt = g_o.ResultTypes.Plate
        rtype = None
        if rt:
            for c in [component, component + '2D']:
                if hasattr(rt, c):
                    rtype = getattr(rt, c)
                    break
        if not rtype:
            continue
        for obj in objs:
            disp_results[stype][obj.Name.value] = {{}}
            for ph in disp_phases:
                val = None
                try:
                    vals = g_o.getresults(obj, ph, rtype, 'node')
                    val = max(abs(v) for v in vals) if vals else None
                except:
                    try:
                        vals = g_o.getresults(ph, rtype, 'node', obj)
                        val = max(abs(v) for v in vals) if vals else None
                    except:
                        pass
                disp_results[stype][obj.Name.value][ph.Identification.value] = val
    results['displacement'] = disp_results

results['success'] = True
print(json.dumps(results))"""
    return _wrap(body)


def build_parametric_script(
    host: str, port: int, password: str,
    output_port: Optional[int], output_password: Optional[str],
    ks_soil: str, plate: str, su: float,
    depth: Optional[float],
    fos_phase: Optional[str], disp_phase: Optional[str], cap_phase: Optional[str],
) -> str:
    """Script that runs one parametric iteration."""
    body = f"""\
s_i, g_i = new_server({host!r}, {port}, password={password!r})

# Find and modify KS soil Su
material = None
for mat in g_i.Materials:
    try:
        if mat.Identification.value == {ks_soil!r}:
            material = mat
            break
    except:
        pass
if not material:
    print(json.dumps({{'success': False, 'error': 'Material not found: {ks_soil}'}}))
    sys.exit(0)

su_set = False
for attr in ('sURef', 'SuRef', 'su_ref'):
    if hasattr(material, attr):
        getattr(material, attr).set({su})
        su_set = True
        break
if not su_set:
    try:
        material.setproperties("sURef", {su})
    except:
        print(json.dumps({{'success': False, 'error': 'Could not set Su on material'}}))
        sys.exit(0)
"""

    if depth is not None:
        body += f"""
# Adjust plate depth
plate_obj = None
for p in g_i.Plates:
    try:
        if p.Name.value == {plate!r}:
            plate_obj = p
            break
    except:
        pass
if plate_obj:
    line = plate_obj.Parent.value
    p1 = line.First.value
    p2 = line.Second.value
    if p1.y.value < p2.y.value:
        p1.y.set({depth})
    else:
        p2.y.set({depth})
"""

    body += f"""
# Run calculation
try:
    g_i.calculate()
except Exception as exc:
    print(json.dumps({{'success': False, 'error': f'Calculation failed: {{exc}}'}}))
    sys.exit(0)

# Connect to output and extract results
result = {{'success': False, 'msf': None, 'ux_max': None, 'm_max': None}}
g_o = None
output_port = {output_port!r}
output_password = {output_password!r} or {password!r}
if output_port:
    try:
        _s_o, g_o = new_server({host!r}, int(output_port), password=output_password)
    except:
        pass

if g_o is None:
    result['success'] = True
    result['error'] = 'Calc ran but no Output connection'
    print(json.dumps(result))
    sys.exit(0)

def _find_phase(g, name):
    for ph in g.Phases:
        if ph.Identification.value == name:
            return ph
    return None

def _find_plate(g, name):
    for p in g.Plates:
        if p.Name.value == name:
            return p
    return None

fos_phase_name = {fos_phase!r}
disp_phase_name = {disp_phase!r}
cap_phase_name = {cap_phase!r}

if fos_phase_name:
    o_fos = _find_phase(g_o, fos_phase_name)
    if o_fos:
        for acc in (
            lambda: o_fos.Reached.SumMsf.value,
            lambda: o_fos.Reached.MsfReached.value,
            lambda: o_fos.Reached.Msf.value,
        ):
            try:
                result['msf'] = acc()
                break
            except:
                pass

o_plate = _find_plate(g_o, {plate!r})

if o_plate and disp_phase_name:
    o_disp = _find_phase(g_o, disp_phase_name)
    if o_disp:
        rt = None
        if hasattr(g_o.ResultTypes, 'Plate'):
            for attr in ('Ux', 'Ux2D'):
                if hasattr(g_o.ResultTypes.Plate, attr):
                    rt = getattr(g_o.ResultTypes.Plate, attr)
                    break
        if rt:
            for call_fn in (
                lambda: g_o.getresults(o_plate, o_disp, rt, 'node'),
                lambda: g_o.getresults(o_disp, rt, 'node', o_plate),
            ):
                try:
                    vals = call_fn()
                    if vals:
                        result['ux_max'] = max(abs(v) for v in vals)
                    break
                except:
                    pass

if o_plate and cap_phase_name:
    o_cap = _find_phase(g_o, cap_phase_name)
    if o_cap:
        rt = None
        if hasattr(g_o.ResultTypes, 'Plate'):
            for attr in ('M2D', 'M', 'Mx'):
                if hasattr(g_o.ResultTypes.Plate, attr):
                    rt = getattr(g_o.ResultTypes.Plate, attr)
                    break
        if rt:
            for call_fn in (
                lambda: g_o.getresults(o_plate, o_cap, rt, 'node'),
                lambda: g_o.getresults(o_cap, rt, 'node', o_plate),
            ):
                try:
                    vals = call_fn()
                    if vals:
                        result['m_max'] = max(abs(v) for v in vals)
                    break
                except:
                    pass

result['success'] = True
print(json.dumps(result))"""
    return _wrap(body)


def build_water_sensitivity_script(
    host: str, port: int, password: str,
    output_port: Optional[int], output_password: Optional[str],
    water_level: float, plate: Optional[str],
    fos_phase: Optional[str], disp_phase: Optional[str], cap_phase: Optional[str],
) -> str:
    """Script that runs one water-level sensitivity iteration."""
    body = f"""\
s_i, g_i = new_server({host!r}, {port}, password={password!r})

# Set water head on all boreholes
g_i.gotosoil()
for bh in g_i.Boreholes:
    bh.Head.set({water_level})

# Run calculation
try:
    g_i.calculate()
except Exception as exc:
    print(json.dumps({{'success': False, 'error': f'Calculation failed: {{exc}}'}}))
    sys.exit(0)

# Connect to output
result = {{'success': False, 'water_level': {water_level}, 'msf': None, 'ux_max': None, 'm_max': None}}
g_o = None
output_port = {output_port!r}
output_password = {output_password!r} or {password!r}
if output_port:
    try:
        _s_o, g_o = new_server({host!r}, int(output_port), password=output_password)
    except:
        pass

if g_o is None:
    result['success'] = True
    result['error'] = 'Calc ran but no Output connection'
    print(json.dumps(result))
    sys.exit(0)

def _find_phase(g, name):
    for ph in g.Phases:
        if ph.Identification.value == name:
            return ph
    return None

def _find_plate(g, name):
    for p in g.Plates:
        if p.Name.value == name:
            return p
    return None

fos_phase_name = {fos_phase!r}
disp_phase_name = {disp_phase!r}
cap_phase_name = {cap_phase!r}

if fos_phase_name:
    o_fos = _find_phase(g_o, fos_phase_name)
    if o_fos:
        for acc in (
            lambda: o_fos.Reached.SumMsf.value,
            lambda: o_fos.Reached.MsfReached.value,
            lambda: o_fos.Reached.Msf.value,
        ):
            try:
                result['msf'] = acc()
                break
            except:
                pass

o_plate = _find_plate(g_o, {plate!r}) if {plate!r} else None

if o_plate and disp_phase_name:
    o_disp = _find_phase(g_o, disp_phase_name)
    if o_disp:
        rt = None
        if hasattr(g_o.ResultTypes, 'Plate'):
            for attr in ('Ux', 'Ux2D'):
                if hasattr(g_o.ResultTypes.Plate, attr):
                    rt = getattr(g_o.ResultTypes.Plate, attr)
                    break
        if rt:
            for call_fn in (
                lambda: g_o.getresults(o_plate, o_disp, rt, 'node'),
                lambda: g_o.getresults(o_disp, rt, 'node', o_plate),
            ):
                try:
                    vals = call_fn()
                    if vals:
                        result['ux_max'] = max(abs(v) for v in vals)
                    break
                except:
                    pass

if o_plate and cap_phase_name:
    o_cap = _find_phase(g_o, cap_phase_name)
    if o_cap:
        rt = None
        if hasattr(g_o.ResultTypes, 'Plate'):
            for attr in ('M2D', 'M', 'Mx'):
                if hasattr(g_o.ResultTypes.Plate, attr):
                    rt = getattr(g_o.ResultTypes.Plate, attr)
                    break
        if rt:
            for call_fn in (
                lambda: g_o.getresults(o_plate, o_cap, rt, 'node'),
                lambda: g_o.getresults(o_cap, rt, 'node', o_plate),
            ):
                try:
                    vals = call_fn()
                    if vals:
                        result['m_max'] = max(abs(v) for v in vals)
                    break
                except:
                    pass

result['success'] = True
print(json.dumps(result))"""
    return _wrap(body)


# ---------------------------------------------------------------------------
# Sensitivity analysis script
# ---------------------------------------------------------------------------

def build_sensitivity_script(
    host: str, port: int, password: str,
    output_port: Optional[int], output_password: Optional[str],
    param_type: str, param_value: float,
    soil_name: Optional[str], plate: Optional[str],
    fos_phase: Optional[str], disp_phase: Optional[str], cap_phase: Optional[str],
) -> str:
    """Script that runs one sensitivity iteration.

    *param_type* is one of: 'su', 'phi', 'cohesion', 'gamma', 'eref',
    'water_level', 'plate_depth'.
    *param_value* is the value to set for the given parameter.
    *soil_name* is the material name in Plaxis to modify (not needed for
    water_level/plate_depth).
    """
    # Map param_type to Plaxis material attribute names (multiple candidates)
    _ATTR_MAP: Dict[str, List[str]] = {
        'su':       ['sURef', 'SuRef', 'su_ref', 'cRef', 'cref'],
        'phi':      ['phi', 'phiRef', 'phi0'],
        'cohesion': ['cRef', 'cref', 'Cohesion', 'cRefPrime'],
        'gamma':    ['gammaUnsat', 'gammaSat', 'gamma'],
        'eref':     ['Eref', 'E50ref', 'EoedRef', 'EurRef', 'Gref'],
    }

    body = f"""\
s_i, g_i = new_server({host!r}, {port}, password={password!r})

param_type = {param_type!r}
param_value = {param_value}
"""
    if param_type == 'water_level':
        body += f"""\
# Set water head on all boreholes
g_i.gotosoil()
for bh in g_i.Boreholes:
    bh.Head.set(param_value)
"""
    elif param_type == 'plate_depth':
        body += f"""\
# Adjust plate depth
plate_obj = None
for p in g_i.Plates:
    try:
        if p.Name.value == {plate!r}:
            plate_obj = p
            break
    except:
        pass
if plate_obj:
    line = plate_obj.Parent.value
    p1 = line.First.value
    p2 = line.Second.value
    if p1.y.value < p2.y.value:
        p1.y.set(param_value)
    else:
        p2.y.set(param_value)
"""
    else:
        attrs = _ATTR_MAP.get(param_type, [param_type])
        body += f"""\
# Modify soil parameter
material = None
for mat in g_i.Materials:
    try:
        if mat.Identification.value == {soil_name!r}:
            material = mat
            break
    except:
        pass
if not material:
    print(json.dumps({{'success': False, 'error': 'Material not found: {soil_name}'}}))
    sys.exit(0)

attr_set = False
for attr in {attrs!r}:
    if hasattr(material, attr):
        try:
            getattr(material, attr).set(param_value)
            attr_set = True
            break
        except:
            pass
if not attr_set:
    try:
        material.setproperties({attrs[0]!r}, param_value)
    except:
        print(json.dumps({{'success': False, 'error': 'Could not set {{param_type}} on material'}}))
        sys.exit(0)
"""

    body += f"""\
# Run calculation
try:
    g_i.calculate()
except Exception as exc:
    print(json.dumps({{'success': False, 'error': f'Calculation failed: {{exc}}'}}))
    sys.exit(0)

# Connect to output and extract results
result = {{'success': False, 'param_type': param_type, 'param_value': param_value,
           'msf': None, 'ux_max': None, 'm_max': None, 'q_max': None, 'n_max': None}}
g_o = None
output_port = {output_port!r}
output_password = {output_password!r} or {password!r}
if output_port:
    try:
        _s_o, g_o = new_server({host!r}, int(output_port), password=output_password)
    except:
        pass

if g_o is None:
    result['success'] = True
    result['error'] = 'Calc ran but no Output connection'
    print(json.dumps(result))
    sys.exit(0)

def _find_phase(g, name):
    for ph in g.Phases:
        if ph.Identification.value == name:
            return ph
    return None

def _find_plate(g, name):
    for p in g.Plates:
        if p.Name.value == name:
            return p
    return None

fos_phase_name = {fos_phase!r}
disp_phase_name = {disp_phase!r}
cap_phase_name = {cap_phase!r}

# MSF / FoS
if fos_phase_name:
    o_fos = _find_phase(g_o, fos_phase_name)
    if o_fos:
        for acc in (
            lambda: o_fos.Reached.SumMsf.value,
            lambda: o_fos.Reached.MsfReached.value,
            lambda: o_fos.Reached.Msf.value,
        ):
            try:
                result['msf'] = acc()
                break
            except:
                pass

o_plate = _find_plate(g_o, {plate!r}) if {plate!r} else None

# Displacement
if o_plate and disp_phase_name:
    o_disp = _find_phase(g_o, disp_phase_name)
    if o_disp:
        rt = None
        if hasattr(g_o.ResultTypes, 'Plate'):
            for attr in ('Ux', 'Ux2D'):
                if hasattr(g_o.ResultTypes.Plate, attr):
                    rt = getattr(g_o.ResultTypes.Plate, attr)
                    break
        if rt:
            for call_fn in (
                lambda: g_o.getresults(o_plate, o_disp, rt, 'node'),
                lambda: g_o.getresults(o_disp, rt, 'node', o_plate),
            ):
                try:
                    vals = call_fn()
                    if vals:
                        result['ux_max'] = max(abs(v) for v in vals)
                    break
                except:
                    pass

# Forces (moment, shear, axial)
if o_plate and cap_phase_name:
    o_cap = _find_phase(g_o, cap_phase_name)
    if o_cap and hasattr(g_o.ResultTypes, 'Plate'):
        rt_plate = g_o.ResultTypes.Plate
        for force_key, candidates in [('m_max', ['M2D','M','Mx']),
                                       ('q_max', ['Q2D','Q','Qx']),
                                       ('n_max', ['Nx2D','N','Nx'])]:
            rtype = None
            for c in candidates:
                if hasattr(rt_plate, c):
                    rtype = getattr(rt_plate, c)
                    break
            if rtype:
                for call_fn in (
                    lambda rt=rtype: g_o.getresults(o_plate, o_cap, rt, 'node'),
                    lambda rt=rtype: g_o.getresults(o_cap, rt, 'node', o_plate),
                ):
                    try:
                        vals = call_fn()
                        if vals:
                            result[force_key] = max(abs(v) for v in vals)
                        break
                    except:
                        pass

result['success'] = True
print(json.dumps(result))"""
    return _wrap(body)


# ---------------------------------------------------------------------------
# Agent scripts (GAPI)
# ---------------------------------------------------------------------------

def build_agent_test_script(host: str, port: int, password: str) -> str:
    """Script that tests the Plaxis connection and returns project name."""
    body = f"""\
s_i, g_i = new_server({host!r}, {port}, password={password!r})
project_name = ''
try:
    project_name = g_i.Project.Name.value
except Exception:
    project_name = '(tilkoblet)'
print(json.dumps({{'success': True, 'project': project_name}}))"""
    return _wrap(body)


def build_agent_exec_script(
    host: str,
    port: int,
    password: str,
    output_port: int | None,
    output_password: str | None,
    agent_code: str,
) -> str:
    """
    Wrap agent-generated code into a self-contained script for PlaxisWorker.

    The agent code expects variables ``g``, ``s``, ``g_o``, ``s_o`` to exist.
    This wrapper creates the Plaxis connection, runs the agent code in an
    exec() call, captures stdout, and returns the result as JSON.
    """
    import base64
    encoded = base64.b64encode(agent_code.encode("utf-8")).decode("ascii")

    out_port = output_port or (port + 1)
    out_pwd = output_password or password

    body = f"""\
import base64, io, contextlib

s, g = new_server({host!r}, {port}, password={password!r})
s_o, g_o = new_server({host!r}, {out_port}, password={out_pwd!r})

_code = base64.b64decode('{encoded}').decode('utf-8')
_namespace = {{'g': g, 's': s, 'g_o': g_o, 's_o': s_o}}
_buf = io.StringIO()

try:
    with contextlib.redirect_stdout(_buf):
        exec(_code, _namespace)
    _output = _buf.getvalue()
    print(json.dumps({{'success': True, 'output': _output}}))
except Exception as _exc:
    _output = _buf.getvalue()
    print(json.dumps({{'success': False, 'output': _output, 'error': str(_exc)}}))"""
    return _wrap(body)
