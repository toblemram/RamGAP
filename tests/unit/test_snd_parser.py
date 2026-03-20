# -*- coding: utf-8 -*-
"""
Unit Tests — SND Parser
========================
Tests for the SND file parser in
backend/activities/geotolk/parsing/snd_parser.py.
Uses real SND-format text snippets — no external files required.
"""

import pytest
from activities.geotolk.parsing.snd_parser import parse_snd_with_events, find_snd_data_start


SAMPLE_SND = """\
*
*
*
*
   Header line 1
   Header line 2
   Header line 3
   0.025  2846  55  79
   0.050  2900  60  80
   0.075  2950  58  81
"""


def test_find_data_start_returns_positive_index():
    lines = SAMPLE_SND.splitlines()
    idx = find_snd_data_start(lines)
    assert idx >= 0


def test_parse_returns_records():
    result = parse_snd_with_events(SAMPLE_SND)
    assert len(result["depth"]) > 0


def test_first_depth_is_small_positive():
    result = parse_snd_with_events(SAMPLE_SND)
    assert result["depth"][0] > 0
    assert result["depth"][0] < 1.0
