# -*- coding: utf-8 -*-
"""
Live Plaxis Integrasjonstest
=============================
Kobler til en ekte Plaxis-server og tester hele kjeden:
    tilkobling → model-info → resolve → extract → Excel

Hoppes automatisk over med mindre --plaxis-port og --plaxis-password er gitt.

Kjøring med ekte Plaxis:
    pytest tests/integration/test_plaxis_live.py \\
        --plaxis-port 10000 \\
        --plaxis-password DittPassord

Hvis Plaxis Output kjører på en annen port:
    pytest tests/integration/test_plaxis_live.py \\
        --plaxis-port 10000 \\
        --plaxis-password DittPassord \\
        --plaxis-out-port 10001

Forutsetning: Plaxis Input må kjøre med et åpent prosjekt.
"""

import pytest

from activities.plaxis.extraction.model_info import extract_model_info
from activities.plaxis.extraction.structure_resolver import resolve_structures, resolve_phases
from activities.plaxis.extraction.result_extractor import run_msf, run_capacity, run_displacement


# ---------------------------------------------------------------------------
# Hjelpere
# ---------------------------------------------------------------------------

def _plate_names(info, n=2):
    return [p["name"] for p in info["structures"]["plates"][:n]]

def _phase_names(info, n=2):
    return [ph["name"] for ph in info["phases"][:n]]


# ---------------------------------------------------------------------------
# 1. Tilkoblingstester
# ---------------------------------------------------------------------------

class TestTilkobling:

    def test_input_server_svarer(self, plaxis_connection):
        """g_i er tilkoblet og har Phases."""
        g_i = plaxis_connection["g_i"]
        assert hasattr(g_i, "Phases"), "g_i mangler Phases — er Plaxis Input startet med åpent prosjekt?"
        assert len(g_i.Phases) > 0, "Ingen faser funnet i modellen"

    def test_output_server_svarer(self, plaxis_connection):
        """g_o er tilkoblet og har Phases."""
        g_o = plaxis_connection["g_o"]
        if g_o is None:
            pytest.skip("Plaxis Output ikke tilgjengelig — kjør med --plaxis-out-port")
        assert hasattr(g_o, "Phases")
        assert len(g_o.Phases) > 0


# ---------------------------------------------------------------------------
# 2. Model-info
# ---------------------------------------------------------------------------

class TestModelInfo:

    def test_returnerer_strukturer_og_faser(self, plaxis_connection):
        info = extract_model_info(plaxis_connection["g_i"])
        assert "structures" in info
        assert "phases"     in info
        assert len(info["phases"]) > 0, "Ingen faser i modellen"

    def test_strukturer_har_alle_nøkler(self, plaxis_connection):
        info = extract_model_info(plaxis_connection["g_i"])
        for key in ("plates", "embedded_beams", "node_to_node_anchors",
                    "fixed_end_anchors", "geogrids"):
            assert key in info["structures"], f"Mangler struktur-nøkkel: {key}"

    def test_faser_har_navn(self, plaxis_connection):
        info = extract_model_info(plaxis_connection["g_i"])
        for ph in info["phases"]:
            assert ph.get("name"), f"Fase mangler navn: {ph}"

    def test_plater_har_påkrevde_felt(self, plaxis_connection):
        info   = extract_model_info(plaxis_connection["g_i"])
        plates = info["structures"]["plates"]
        if not plates:
            pytest.skip("Ingen plater i modellen")
        for pl in plates:
            assert "name"         in pl
            assert "display_name" in pl
            assert pl["type"]     == "plate"

    def test_fasenavn_er_unike(self, plaxis_connection):
        info  = extract_model_info(plaxis_connection["g_i"])
        names = [ph["name"] for ph in info["phases"]]
        assert len(names) == len(set(names)), "Duplikate fasenavn funnet"


# ---------------------------------------------------------------------------
# 3. Resolve strukturer og faser
# ---------------------------------------------------------------------------

