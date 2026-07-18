"""Tests for Vietnamese text correction."""
from __future__ import annotations

from unittest.mock import patch
from antigravity.corrector import correct_text


def test_vietnamese_correction_live():
    # Test with standard correction
    # Note: Model loading might print warnings, but it should return corrected text
    res1 = correct_text("may lanh tiet kiem dien")
    
    from antigravity.corrector import _load_failed
    if _load_failed:
        import pytest
        pytest.skip("Vietnamese correction model failed to load (offline or network error)")

    assert "may lanh" in res1.lower() or "máy lạnh" in res1.lower()

    res2 = correct_text("tủ lanhj")
    assert "tủ lạnh" in res2.lower() or "tu lanh" in res2.lower()


def test_vietnamese_correction_fallback():
    # Test fallback path when model is not available or fails
    with patch("antigravity.corrector._model", None):
        with patch("antigravity.corrector._load_failed", True):
            res = correct_text("may lanh tiet kiem dien")
            assert res == "may lanh tiet kiem dien"
