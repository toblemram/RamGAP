"""
Pure-Python calculation engine for tørrmur dimensjonering.

Reimplements the formulas from the Excel workbook
"Dimensjonering av tørrmurer iht V220_rev 1.xltm" (sheet BEREGNING).

All cell references in comments refer to the original workbook.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TorrmurInput:
    """All user-supplied inputs (mirrors the INPUT_SECTIONS cells)."""
    # Laster
    qk: float = 0.0           # B4 - Nyttelast bak mur [kPa]
    qQk: float = 0.0          # B5 - Boggilast bak mur [kPa]
    gammaQ_nyttelast: float = 1.3   # B6 - Lastfaktor nyttelast
    gammaQ_boggilast: float = 1.15  # C6 - Lastfaktor boggilast
    inv_tan_beta: float = 0.0       # B7 - Helning bak mur, 1/tan β
    PH: float = 0.0           # B8 - Horisontallast topp mur [kN/m]
    PV: float = 0.0           # B9 - Vertikallast topp mur [kN/m]
    yp: float = 0.0           # B10 - Høyde over mur for horisontal kraft [m]
    xp: float = 0.0           # B11 - Avstand fra murfront for vertikal kraft [m]
    gamma_mur: float = 23.0   # B12 - Spesifikk tyngdetetthet mur [kN/m³]

    # Dimensjoner mur
    H: float = 0.0            # B14 - Murhøyde [m]
    D: float = 0.0            # B15 - Fotdybde [m]
    bb: float = 0.0           # B16 - Murbredde bunn [m]
    stopt_saale: bool = False  # B17 - Støpt såle
    bx: float = 0.0           # B18 - Tillegg murbredde bunn [m]
    bt: float = 0.0           # B19 - Murbredde topp [m]
    d_helning: float = 0.0    # B20 - Murens helning
    inv_tan_alpha: float = 0.0  # B21 - Terrenghelning foran mur, 1/tan α
    rv: float = 0.3           # B22 - Ruhet bak muren

    # Beregning
    gamma_m: float = 0.0      # B24 - Materialfaktor
    inkluder_jordsug: bool = False  # B25

    # Jordparametre - bak
    phi_bak: float = 0.0      # H5 - Friksjonsvinkel bak [°]
    a_bak: float = 0.0        # H6 - Attraksjon bak [kPa]
    gamma_bak: float = 0.0    # H7 - Tyngdetetthet bak [kN/m³]

    # Jordparametre - under/foran
    phi_under: float = 0.0    # H9 - Friksjonsvinkel under/foran [°]
    a_under: float = 0.0      # H10 - Attraksjon under/foran [kPa]
    gamma_under: float = 0.0  # H11 - Tyngdetetthet under [kN/m³]
    gamma_foran: float = 0.0  # H12 - Tyngdetetthet foran [kN/m³]


@dataclass
class TorrmurResult:
    """All computed outputs, keyed by original cell reference."""
    cells: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.cells.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.cells[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.cells.get(key, default)

    def is_ok(self) -> bool:
        """Return True if all structural checks pass."""
        return (
            self.get("H45") == "OK"
            and self.get("M45") == "OK"
        )


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return float("inf")
    return a / b


def _compute_Ng_boss76(tan_rho: float, rb: float) -> float:
    """Compute Nγ using the BOSS-76 iterative method (columns AE-AL in Excel)."""
    if tan_rho == 0:
        return 0.0

    # Guard: rb should be in [0, 1) physically. Outside that range the
    # iterative formula can produce Rot < 0 → math domain error.
    if rb <= 0 or rb >= 1:
        return 0.0

    tan_a = tan_rho + math.sqrt(1 + tan_rho**2)
    N = tan_a**2
    rho_rad = math.atan(tan_rho)
    Kp = 2 * N / (N + 1) * math.exp((math.pi / 2 + rho_rad) * tan_rho)
    X0 = 2 * (1 - rb) * tan_rho

    # Iterative fixed-point (20 iterations)
    Xc = X0
    for _ in range(20):
        tan_psi = Xc - tan_rho
        psi = math.atan(tan_psi)
        c = (1 + tan_psi * tan_rho) * Kp * math.exp(2 * psi * tan_rho) - 1
        if c <= 0:
            break
        Rot = (1 - rb)**2 + (1 - rb) / c
        if Rot < 0:
            break
        Xc_new = (1 - rb + math.sqrt(Rot)) * tan_rho
        Xc = Xc_new

    # Final Ng
    tan_psi = Xc - tan_rho
    psi = math.atan(tan_psi)
    c = (1 + tan_psi * tan_rho) * Kp * math.exp(2 * psi * tan_rho) - 1
    if c <= 0 or Xc <= 0:
        return 0.0
    Ng = (2 * c * Xc + tan_rho) / (1 + tan_psi**2)
    return max(0.0, Ng)


def _compute_fsq_fsa_slope(inv_tan_alpha: float, tan_rho_under: float) -> tuple[float, float]:
    """Compute fsq and fsa reduction factors for sloping terrain."""
    if inv_tan_alpha == 0:
        return 1.0, 1.0

    tan_b = 1.0 / inv_tan_alpha
    b_rad = math.atan(tan_b)
    fsa = math.exp(-2 * b_rad * tan_rho_under)
    fsq = (1 - 0.55 * tan_b)**5
    return fsq, fsa


def _compute_fsq_fsa_table(inv_tan_alpha: float) -> tuple[float, float]:
    """Compute fsq and fsa from the piecewise table (columns V-Y, rows 100-107)."""
    if inv_tan_alpha == 0:
        return 1.0, 1.0

    tan_b = 1.0 / inv_tan_alpha

    # fsa piecewise
    if tan_b < 0.31:
        fsa = 1 - 1.0667 * tan_b
    elif tan_b < 0.41:
        fsa = 0.68 - 0.95 * (tan_b - 0.3)
    elif tan_b < 0.51:
        fsa = 0.585 - 0.8 * (tan_b - 0.4)
    elif tan_b < 0.61:
        fsa = 0.505 - 0.7 * (tan_b - 0.5)
    elif tan_b < 0.71:
        fsa = 0.435 - 0.65 * (tan_b - 0.6)
    elif tan_b < 0.751:
        fsa = 0.37 - 0.9 * (tan_b - 0.7)
    else:
        fsa = 0.0

    # fsq piecewise
    if tan_b < 0.31:
        fsq = 1 - 1.633 * tan_b
    elif tan_b < 0.41:
        fsq = 0.51 - 1.3 * (tan_b - 0.3)
    elif tan_b < 0.51:
        fsq = 0.38 - 1.2 * (tan_b - 0.4)
    elif tan_b < 0.61:
        fsq = 0.26 - 0.8 * (tan_b - 0.5)
    elif tan_b < 0.71:
        fsq = 0.18 - 0.65 * (tan_b - 0.6)
    elif tan_b < 0.751:
        fsq = 0.115 - 0.7 * (tan_b - 0.7)
    else:
        fsq = 0.0

    return fsq, fsa


def calculate(inp: TorrmurInput) -> TorrmurResult:
    """Run the full tørrmur calculation and return results keyed by cell ref."""
    r = TorrmurResult()

    # Shorthand aliases
    gm = inp.gamma_m
    H = inp.H
    D = inp.D
    bb = inp.bb
    bt = inp.bt
    d_h = inp.d_helning
    inv_tan_alpha = inp.inv_tan_alpha
    rv = inp.rv
    bx = inp.bx

    qk = inp.qk
    qQk = inp.qQk
    gammaQ = inp.gammaQ_nyttelast
    gammaQ_b = inp.gammaQ_boggilast
    inv_tan_beta = inp.inv_tan_beta
    PH = inp.PH
    PV = inp.PV
    yp = inp.yp
    xp = inp.xp
    gamma_mur = inp.gamma_mur

    phi_bak = inp.phi_bak
    a_bak = inp.a_bak
    gamma_bak = inp.gamma_bak
    phi_under = inp.phi_under
    a_under = inp.a_under
    gamma_under = inp.gamma_under
    gamma_foran = inp.gamma_foran

    inkluder_jordsug = inp.inkluder_jordsug
    stopt_saale = inp.stopt_saale

    pi = math.pi

    # Store inputs in result for reference
    r["B4"] = qk;  r["B5"] = qQk;  r["B6"] = gammaQ;  r["C6"] = gammaQ_b
    r["B7"] = inv_tan_beta;  r["B8"] = PH;  r["B9"] = PV
    r["B10"] = yp;  r["B11"] = xp;  r["B12"] = gamma_mur
    r["B14"] = H;  r["B15"] = D;  r["B16"] = bb
    r["B17"] = "Ja" if stopt_saale else "Nei"
    r["B18"] = bx;  r["B19"] = bt;  r["B20"] = d_h
    r["B21"] = inv_tan_alpha;  r["B22"] = rv
    r["B24"] = gm;  r["B25"] = "Ja" if inkluder_jordsug else "Nei"
    r["H5"] = phi_bak;  r["H6"] = a_bak;  r["H7"] = gamma_bak
    r["H9"] = phi_under;  r["H10"] = a_under
    r["H11"] = gamma_under;  r["H12"] = gamma_foran

    if gm == 0:
        for cell in ["B26", "B27", "B28", "B29", "B30", "B31",
                      "B35", "B36", "B37", "B38", "B39", "B40", "B41", "B42",
                      "B43", "B44", "B45", "B46", "B47",
                      "H40", "H41", "H42", "H43", "H44", "H45",
                      "M40", "M41", "M42", "M43", "M44", "M45",
                      "A33", "A34", "D46", "I46"]:
            r[cell] = " "
        return r

    # --- Friction angles ---
    R71 = phi_bak
    R72 = math.tan(R71 * pi / 180)
    R73 = phi_under
    R74 = math.tan(R73 * pi / 180)

    tan_rho_under = R74 / gm;  r["B26"] = tan_rho_under
    tan_rho_bak = R72 / gm;    r["B27"] = tan_rho_bak

    if inv_tan_beta != 0 and tan_rho_bak != 0:
        R87 = 1.0 / (inv_tan_beta * tan_rho_bak)
    else:
        R87 = 0.0
    r["B28"] = R87

    t_val = (1 + rv) * (1 - R87);  r["B29"] = t_val

    R90 = rv
    if tan_rho_bak > 0 and (1 - R87) >= 0 and (1 + R90) > 0:
        sin_rho_bak = math.sin(math.atan(tan_rho_bak))
        R88 = 1 + (1 / sin_rho_bak) * math.sqrt((1 - R87) / (1 + R90))
    else:
        R88 = float("nan")

    R97 = 1 if inkluder_jordsug else 0

    if d_h != 0:
        db = H / (H / d_h + bt - bb)
    else:
        db = float("inf")
    r["B30"] = db

    if not math.isinf(db):
        R129 = math.atan(db);  R130 = R129 * 180 / pi
    else:
        R129 = pi / 2;  R130 = 90.0
    R131 = 90 - R130;  r["B31"] = R131

    R93 = tan_rho_bak
    R94 = math.atan(R93) * 180 / pi
    R132 = R94;  R133 = R131 * pi / 180;  R134 = R132 * pi / 180

    cos_sum = math.cos(R133 + R134);  cos_d = math.cos(R133)
    cos_r = math.cos(R134)
    R135 = cos_sum**2 / (cos_d**3 * cos_r**2) if (cos_d != 0 and cos_r != 0) else 1.0

    K_delta = 1.0 if db < 0 else R135;  r["B37"] = K_delta

    R92 = t_val
    if R92 >= 0:
        denom = math.sqrt(1 + R93**2) + R93 * math.sqrt(R92)
        KA = 1.0 / denom**2
    else:
        KA = float("nan")
    r["B35"] = KA

    KA_korr = KA * K_delta;  r["B36"] = KA_korr

    # --- Wall weight ---
    if db < 0:
        Gvekt = abs(1 / db) * gamma_bak * H / 2 + (bb + bt) * H * gamma_mur / 2
    else:
        Gvekt = (bb + bt) * H * gamma_mur / 2
    r["B40"] = Gvekt

    # --- Earth pressure ---
    B71 = qQk * gammaQ_b + qk * gammaQ
    if H > 5:
        B73 = gamma_bak * 5 + qk * gammaQ
    else:
        B73 = (1 - H / 5) * qQk * gammaQ_b + qk * gammaQ + gamma_bak * H
    B74 = H * gamma_bak + qk * gammaQ if H > 5 else B73

    if (R87 - R88) != 0:
        jordsug_term = R97 * R87 / (R87 - R88)
    else:
        jordsug_term = 0
    D78 = KA_korr * (qk * gammaQ + qQk * gammaQ_b + a_bak) + a_bak * (jordsug_term - 1)

    R75 = KA_korr * (qk + a_bak) - a_bak
    J77 = PH;  J78 = yp + H

    if (R88 - R87) != 0:
        jordsug_factor = R97 * R87 / (R88 - R87)
    else:
        jordsug_factor = 0

    # Case 1: H>5, no tension
    B82 = (H * KA_korr * ((2 * (a_bak + qk * gammaQ) + gamma_bak * H) * 0.5)
           - H * a_bak * (1 + jordsug_factor)
           + KA_korr * gammaQ_b * qQk * 5 * 0.5)
    if B82 != 0:
        F82 = (1 / (6 * B82)) * (
            3 * H**2 * (KA_korr * (gammaQ * qk + gammaQ_b * qQk * 5 / H +
                                    gamma_bak * H / 3 + a_bak) -
                        a_bak * (1 + jordsug_factor)) -
            KA_korr * gammaQ_b * qQk * 5**2)
    else:
        F82 = 0
    B83 = B82 + J77
    F83 = (J77 / B83) * J78 + (B82 / B83) * F82 if B83 != 0 else 0
    B84 = R90 * R93 * (B82 / H + a_bak) * H if H != 0 else 0

    # Case 2: H>5, with tension
    denom_z0 = KA_korr * (gamma_bak - gammaQ_b * qQk / 5)
    B87 = ((a_bak * (jordsug_factor + 1) -
            KA_korr * (a_bak + gammaQ_b * qQk + gammaQ * qk)) / denom_z0
           if denom_z0 != 0 else 0)
    top_stress = KA_korr * (a_bak + qk * gammaQ + gamma_bak * H) - a_bak * (jordsug_factor + 1)
    bot5_stress = a_bak * (jordsug_factor + 1) - KA_korr * (a_bak + gammaQ * qk + gamma_bak * 5)
    B88 = 0.5 * (top_stress * (H - 5) - bot5_stress * (H - B87))
    B89 = B88 + J77
    if B88 != 0 and B89 != 0:
        F88_num = (top_stress * (H - 5)**2 +
                   bot5_stress * (H - B87) * (B87 - 2 * H + 5))
        F88 = (1 / (6 * B88)) * F88_num
        F89 = (J77 / B89) * J78 + (B88 / B89) * F88
    else:
        F88 = 0;  F89 = 0
    B90 = R90 * R93 * (B88 / (H - B87) + a_bak) * (H - B87) if (H - B87) != 0 else 0

    # Case 3: H<=5, no tension
    term_top = KA_korr * (a_bak + gammaQ_b * qQk + gammaQ * qk) - a_bak * (jordsug_factor + 1)
    term_bot = KA_korr * (a_bak + gammaQ * qk - gammaQ_b * qQk * (H / 5 - 1) + gamma_bak * H) - a_bak * (jordsug_factor + 1)
    B95 = 0.5 * (H * term_top + H * term_bot)
    B96 = B95 + J77
    F95 = (1 / (6 * B95)) * (2 * H**2 * term_top + H**2 * term_bot) if B95 != 0 else 0
    F96 = (J77 / B96) * J78 + (B95 / B96) * F95 if B96 != 0 else 0
    B97 = R90 * R93 * (B95 / H + a_bak) * H if H != 0 else 0

    # Case 4: H<=5, with tension
    B100 = B87
    B101 = 0.5 * ((H - B100) * term_bot) if (H - B100) != 0 else 0
    B102 = B101 + J77
    F101 = (H - B100) / 3 if (H - B100) != 0 else 0
    F102 = (J77 / B102) * J78 + (B101 / B102) * F101 if B102 != 0 else 0
    B103 = R90 * R93 * (B101 / (H - B100) + a_bak) * (H - B100) if (H - B100) != 0 else 0

    # Select case
    if D78 < 0:
        if H <= 5:
            EA, EA_RH, EA_T, c1, cH = B101, B102, B103, F101, F102
        else:
            EA, EA_RH, EA_T, c1, cH = B88, B89, B90, F88, F89
    else:
        if H <= 5:
            EA, EA_RH, EA_T, c1, cH = B95, B96, B97, F95, F96
        else:
            EA, EA_RH, EA_T, c1, cH = B82, B83, B84, F82, F83

    r["B38"] = EA
    T = (EA / H + a_bak) * rv * tan_rho_bak * H if H != 0 else 0
    r["B39"] = T

    RV = Gvekt + T + PV;  r["B41"] = RV
    r["B42"] = EA_RH
    r["B43"] = c1

    c2 = -c1 / db if (db != 0 and not math.isinf(db)) else 0
    r["B44"] = c2

    if Gvekt != 0 and d_h != 0 and not math.isinf(db):
        tri_weight = H / 6 * (bb - bt) * gamma_mur * (bb - bt - H / db)
        rect_weight = H * bt * gamma_mur * (bb - 0.5 * bt - 0.5 * H / d_h)
        c3 = (tri_weight + rect_weight) / Gvekt
    else:
        c3 = bb / 2
    r["B45"] = c3

    cPv = -bb + (1 / d_h) * H + xp if d_h != 0 else -bb + xp

    c4 = (EA * c1 - T * c2 - Gvekt * c3 + PV * cPv) / RV if RV != 0 else 0
    r["B46"] = c4
    r["B47"] = cH

    # --- Bearing capacity ---
    e = c4 - bb / 2;  r["H40"] = e

    if e < 0:
        W111 = bb + bx
    elif stopt_saale:
        W111 = bb + bx
    else:
        W111 = bb

    R120 = (0.9 * W111 - 2 * e) if not stopt_saale else (W111 - 2 * e)
    R119 = bb + bx
    b0 = min(R120, R119);  r["H44"] = b0

    qV = RV / b0 if b0 != 0 else float("inf");  r["H41"] = qV

    if b0 != 0 and (qV + a_under) != 0 and tan_rho_under != 0:
        rb = EA_RH / (b0 * (qV + a_under) * tan_rho_under)
    else:
        rb = 0
    r["H42"] = rb

    if inv_tan_alpha == 0:
        rb_krav = 0.8 if phi_under < 32 else 0.9
    elif inv_tan_alpha < 10:
        rb_krav = 0.7 if phi_under < 32 else 0.8
    else:
        rb_krav = 0.8 if phi_under < 32 else 0.9
    r["H43"] = rb_krav

    b0_min = (bb - 2 * bb / 6) if stopt_saale else (0.9 * bb - 2 * bb / 6)
    R125 = "OK" if b0 >= b0_min else "Ikke OK"
    e_limit = 0.9 * (bb + bx) / 3
    R126 = "OK" if e <= e_limit else "Ikke OK"
    r["H45"] = "OK" if (R125 == "OK" and R126 == "OK") else "NEI"

    # --- Bearing capacity factors ---
    R98 = tan_rho_under
    R99 = math.atan(R98) * 180 / pi
    R100 = math.atan(R98)

    if abs(rb) < 1:
        R101 = (1 / (rb + 0.00001)) * (1 - math.sqrt(1 - rb**2))
    else:
        R101 = 1.0
    R103 = math.atan(R101 * math.tan(pi * 0.25 + 0.5 * R100))

    sin_rho = math.sin(R99 * pi / 180)
    R104 = (1 + sin_rho) / (1 - sin_rho) if sin_rho < 1 else float("inf")

    Nq = ((R104 + 1) + (R104 - 1) * math.cos(2 * R103)) * math.exp((pi - 2 * R103) * R98) / 2
    r["M41"] = Nq

    Ng = _compute_Ng_boss76(R98, rb);  r["M40"] = Ng

    fsq, fsa = (_compute_fsq_fsa_slope(inv_tan_alpha, R98)
                if inv_tan_alpha != 0 else (1.0, 1.0))
    r["M42"] = fsq;  r["M43"] = fsa

    sigma_V = (fsq * (0.5 * Ng * gamma_under * b0 + Nq * gamma_foran * D) +
               fsa * Nq * a_under - a_under)
    r["M44"] = sigma_V
    r["M45"] = "OK" if sigma_V > qV else "NEI"

    R67_ok = "Ja" if rb < rb_krav else "Nei"
    R68_ok = "Ja" if sigma_V > qV else "Nei"

    # Messages
    r["A33"] = ("Teoretisk strekk i topp – nullspennings\u00addybde beregnet"
                if D78 < 0 else "")
    r["A34"] = ("NB: Murhøyde > 5 m – boggilast fordeles over 5 m"
                if H > 5 else "")
    if rb_krav > rb - 0.0001 and r["H45"] == "OK":
        r["D46"] = "Krav til maksimal ruhet i fundamentfuge og effektiv fundamentbredde innfridd"
    else:
        r["D46"] = "NB! Krav til maksimal ruhet i fundamentfuge eller effektiv fundamentbredde ikke innfridd"
    r["I46"] = ("Krav til maksimalt tillatt overført fundamenttrykk innfridd"
                if sigma_V > qV else
                "NB! Krav til maksimalt tillatt overført fundamenttrykk overskredet")

    return r


def volume_per_meter(bt: float, bb: float, H: float) -> float:
    """Cross-sectional area of a trapezoidal wall per running metre."""
    return 0.5 * (bt + bb) * H


def inputs_from_dict(d: dict) -> TorrmurInput:
    """Create TorrmurInput from a flat parameter dictionary.

    Accepts keys matching dataclass field names, e.g. ``{"H": 4.0, "bb": 2.2}``.
    """
    fields = {f.name for f in TorrmurInput.__dataclass_fields__.values()}
    kwargs = {}
    for k, v in d.items():
        if k in fields:
            ftype = TorrmurInput.__dataclass_fields__[k].type
            if ftype == 'bool':
                kwargs[k] = bool(v) if not isinstance(v, bool) else v
            else:
                try:
                    kwargs[k] = float(v)
                except (TypeError, ValueError):
                    pass
    return TorrmurInput(**kwargs)