class TestResolve:

    def test_resolve_structures_finner_plater(self, plaxis_connection):
        g_i  = plaxis_connection["g_i"]
        g_o  = plaxis_connection["g_o"]
        if g_o is None:
            pytest.skip("Plaxis Output ikke tilgjengelig")
        info = extract_model_info(g_i)

        plates = info["structures"]["plates"]
        if not plates:
            pytest.skip("Ingen plater i modellen")

        names    = _plate_names(info)
        resolved = resolve_structures(g_o, {"structures": {"plates": names}})

        assert len(resolved["plates"]) == len(names)

    def test_resolve_phases_finner_faser(self, plaxis_connection):
        g_i  = plaxis_connection["g_i"]
        g_o  = plaxis_connection["g_o"]
        if g_o is None:
            pytest.skip("Plaxis Output ikke tilgjengelig")
        info = extract_model_info(g_i)

        names    = _phase_names(info)
        resolved = resolve_phases(g_o, names)

        assert len(resolved) >= 1, "Klarte ikke å resolve noen faser"

    def test_resolve_ukjent_struktur_gir_tom_liste(self, plaxis_connection):
        g_o  = plaxis_connection["g_o"]
        if g_o is None:
            pytest.skip("Plaxis Output ikke tilgjengelig")
        result = resolve_structures(g_o, {"structures": {"plates": ["Finnes_absolutt_ikke"]}})
        assert result["plates"] == []


# ---------------------------------------------------------------------------
# 4. Ekstraksjon av resultater
# ---------------------------------------------------------------------------

class TestResultEkstraksjon:

    def test_run_msf_returnerer_dict(self, plaxis_connection):
        g_o    = plaxis_connection["g_o"]
        if g_o is None:
            pytest.skip("Plaxis Output ikke tilgjengelig")
        phases = list(g_o.Phases)[:1]

        result = run_msf(g_o, phases)

        assert isinstance(result, dict)
        assert phases[0].Identification.value in result

    def test_run_msf_verdi_er_tallet_eller_none(self, plaxis_connection):
        g_o   = plaxis_connection["g_o"]
        if g_o is None:
            pytest.skip("Plaxis Output ikke tilgjengelig")
        phases = list(g_o.Phases)[:1]
        result = run_msf(g_o, phases)

        for fase, verdi in result.items():
            assert verdi is None or isinstance(verdi, (int, float)), \
                f"Uventet MSF-verdi for {fase}: {verdi!r}"

    def test_run_capacity_returnerer_krefter_for_plate(self, plaxis_connection):
        g_i  = plaxis_connection["g_i"]
        g_o  = plaxis_connection["g_o"]
        if g_o is None:
            pytest.skip("Plaxis Output ikke tilgjengelig")
        info = extract_model_info(g_i)

        plates = info["structures"]["plates"]
        if not plates:
            pytest.skip("Ingen plater i modellen")

        resolved = resolve_structures(g_o, {"structures": {"plates": [plates[0]["name"]]}})
        phases   = list(g_o.Phases)[:1]
        result   = run_capacity(g_o, resolved, phases)

        assert "plates" in result
        plate_name = plates[0]["name"]
        assert plate_name in result["plates"], f"{plate_name} mangler i resultater"

        phase_id = phases[0].Identification.value
        forces   = result["plates"][plate_name][phase_id]
        print(f"\nKrefter — {plate_name} / {phase_id}: {forces}")

        for key in ("Nx", "Q", "M"):
            assert key in forces, f"Kraft-nøkkel '{key}' mangler"

    def test_run_displacement_returnerer_verdier(self, plaxis_connection):
        g_i  = plaxis_connection["g_i"]
        g_o  = plaxis_connection["g_o"]
        if g_o is None:
            pytest.skip("Plaxis Output ikke tilgjengelig")
        info = extract_model_info(g_i)

        plates = info["structures"]["plates"]
        if not plates:
            pytest.skip("Ingen plater i modellen")

        resolved = resolve_structures(g_o, {"structures": {"plates": [plates[0]["name"]]}})
        phases   = list(g_o.Phases)[:1]
        result   = run_displacement(g_o, resolved, phases, component="Ux")

        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# 5. Full runner-kjøring
