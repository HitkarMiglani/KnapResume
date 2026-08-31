import pytest

from app.normalization import NormalizationError, normalize_fact


def test_trims_outer_whitespace():
    assert normalize_fact("  Built a thing  ") == "Built a thing"


def test_strips_one_leading_bullet_marker():
    assert normalize_fact("- Built a thing") == "Built a thing"
    assert normalize_fact("* Built a thing") == "Built a thing"
    assert normalize_fact("• Built a thing") == "Built a thing"


def test_collapses_horizontal_whitespace():
    assert normalize_fact("Built  a\tthing") == "Built a thing"


def test_nfc_normalizes_unicode():
    decomposed = "cafe\u0301"  # "café" as e + combining acute accent
    assert normalize_fact(decomposed) == "café"


def test_rejects_empty_input():
    with pytest.raises(NormalizationError):
        normalize_fact("   ")


def test_rejects_multiline_input():
    with pytest.raises(NormalizationError):
        normalize_fact("Built a thing\nand another")


def test_rejects_over_max_length():
    with pytest.raises(NormalizationError):
        normalize_fact("x" * 501)
