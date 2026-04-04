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


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return float("inf")
    return a / b


def _compute_Ng_boss76(tan_rho: float, rb: float) -> float:
    """Compute Nγ using the BOSS-76 iterative method (columns AE-AL in Excel)."""
    if tan_rho == 0:
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
        Rot = (1 - rb)**2 + (1 - rb) / c
        Xc_new = (1 - rb + math.sqrt(Rot)) * tan_rho
        Xc = Xc_new

    # Final Ng
    tan_psi = Xc - tan_rho
    psi = math.atan(tan_psi)
    c = (1 + tan_psi * tan_rho) * Kp * math.exp(2 * psi * tan_rho) - 1
    Ng = (2 * c * Xc + tan_rho) / (1 + tan_psi**2)
    return Ng


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
    H = inp.H      # murhøyde_inkl._fotdybde (B14)
    D = inp.D      # B15
    bb = inp.bb    # B16
    bt = inp.bt    # B19
    d_h = inp.d_helning  # B20 (murens_helning)
    inv_tan_alpha = inp.inv_tan_alpha  # B21
    rv = inp.rv    # B22
    bx = inp.bx    # B18

    qk = inp.qk          # B4
    qQk = inp.qQk        # B5
    gammaQ = inp.gammaQ_nyttelast   # B6
    gammaQ_b = inp.gammaQ_boggilast  # C6
    inv_tan_beta = inp.inv_tan_beta  # B7
    PH = inp.PH    # B8
    PV = inp.PV    # B9
    yp = inp.yp    # B10
    xp = inp.xp    # B11
    gamma_mur = inp.gamma_mur  # B12

    phi_bak = inp.phi_bak    # H5
    a_bak = inp.a_bak        # H6
    gamma_bak = inp.gamma_bak  # H7
    phi_under = inp.phi_under  # H9
    a_under = inp.a_under      # H10
    gamma_under = inp.gamma_under  # H11
    gamma_foran = inp.gamma_foran  # H12

    inkluder_jordsug = inp.inkluder_jordsug  # B25
    stopt_saale = inp.stopt_saale  # B17

    pi = math.pi

    # Store inputs in result for reference
    r["B4"] = qk
    r["B5"] = qQk
    r["B6"] = gammaQ
    r["C6"] = gammaQ_b
    r["B7"] = inv_tan_beta
    r["B8"] = PH
    r["B9"] = PV
    r["B10"] = yp
    r["B11"] = xp
    r["B12"] = gamma_mur
    r["B14"] = H
    r["B15"] = D
    r["B16"] = bb
    r["B17"] = "Ja" if stopt_saale else "Nei"
    r["B18"] = bx
    r["B19"] = bt
    r["B20"] = d_h
    r["B21"] = inv_tan_alpha
    r["B22"] = rv
    r["B24"] = gm
    r["B25"] = "Ja" if inkluder_jordsug else "Nei"
    r["H5"] = phi_bak
    r["H6"] = a_bak
    r["H7"] = gamma_bak
    r["H9"] = phi_under
    r["H10"] = a_under
    r["H11"] = gamma_under
    r["H12"] = gamma_foran

    if gm == 0:
        # No calculation possible without materialfaktor
        for cell in ["B26", "B27", "B28", "B29", "B30", "B31",
                      "B35", "B36", "B37", "B38", "B39", "B40", "B41", "B42",
                      "B43", "B44", "B45", "B46", "B47",
                      "H40", "H41", "H42", "H43", "H44", "H45",
                      "M40", "M41", "M42", "M43", "M44", "M45",
                      "A33", "A34", "D46", "I46"]:
            r[cell] = " "
        return r

    # --- R71-R74: friction angles ---
    # R71 = phi_bak, R72 = tan(phi_bak * pi/180)
    R71 = phi_bak
    R72 = math.tan(R71 * pi / 180)  # tan_phi_bak
    R73 = phi_under
    R74 = math.tan(R73 * pi / 180)  # tan_phi_under

    # B26 = tan_rho_under = R74 / gamma_m
    tan_rho_under = R74 / gm
    r["B26"] = tan_rho_under

    # B27 = tan_rho_bak = R72 / gamma_m
    tan_rho_bak = R72 / gm
    r["B27"] = tan_rho_bak

    # R87: s for jordtrykk
    # R87 = IF(B7<>0, 1/(B7*B27), 0)
    if inv_tan_beta != 0 and tan_rho_bak != 0:
        R87 = 1.0 / (inv_tan_beta * tan_rho_bak)
    else:
        R87 = 0.0
    r["B28"] = R87  # s (hellende terreng bak mur)

    # B29 = t = (1 + rv) * (1 - s)
    t_val = (1 + rv) * (1 - R87)
    r["B29"] = t_val

    # R90 = rv (B22)
    R90 = rv

    # R88: omega_a = 1 + (1/sin(atan(tan_rho_bak))) * sqrt((1-s)/(1+rv))
    # This needs tan_rho_bak > 0
    if tan_rho_bak > 0 and (1 - R87) >= 0 and (1 + R90) > 0:
        sin_rho_bak = math.sin(math.atan(tan_rho_bak))
        R88 = 1 + (1 / sin_rho_bak) * math.sqrt((1 - R87) / (1 + R90))
    else:
        R88 = float("nan")

    # R97 = IF(B25="Ja", 1, 0) - jordsug flag
    R97 = 1 if inkluder_jordsug else 0

    # B30: db = H / (H/d + bt - bb)
    if d_h != 0:
        db = H / (H / d_h + bt - bb)
    else:
        # d_h==0 means vertical wall, db undefined
        db = float("inf")
    r["B30"] = db

    # R129-R135: K_delta calculation
    # R129 = atan(B30)
    if not math.isinf(db):
        R129 = math.atan(db)
        R130 = R129 * 180 / pi
    else:
        R129 = pi / 2
        R130 = 90.0

    # R131 = 90 - R130 (delta in degrees)
    R131 = 90 - R130
    r["B31"] = R131  # delta

    # R93 = B27 = tan_rho_bak
    R93 = tan_rho_bak
    # R94 = atan(R93)*180/pi (rho_bak in degrees)
    R94 = math.atan(R93) * 180 / pi
    R132 = R94  # mob. friksjonsvinkel bak mur i grader

    # R133 = R131 * pi / 180 (delta in radians)
    R133 = R131 * pi / 180
    # R134 = R132 * pi / 180 (rho_bak in radians)
    R134 = R132 * pi / 180

    # R135 = cos(R133+R134)^2 / (cos(R133)^3 * cos(R134)^2)
    cos_sum = math.cos(R133 + R134)
    cos_d = math.cos(R133)
    cos_r = math.cos(R134)
    if cos_d != 0 and cos_r != 0:
        R135 = cos_sum**2 / (cos_d**3 * cos_r**2)
    else:
        R135 = 1.0

    # B37: K_delta = IF(db < 0, 1, R135)
    K_delta = 1.0 if db < 0 else R135
    r["B37"] = K_delta

    # R92 = B29 = t
    R92 = t_val
    # R113: KA = 1 / (sqrt(1 + tan_rho_bak^2) + tan_rho_bak * sqrt(t))^2
    if R92 >= 0:
        denom = math.sqrt(1 + R93**2) + R93 * math.sqrt(R92)
        KA = 1.0 / denom**2
    else:
        KA = float("nan")
    r["B35"] = KA

    # B36: KA_korr = KA * K_delta
    KA_korr = KA * K_delta
    r["B36"] = KA_korr

    # --- Wall weight (Gvekt = U118) ---
    # U118: IF(db<0, abs(1/db)*gamma_bak*H/2 + (bb+bt)*H*gamma_mur/2, (bb+bt)*H*gamma_mur/2)
    if db < 0:
        Gvekt = abs(1 / db) * gamma_bak * H / 2 + (bb + bt) * H * gamma_mur / 2
    else:
        Gvekt = (bb + bt) * H * gamma_mur / 2
    r["B40"] = Gvekt

    # --- Earth pressure calculations ---
    # p_gamma = B4 = qk (named range p_gamma -> B4)
    p_gamma = qk

    # B71: qg = qQk*gammaQ_b + qk*gammaQ
    B71 = qQk * gammaQ_b + qk * gammaQ

    # B73: vertical stress at bottom depth
    if H > 5:
        B73 = gamma_bak * 5 + qk * gammaQ
    else:
        B73 = (1 - H / 5) * qQk * gammaQ_b + qk * gammaQ + gamma_bak * H

    # B74
    if H > 5:
        B74 = H * gamma_bak + qk * gammaQ
    else:
        B74 = B73

    # D78: test om strekk i topp
    # D78 = KA_korr*(qk*gammaQ + qQk*gammaQ_b + a_bak) + a_bak*((R97*R87/(R87-R88))-1)
    if (R87 - R88) != 0:
        jordsug_term = R97 * R87 / (R87 - R88)
    else:
        jordsug_term = 0
    D78 = KA_korr * (qk * gammaQ + qQk * gammaQ_b + a_bak) + a_bak * (jordsug_term - 1)

    # R75: B = KA_korr*(p_gamma + a_bak) - a_bak
    R75 = KA_korr * (p_gamma + a_bak) - a_bak
    # R76: IF(R75 < 0, 0, R75)
    R76 = max(0, R75)

    # J77 = PH (B8)
    J77 = PH
    # J78 = yp + H (B10 + B14)
    J78 = yp + H

    # Determine if R88 - R87 != 0 for jordsug formulas
    if (R88 - R87) != 0:
        jordsug_factor = R97 * R87 / (R88 - R87)
    else:
        jordsug_factor = 0

    # ---- Four cases for earth pressure ----
    # Case 1: H>5, no theoretical tension (D78 >= 0)
    # B82: EA
    B82 = (H * KA_korr * ((2 * (a_bak + qk * gammaQ) + gamma_bak * H) * 0.5)
           - H * a_bak * (1 + jordsug_factor)
           + KA_korr * gammaQ_b * qQk * 5 * 0.5)
    # F82: c1 (momentarm)
    if B82 != 0:
        F82 = (1 / (6 * B82)) * (
            3 * H**2 * (KA_korr * (gammaQ * qk + gammaQ_b * qQk * 5 / H +
                                    gamma_bak * H / 3 + a_bak) -
                        a_bak * (1 + jordsug_factor)) -
            KA_korr * gammaQ_b * qQk * 5**2
        )
    else:
        F82 = 0
    B83 = B82 + J77  # RH
    if B83 != 0:
        F83 = (J77 / B83) * J78 + (B82 / B83) * F82
    else:
        F83 = 0
    B84 = R90 * R93 * (B82 / H + a_bak) * H if H != 0 else 0  # T

    # Case 2: H>5, with theoretical tension
    # B87: z0 (nullspenningsdybde)
    denom_z0 = KA_korr * (gamma_bak - gammaQ_b * qQk / 5)
    if denom_z0 != 0:
        B87 = (a_bak * (jordsug_factor + 1) -
               KA_korr * (a_bak + gammaQ_b * qQk + gammaQ * qk)) / denom_z0
    else:
        B87 = 0

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
        F88 = 0
        F89 = 0
    B90 = R90 * R93 * (B88 / (H - B87) + a_bak) * (H - B87) if (H - B87) != 0 else 0

    # Case 3: H<=5, no theoretical tension (D78 >= 0)
    term_top = KA_korr * (a_bak + gammaQ_b * qQk + gammaQ * qk) - a_bak * (jordsug_factor + 1)
    term_bot = KA_korr * (a_bak + gammaQ * qk - gammaQ_b * qQk * (H / 5 - 1) + gamma_bak * H) - a_bak * (jordsug_factor + 1)
    B95 = 0.5 * (H * term_top + H * term_bot)
    B96 = B95 + J77
    if B95 != 0:
        F95 = (1 / (6 * B95)) * (2 * H**2 * term_top + H**2 * term_bot)
    else:
        F95 = 0
    if B96 != 0:
        F96 = (J77 / B96) * J78 + (B95 / B96) * F95
    else:
        F96 = 0
    B97 = R90 * R93 * (B95 / H + a_bak) * H if H != 0 else 0

    # Case 4: H<=5, with theoretical tension
    B100 = B87  # same z0
    if (H - B100) != 0:
        B101 = 0.5 * ((H - B100) * term_bot)
    else:
        B101 = 0
    B102 = B101 + J77
    if (H - B100) != 0:
        F101 = (H - B100) / 3
    else:
        F101 = 0
    if B102 != 0:
        F102 = (J77 / B102) * J78 + (B101 / B102) * F101
    else:
        F102 = 0
    B103 = R90 * R93 * (B101 / (H - B100) + a_bak) * (H - B100) if (H - B100) != 0 else 0

    # Select case (B104-B106, F104-F105)
    if D78 < 0:
        # With tension
        if H <= 5:
            EA = B101
            EA_RH = B102
            EA_T = B103
            c1 = F101
            cH = F102
        else:
            EA = B88
            EA_RH = B89
            EA_T = B90
            c1 = F88
            cH = F89
    else:
        # No tension
        if H <= 5:
            EA = B95
            EA_RH = B96
            EA_T = B97
            c1 = F95
            cH = F96
        else:
            EA = B82
            EA_RH = B83
            EA_T = B84
            c1 = F82
            cH = F83

    # R81 = B104 = EA
    r["B38"] = EA   # Jordtrykksresultant

    # B39: T = (EA/H + a_bak) * rv * tan_rho_bak * H
    if H != 0:
        T = (EA / H + a_bak) * rv * tan_rho_bak * H
    else:
        T = 0
    r["B39"] = T

    # B41: RV = Gvekt + T + PV
    RV = Gvekt + T + PV
    r["B41"] = RV

    # B42: RH = R83 = EA + PH (the selected EA_RH already includes PH)
    r["B42"] = EA_RH

    # B43: c1 (momentarm for EA)
    r["B43"] = c1

    # B44: c2 = -c1 / db  (momentarm for T)
    if db != 0 and not math.isinf(db):
        c2 = -c1 / db
    else:
        c2 = 0
    r["B44"] = c2

    # B45: c3 (momentarm for egenvekt)
    if Gvekt != 0 and d_h != 0 and not math.isinf(db):
        tri_weight = H / 6 * (bb - bt) * gamma_mur * (bb - bt - H / db)
        rect_weight = H * bt * gamma_mur * (bb - 0.5 * bt - 0.5 * H / d_h)
        c3 = (tri_weight + rect_weight) / Gvekt
    else:
        c3 = bb / 2  # fallback for vertical wall
    r["B45"] = c3

    # R86: Momentarm vertikallast cPv = -bb + (1/d_h)*H + xp
    if d_h != 0:
        cPv = -bb + (1 / d_h) * H + xp
    else:
        cPv = -bb + xp

    # B46: c4 (momentarm for vertikalresultant)
    if RV != 0:
        c4 = (EA * c1 - T * c2 - Gvekt * c3 + PV * cPv) / RV
    else:
        c4 = 0
    r["B46"] = c4

    # B47: cH (momentarm for horisontalresultant) = selected cH
    r["B47"] = cH

    # ---- Bæreevne ----
    # H40: e = c4 - bb/2
    e = c4 - bb / 2
    r["H40"] = e

    # W111: effective width parameter
    if e < 0:
        W111 = bb + bx
    elif stopt_saale:
        W111 = bb + bx
    else:
        W111 = bb

    # R120: b0 calculation
    if not stopt_saale:
        R120 = 0.9 * W111 - 2 * e
    else:
        R120 = W111 - 2 * e

    # R119 = bb + bx
    R119 = bb + bx

    # R121: b0 = min(R120, R119)
    b0 = min(R120, R119) if R120 <= R119 else R119
    r["H44"] = b0

    # H41: qV = RV / b0
    if b0 != 0:
        qV = RV / b0
    else:
        qV = float("inf")
    r["H41"] = qV

    # H42: rb = RH / (b0 * (qV + a_under) * tan_rho_under)
    if b0 != 0 and (qV + a_under) != 0 and tan_rho_under != 0:
        rb = EA_RH / (b0 * (qV + a_under) * tan_rho_under)
    else:
        rb = 0
    r["H42"] = rb

    # R140-R143: krav til rb
    if phi_under < 32:
        material_type = "Leire"
    else:
        material_type = "Grus"

    if inv_tan_alpha == 0:
        rb_leire = 0.8
        rb_grus = 0.9
    elif inv_tan_alpha < 10:
        rb_leire = 0.7
        rb_grus = 0.8
    else:
        rb_leire = 0.8
        rb_grus = 0.9

    rb_krav = rb_leire if phi_under < 32 else rb_grus
    r["H43"] = rb_krav

    # R124: b0_min
    if stopt_saale:
        b0_min = bb - 2 * bb / 6
    else:
        b0_min = 0.9 * bb - 2 * bb / 6

    # R125, R126: checks
    R125 = "OK" if b0 >= b0_min else "Ikke OK"
    e_limit = 0.9 * (bb + bx) / 3
    R126 = "OK" if e <= e_limit else "Ikke OK"

    # H45
    if R125 == "OK" and R126 == "OK":
        r["H45"] = "OK"
    else:
        r["H45"] = "NEI"

    # ---- Bæreevnefaktorer ----
    # R98 = B26 = tan_rho_under
    R98 = tan_rho_under
    # R99 = atan(R98)*180/pi (rho_under deg)
    R99 = math.atan(R98) * 180 / pi
    R100 = math.atan(R98)  # rho_under rad

    # R91 = H42 = rb
    R91 = rb

    # R101: fw = (1/(rb+0.00001)) * (1 - sqrt(1 - rb^2))
    if abs(R91) < 1:
        R101 = (1 / (R91 + 0.00001)) * (1 - math.sqrt(1 - R91**2))
    else:
        R101 = 1.0
    # R103: omega_rad = atan(fw * tan(pi/4 + rho_under_rad/2))
    R103 = math.atan(R101 * math.tan(pi * 0.25 + 0.5 * R100))

    # R104: N = (1+sin(rho_deg*pi/180))/(1-sin(rho_deg*pi/180))
    sin_rho = math.sin(R99 * pi / 180)
    if sin_rho < 1:
        R104 = (1 + sin_rho) / (1 - sin_rho)
    else:
        R104 = float("inf")

    # R114: Nq = ((N+1) + (N-1)*cos(2*omega_rad)) * exp((pi - 2*omega_rad)*tan_rho_under) / 2
    Nq = ((R104 + 1) + (R104 - 1) * math.cos(2 * R103)) * math.exp((pi - 2 * R103) * R98) / 2
    r["M41"] = Nq

    # R115: Ng (from BOSS-76 iteration)
    Ng = _compute_Ng_boss76(R98, R91)
    r["M40"] = Ng

    # fsq, fsa
    if inv_tan_alpha != 0:
        fsq, fsa = _compute_fsq_fsa_slope(inv_tan_alpha, R98)
    else:
        fsq = 1.0
        fsa = 1.0
    r["M42"] = fsq
    r["M43"] = fsa

    # M44: σV = fsq * (0.5 * Ng * gamma_under * b0 + Nq * gamma_foran * D) + fsa * Nq * a_under - a_under
    sigma_V = (fsq * (0.5 * Ng * gamma_under * b0 + Nq * gamma_foran * D) +
               fsa * Nq * a_under - a_under)
    r["M44"] = sigma_V

    # M45: kontroll
    r["M45"] = "OK" if sigma_V > qV else "NEI"

    # R67, R68, R69
    R67_ok = "Ja" if rb < rb_krav else "Nei"
    R68_ok = "Ja" if sigma_V > qV else "Nei"
    if R67_ok == "Ja" and R68_ok == "Ja":
        R69 = "OK"
    else:
        R69 = "NEI"

    # Messages
    # A33: general message about earth pressure (from workbook this is static text)
    if D78 < 0:
        r["A33"] = "Teoretisk strekk i topp – nullspennings­dybde beregnet"
    else:
        r["A33"] = ""

    if H <= 5:
        r["A34"] = ""
    else:
        r["A34"] = "NB: Murhøyde > 5 m – boggilast fordeles over 5 m"

    # D46: message
    if rb_krav > rb - 0.0001 and r["H45"] == "OK":
        r["D46"] = "Krav til maksimal ruhet i fundamentfuge og effektiv fundamentbredde innfridd"
    else:
        r["D46"] = "NB! Krav til maksimal ruhet i fundamentfuge eller effektiv fundamentbredde ikke innfridd"

    # I46: message
    if sigma_V > qV:
        r["I46"] = "Krav til maksimalt tillatt overført fundamenttrykk innfridd"
    else:
        r["I46"] = "NB! Krav til maksimalt tillatt overført fundamenttrykk overskredet"

    # --- Store remaining R-cells needed for detail tables ---
    r["R67"] = R67_ok
    r["R68"] = R68_ok
    r["R69"] = R69
    r["R70"] = rb_krav
    r["R71"] = R71
    r["R72"] = R72
    r["R73"] = R73
    r["R74"] = R74
    r["R75"] = R75
    r["R76"] = R76
    r["R77"] = KA_korr * (qk + gamma_bak * H + a_bak) * H / 2 - a_bak * H / 2 if H > 0 else 0
    r["R78"] = 0  # placeholder
    r["R79"] = (KA_korr * gamma_bak * H**2) / 2 + H * (KA_korr * (qk + a_bak) - a_bak) if H > 0 else 0
    r["R80"] = 0  # placeholder
    r["R81"] = EA
    r["R82"] = c1
    r["R83"] = EA_RH
    r["R84"] = cH
    r["R85"] = EA_T if D78 < 0 else (B97 if H <= 5 else B84)
    r["R86"] = cPv
    r["R87"] = R87
    r["R88"] = R88
    r["R89"] = pi
    r["R90"] = R90
    r["R91"] = rb
    r["R92"] = t_val
    r["R93"] = R93
    r["R94"] = R94
    r["R95"] = "Ja"
    r["R96"] = "Nei"
    r["R97"] = R97
    r["R98"] = R98
    r["R99"] = R99
    r["R100"] = R100
    r["R101"] = R101
    r["R103"] = R103
    r["R104"] = R104
    r["R113"] = KA
    r["R114"] = Nq
    r["R115"] = Ng
    r["R116"] = fsq
    r["R117"] = fsa
    r["R119"] = R119
    r["R120"] = R120
    r["R121"] = b0
    r["R124"] = b0_min
    r["R125"] = R125
    r["R126"] = R126
    r["R129"] = R129 if not math.isinf(db) else 0
    r["R130"] = R130
    r["R131"] = R131
    r["R132"] = R132
    r["R133"] = R133
    r["R134"] = R134
    r["R135"] = R135
    r["R140"] = material_type
    r["R141"] = rb_leire
    r["R142"] = rb_grus
    r["R143"] = rb_krav

    # B-column detail rows
    r["B71"] = B71
    r["B73"] = B73
    r["B74"] = B74
    r["B82"] = B82
    r["B83"] = B83
    r["B84"] = B84
    r["B87"] = B87
    r["B88"] = B88
    r["B89"] = B89
    r["B90"] = B90
    r["B95"] = B95
    r["B96"] = B96
    r["B97"] = B97
    r["B100"] = B100
    r["B101"] = B101
    r["B102"] = B102
    r["B103"] = B103
    r["B104"] = EA
    r["B105"] = EA_RH
    r["B106"] = EA_T

    # F-column detail rows
    r["F82"] = F82
    r["F83"] = F83
    r["F88"] = F88
    r["F89"] = F89
    r["F95"] = F95
    r["F96"] = F96
    r["F101"] = F101
    r["F102"] = F102
    r["F104"] = c1
    r["F105"] = cH

    # D78
    r["D78"] = D78

    # U118 = Gvekt
    r["U118"] = Gvekt

    # J77, J78
    r["J77"] = J77
    r["J78"] = J78

    # D73, D74
    r["D73"] = min(5, H) if H > 0 else 0
    r["D74"] = H if H > 5 else r["D73"]

    # W111
    r["W111"] = W111

    return r


