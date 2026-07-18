"""Comparison + abstract-need steering tests. Pure code, no API."""
from __future__ import annotations

from antigravity import comparison as cmp


def test_detect_comparison_intent():
    for t in ["so sánh Daikin và LG", "cái nào tốt hơn", "nên mua A hay B", "con nào ngon hơn"]:
        assert cmp.detect_comparison_intent(t) is True
    for t in ["tư vấn máy lạnh phòng 18m2", "máy lạnh dưới 20 triệu"]:
        assert cmp.detect_comparison_intent(t) is False


def test_compare_grounded_winner_per_field():
    a = {"product_id": "A", "name": "Daikin", "price": 15_400_000, "rating": 4.8,
         "spec": {"indoor_noise_min_db": 19, "power_kwh": 0.8}}
    b = {"product_id": "B", "name": "LG", "price": 16_100_000, "rating": 4.5,
         "spec": {"indoor_noise_min_db": 21, "power_kwh": 0.7}}
    out = cmp.compare([a, b])
    assert out["mode"] == "comparison" and len(out["products"]) == 2
    rows = {r["label"]: r for r in out["rows"]}
    assert rows["Giá"]["winner_idx"] == 0        # cheaper A
    assert rows["Độ ồn (dB)"]["winner_idx"] == 0  # quieter A
    assert rows["Tiêu thụ điện"]["winner_idx"] == 1  # lower kWh B


def test_compare_missing_field_says_no_data():
    a = {"product_id": "A", "name": "A", "price": 10_000_000, "spec": {"indoor_noise_min_db": 20}}
    b = {"product_id": "B", "name": "B", "price": 12_000_000, "spec": {}}
    out = cmp.compare([a, b])
    noise = [r for r in out["rows"] if r["label"] == "Độ ồn (dB)"]
    assert noise == []  # only 1 product has noise -> field skipped (never fabricated)


def test_abstract_need_becomes_top_rerank_criterion():
    q = cmp.priority_rerank_query("máy lạnh 15 triệu", "mua máy lạnh cho trẻ em")
    assert q.startswith("an toàn cho trẻ em")
    assert cmp.priority_rerank_query("máy lạnh 15 triệu", "phòng 18m2") == "máy lạnh 15 triệu"


def test_extract_abstract_need():
    assert cmp.extract_abstract_need("cho người già dùng") is not None
    assert cmp.extract_abstract_need("phòng 20m2") is None