# ---------------------------------------------------------------------------

class TestFullRunner:
    """Tester hele run_plaxis_extraction fra start til ferdig Excel-fil."""

    def test_full_kjøring_lykkes(self, plaxis_connection, tmp_path):
        from activities.plaxis.runner.runner import run_plaxis_extraction

        if plaxis_connection["g_o"] is None:
            pytest.skip("Plaxis Output ikke tilgjengelig")

        g_i  = plaxis_connection["g_i"]
        info = extract_model_info(g_i)

        plates       = info["structures"]["plates"]
        phase_names  = _phase_names(info)

        if not plates:
            pytest.skip("Ingen plater i modellen")

        job = {
            "structures": {
                "plates":               [plates[0]["name"]],
                "embedded_beams":       [],
                "node_to_node_anchors": [],
                "fixed_end_anchors":    [],
                "geogrids":             [],
            },
            "analysis": {
                "capacity_check": {"enabled": True,  "phases": phase_names},
                "msf":            {"enabled": False, "phases": []},
                "displacement":   {"enabled": True,  "phases": phase_names, "component": "Ux"},
            },
            "resultsPath": {"path": str(tmp_path)},
        }

        framdrift = []
        def _cb(pct, msg):
            framdrift.append((pct, msg))
            print(f"  [{pct:3d}%] {msg}")

        result = run_plaxis_extraction(
            input_port=plaxis_connection["port"],
            input_password=plaxis_connection["password"],
            output_port=plaxis_connection["out_port"],
            output_password=plaxis_connection["password"],
            job=job,
            progress_callback=_cb,
        )

        assert result["success"] is True, f"Kjøring feilet: {result.get('errors')}"

        # Capacity-resultater skal finnes for valgt plate
        assert plates[0]["name"] in result.get("capacity", {}).get("plates", {})

        # Excel-fil skal eksistere
        from pathlib import Path
        excel = result.get("output_file")
        assert excel is not None
        assert Path(excel).exists(), f"Excel-fil ikke funnet: {excel}"

        # Framdrift skal ha blitt logget
        assert len(framdrift) > 0
        assert framdrift[-1][0] == 100

        print(f"\n✅ Excel skrevet til: {excel}")
        print(f"   {len(framdrift)} framdriftssteg logget")

    def test_framdrift_starter_paa_0_og_ender_paa_100(self, plaxis_connection, tmp_path):
        from activities.plaxis.runner.runner import run_plaxis_extraction

        if plaxis_connection["g_o"] is None:
            pytest.skip("Plaxis Output ikke tilgjengelig")

        g_i  = plaxis_connection["g_i"]
        info = extract_model_info(g_i)

        plates = info["structures"]["plates"]
        if not plates:
            pytest.skip("Ingen plater i modellen")

        job = {
            "structures": {"plates": [plates[0]["name"]], "embedded_beams": [],
                           "node_to_node_anchors": [], "fixed_end_anchors": [], "geogrids": []},
            "analysis": {
                "capacity_check": {"enabled": True, "phases": _phase_names(info)},
                "msf":            {"enabled": False, "phases": []},
                "displacement":   {"enabled": False, "phases": []},
            },
            "resultsPath": {"path": str(tmp_path)},
        }

        prosenter = []
        run_plaxis_extraction(
            input_port=plaxis_connection["port"],
            input_password=plaxis_connection["password"],
            job=job,
            progress_callback=lambda pct, _: prosenter.append(pct),
        )

        assert prosenter[0]  <  10,  "Første framdriftssteg skal starte lavt"
        assert prosenter[-1] == 100, "Siste framdriftssteg skal være 100"
        assert prosenter == sorted(prosenter), "Framdrift skal være stigende"