def inputs_from_cell_dict(cell_dict: dict[str, Any]) -> TorrmurInput:
    """Convert the app's entered_values dict (cell->value) to TorrmurInput."""
    def _num(cell: str, default: float = 0.0) -> float:
        v = cell_dict.get(cell)
        if v is None:
            return default
        if isinstance(v, (int, float)):
            return float(v)
        return default

    def _bool_choice(cell: str) -> bool:
        v = cell_dict.get(cell)
        if isinstance(v, str):
            return v.strip().lower() == "ja"
        if isinstance(v, bool):
            return v
        return False

    return TorrmurInput(
        qk=_num("B4"),
        qQk=_num("B5"),
        gammaQ_nyttelast=_num("B6", 1.3),
        gammaQ_boggilast=_num("C6", 1.15),
        inv_tan_beta=_num("B7"),
        PH=_num("B8"),
        PV=_num("B9"),
        yp=_num("B10"),
        xp=_num("B11"),
        gamma_mur=_num("B12", 23.0),
        H=_num("B14"),
        D=_num("B15"),
        bb=_num("B16"),
        stopt_saale=_bool_choice("B17"),
        bx=_num("B18"),
        bt=_num("B19"),
        d_helning=_num("B20"),
        inv_tan_alpha=_num("B21"),
        rv=_num("B22", 0.3),
        gamma_m=_num("B24"),
        inkluder_jordsug=_bool_choice("B25"),
        phi_bak=_num("H5"),
        a_bak=_num("H6"),
        gamma_bak=_num("H7"),
        phi_under=_num("H9"),
        a_under=_num("H10"),
        gamma_under=_num("H11"),
        gamma_foran=_num("H12"),
    )
