"""Accessory cross-sell tests — necessity + grounding. Pure code, synthetic, no API."""
from __future__ import annotations

from antigravity import accessory


def _pool():
    return [
        {"product_id": "OP1", "category_name": "Ốp lưng, miếng dán", "tên sản phẩm": "Ốp A",
         "Giá gốc": 50000, "quantity_sold": "5k", "rating_vote": "4.8", "url": "u/OP1"},
        {"product_id": "OP2", "category_name": "Ốp lưng, miếng dán", "tên sản phẩm": "Ốp B",
         "Giá gốc": 60000, "quantity_sold": "100", "rating_vote": "4.0", "url": "u/OP2"},
        {"product_id": "SAC1", "category_name": "Sạc, cáp", "tên sản phẩm": "Sạc 20W",
         "Giá gốc": 130000, "quantity_sold": "2k", "url": "u/SAC1"},
        {"product_id": "TUI1", "category_name": "Balo, túi chống sốc", "tên sản phẩm": "Túi laptop",
         "Giá gốc": 300000, "url": "u/TUI1"},
    ]


def test_standalone_product_gets_no_accessory():
    for cat in ["Lò vi sóng", "Nồi cơm điện", "Quạt các loại", "Tủ lạnh", "Máy giặt"]:
        assert accessory.needed_accessory_categories({"category_name": cat}) == []


def test_phone_needs_case_and_charger():
    need = accessory.needed_accessory_categories(
        {"category_name": "Điện thoại", "Phụ kiện đi kèm": ""})
    assert "Ốp lưng, miếng dán" in need and "Sạc, cáp" in need


def test_inbox_charger_skips_charger():
    # laptop ships a charger in the box -> don't upsell a charger, bag still ok
    need = accessory.needed_accessory_categories(
        {"category_name": "Laptop", "Phụ kiện đi kèm": "Bộ sản phẩm gồm: Sạc Laptop 65W, Thùng máy"})
    assert "Balo, túi chống sốc" in need
    # Laptop map has no "Sạc, cáp" entry anyway; assert the skip logic on phone instead
    phone_need = accessory.needed_accessory_categories(
        {"category_name": "Điện thoại", "Phụ kiện đi kèm": "Hộp có: Sạc nhanh, Cáp"})
    assert "Sạc, cáp" not in phone_need


def test_suggestions_are_real_and_ranked():
    phone = {"category_name": "Điện thoại", "Phụ kiện đi kèm": ""}
    out = accessory.suggest_accessories(phone, _pool(), per_category=1)
    ids = [o["product_id"] for o in out]
    assert "OP1" in ids and "SAC1" in ids       # real SKUs pulled from pool
    # within Ốp category, higher-sold OP1 (5k) beats OP2 (100)
    op = [o for o in out if o["category"] == "Ốp lưng, miếng dán"]
    assert op and op[0]["product_id"] == "OP1"
    for o in out:                                # grounded fields only
        assert o["product_id"] and o["name"] and o["url"]


def test_standalone_suggest_returns_empty():
    assert accessory.suggest_accessories({"category_name": "Lò vi sóng"}, _pool()) == []
