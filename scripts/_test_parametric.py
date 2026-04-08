import json, sys
from plxscripting.easy import new_server

def main():
    try:
        s_i, g_i = new_server('localhost', 10000, password='=~Z3xH<D51<Bn3BG')

        # Find and modify KS soil strength parameter
        material = None
        for mat in g_i.Materials:
            try:
                if mat.Identification.value == 'Fyllmasser':
                    material = mat
                    break
            except:
                pass
        if not material:
            print(json.dumps({'success': False, 'error': 'Material not found: Fyllmasser'}))
            sys.exit(0)

        # Try Su first (undrained), then cRef (drained cohesion)
        su_set = False
        _attr_used = None
        for attr in ('sURef', 'SuRef', 'su_ref', 'cRef', 'cref'):
            if hasattr(material, attr):
                try:
                    getattr(material, attr).set(10.0)
                    su_set = True
                    _attr_used = attr
                    break
                except:
                    pass
        if not su_set:
            for prop_name in ('sURef', 'cRef'):
                try:
                    material.setproperties(prop_name, 10.0)
                    su_set = True
                    _attr_used = prop_name
                    break
                except:
                    pass
        if not su_set:
            print(json.dumps({'success': False, 'error': 'Material has no Su or cRef: Fyllmasser'}))
            sys.exit(0)

        # Adjust plate depth
        plate_obj = None
        for p in g_i.Plates:
            try:
                if p.Name.value == 'Spunt_venstre':
                    plate_obj = p
                    break
            except:
                pass
        if plate_obj:
            line = plate_obj.Parent.value
            p1 = line.First.value
            p2 = line.Second.value
            if p1.y.value < p2.y.value:
                p1.y.set(-8.0)
            else:
                p2.y.set(-8.0)

        # Ensure mesh is generated
        try:
            g_i.gotomesh()
            g_i.mesh(0.06)
        except:
            pass

        # Mark all phases for recalculation and calculate one by one
        g_i.gotostages()
        for _ph in g_i.Phases:
            try:
                _ph.ShouldCalculate = True
            except:
                pass
        _calc_errors = []
        for _ph in g_i.Phases:
            try:
                _r = g_i.calculate(_ph)
                if isinstance(_r, str) and 'failed' in _r.lower():
                    _calc_errors.append(_ph.Identification.value)
            except Exception as _e:
                _calc_errors.append(_ph.Identification.value)

        # Connect to output and extract results
        result = {'success': False, 'msf': None, 'ux_max': None, 'm_max': None}
        g_o = None
        output_port = 10001
        output_password = '=~Z3xH<D51<Bn3BG' or '=~Z3xH<D51<Bn3BG'
        if output_port:
            try:
                _s_o, g_o = new_server('localhost', int(output_port), password=output_password)
            except:
                pass

        if g_o is None:
            result['success'] = True
            result['error'] = 'Calc ran but no Output connection'
            print(json.dumps(result))
            sys.exit(0)

        def _find_phase(g, name):
            for ph in g.Phases:
                ph_name = ph.Identification.value
                if ph_name == name or ph_name.startswith(name + ' [') or ph_name.startswith(name + '['):
                    return ph
            return None

        def _find_plate(g, name):
            for p in g.Plates:
                p_name = p.Name.value
                if p_name == name or p_name.startswith(name + ' [') or p_name.startswith(name + '['):
                    return p
            return None

        fos_phase_name = '0.5.1 FoS'
        disp_phase_name = '0.5.2 Utpumping vann'
        cap_phase_name = '0.5.2 Utpumping vann'

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

        o_plate = _find_plate(g_o, 'Spunt_venstre')

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
        print(json.dumps(result))
    except Exception as exc:
        print(json.dumps({'success': False, 'error': str(exc)}))
        sys.exit(0)

main()
