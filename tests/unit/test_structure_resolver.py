# -*- coding: utf-8 -*-
"""
Unit Tests — Structure Resolver
================================
Tester resolve_structures og resolve_phases uten live Plaxis-tilkobling.
Bruker mock-objekter som etterligner Plaxis Output API-et.
"""

import pytest
from unittest.mock import MagicMock

from activities.plaxis.extraction.structure_resolver import resolve_structures, resolve_phases


# ---------------------------------------------------------------------------
# Hjelpere
# ---------------------------------------------------------------------------

def _obj(name: str) -> MagicMock:
    """Lag et mock-element med Name.value."""
    o = MagicMock()
    o.Name.value = name
    return o


def _phase(identification: str) -> MagicMock:
    """Lag et mock-fase med Identification.value."""
    p = MagicMock()
    p.Identification.value = identification
    return p


def _g_o_with_plates(*names):
    """Lag et mock g_o med de gitte platene."""
    g = MagicMock()
    g.Plates = [_obj(n) for n in names]
    g.EmbeddedBeamRows = []
    g.NodeToNodeAnchors = []
    g.FixedEndAnchors = []
    g.Geogrids = []
    return g


# ---------------------------------------------------------------------------
# resolve_structures
# ---------------------------------------------------------------------------

class TestResolveStructures:

    def test_matcher_plate_paa_navn(self):
        plate = _obj("Spunt_venstre")
        g = _g_o_with_plates("Spunt_venstre", "Spunt_høyre")
        g.Plates = [plate, _obj("Spunt_høyre")]

        result = resolve_structures(g, {"structures": {"plates": ["Spunt_venstre"]}})

        assert result["plates"] == [plate]

    def test_ignorerer_plater_som_ikke_er_valgt(self):
        plate_a = _obj("Spunt_A")
        plate_b = _obj("Spunt_B")
        g = MagicMock()
        g.Plates = [plate_a, plate_b]
        g.EmbeddedBeamRows = g.NodeToNodeAnchors = g.FixedEndAnchors = g.Geogrids = []

        result = resolve_structures(g, {"structures": {"plates": ["Spunt_A"]}})

        assert plate_a in result["plates"]
        assert plate_b not in result["plates"]

    def test_tom_valgliste_gir_tom_resultat(self):
        g = _g_o_with_plates("Spunt_A")
        result = resolve_structures(g, {"structures": {"plates": []}})
        assert result["plates"] == []

    def test_manglende_attributt_paa_g_o_krasjer_ikke(self):
        """Hvis g_o ikke har EmbeddedBeamRows skal resolve ikke krasje."""
        g = MagicMock(spec=[])   # ingen attributter i det hele tatt
        job = {"structures": {"plates": ["Spunt_A"], "embedded_beams": ["Pile_1"]}}

        result = resolve_structures(g, job)

        assert result["plates"] == []
        assert result["embedded_beams"] == []

    def test_flere_strukturtyper_samtidig(self):
        plate  = _obj("Spunt_1")
        anchor = _obj("Anker_1")
        g = MagicMock()
        g.Plates = [plate]
        g.EmbeddedBeamRows = []
        g.NodeToNodeAnchors = [anchor]
        g.FixedEndAnchors = []
        g.Geogrids = []

        result = resolve_structures(g, {
            "structures": {
                "plates":               ["Spunt_1"],
                "node_to_node_anchors": ["Anker_1"],
            }
        })

        assert result["plates"] == [plate]
        assert result["node_to_node_anchors"] == [anchor]

    def test_ukjent_navn_gir_tom_liste(self):
        g = _g_o_with_plates("Spunt_A")
        result = resolve_structures(g, {"structures": {"plates": ["Finnes_ikke"]}})
        assert result["plates"] == []

    def test_ingen_strukturer_i_job_gir_tomme_lister(self):
        g = _g_o_with_plates("Spunt_A")
        result = resolve_structures(g, {"structures": {}})
        for key in result:
            assert result[key] == []


# ---------------------------------------------------------------------------
# resolve_phases
# ---------------------------------------------------------------------------

class TestResolvePhases:

    def test_eksakt_match(self):
        phase = _phase("Utgraving til bunn")
        g = MagicMock()
        g.Phases = [phase]

        result = resolve_phases(g, ["Utgraving til bunn"])
        assert result == [phase]

    def test_prefiks_match_med_plaxis_suffiks(self):
        """Plaxis legger til '[Phase_N]' i Identification — vi matcher bare prefiks."""
        phase = _phase("Utgraving til bunn [Phase_4]")
        g = MagicMock()
        g.Phases = [phase]

        result = resolve_phases(g, ["Utgraving til bunn"])
        assert result == [phase]

    def test_ukjent_fase_ikke_inkludert(self):
        g = MagicMock()
        g.Phases = [_phase("Initial phase")]

        result = resolve_phases(g, ["Ukjent fase"])
        assert result == []

    def test_flere_faser_riktig_rekkefølge(self):
        ph1 = _phase("Fase 1")
        ph2 = _phase("Fase 2")
        ph3 = _phase("Fase 3")
        g = MagicMock()
        g.Phases = [ph1, ph2, ph3]

        result = resolve_phases(g, ["Fase 2", "Fase 1"])

        assert ph1 in result
        assert ph2 in result
        assert ph3 not in result

    def test_tom_navneliste_gir_tomt_resultat(self):
        g = MagicMock()
        g.Phases = [_phase("Fase 1")]
        assert resolve_phases(g, []) == []

    def test_ingen_duplikate_faser(self):
        """Samme fase skal ikke legges til to ganger selv om den matcher to navn."""
        phase = _phase("FoS analyse")
        g = MagicMock()
        g.Phases = [phase]

        result = resolve_phases(g, ["FoS analyse", "FoS analyse"])
        assert len(result) == 1

    def test_alle_faser_i_modellen_kan_resolves(self):
        faser = ["Initial phase", "Installasjon spunt", "Utgraving nivå 1", "FoS analyse"]
        g = MagicMock()
        g.Phases = [_phase(n) for n in faser]

        result = resolve_phases(g, faser)
        assert len(result) == len(faser)
