"""Phase 4 explainer tests. fpt_client mocked -> $0, no real API in CI."""
from __future__ import annotations

import pytest

from antigravity import explainer, fpt_client
from antigravity.aircon_ranking import NeedProfile


def _items():
    return [
        {"brand": "Daikin", "product_id": "A", "price": 15_390_000,
         "spec": {"indoor_noise_min_db": 19, "cspf": 6.2, "area_min_m2": 15,
                  "area_max_m2": 20, "inverter": True}},
        {"brand": "LG", "product_id": "B", "price": 16_090_000,
         "spec": {"indoor_noise_min_db": 21, "cspf": 5.8, "area_min_m2": 15,
                  "area_max_m2": 20, "inverter": True}},
    ]


PROFILE = NeedProfile(budget_max=20_000_000, area_m2=18, priority="quiet")


# --- facts block feeds ONLY grounded numbers (anti-hallucination surface) ----
def test_facts_block_contains_only_given_numbers():
    fb = explainer._facts_block(_items(), PROFILE)
    assert "Daikin" in fb and "15.4 triệu" in fb and "19 dB" in fb and "CSPF 6.2" in fb
    assert "LG" in fb and "16.1 triệu" in fb
    # need line reflects the profile, nothing invented
    assert "ngân sách tối đa 20 triệu" in fb and "phòng 18m²" in fb


def test_facts_block_omits_missing_fields():
    items = [{"brand": "X", "product_id": "X", "price": None, "spec": {}}]
    fb = explainer._facts_block(items, NeedProfile())
    assert "triệu" not in fb.split("SẢN PHẨM")[1]  # no price stated when absent
    assert "dB" not in fb and "CSPF" not in fb


# --- explain_top -------------------------------------------------------------
def test_explain_top_returns_prose(monkeypatch):
    monkeypatch.setattr(fpt_client, "chat_completion",
                        lambda *a, **k: "Daikin êm hơn, LG tiết kiệm điện hơn.")
    out = explainer.explain_top(_items(), PROFILE)
    assert out == "Daikin êm hơn, LG tiết kiệm điện hơn."


def test_explain_top_empty_items_returns_none():
    assert explainer.explain_top([], PROFILE) is None


def test_explain_top_llm_error_returns_none(monkeypatch):
    def boom(*a, **k):
        raise fpt_client.FPTError("timeout")
    monkeypatch.setattr(fpt_client, "chat_completion", boom)
    assert explainer.explain_top(_items(), PROFILE) is None


def test_explain_top_blank_content_returns_none(monkeypatch):
    monkeypatch.setattr(fpt_client, "chat_completion", lambda *a, **k: "   ")
    assert explainer.explain_top(_items(), PROFILE) is None
