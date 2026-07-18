"""Accessory cross-sell — suggest complementary accessories for a chosen product.

Advisor scope, grounded: suggestions are REAL accessory SKUs pulled from the DMX catalog
(never invented), and only offered when they make sense. The "when NOT to suggest" rules are
guardrails (see antigravity/.agents/guard_agent.yaml → accessory_suggestion):
  1. Only categories in ACCESSORY_MAP get suggestions. Standalone appliances (lò vi sóng,
     nồi cơm, quạt, bàn ủi, tủ lạnh, máy giặt…) are NOT in the map → no accessory.
  2. Skip an accessory type already bundled in the box (product's "Phụ kiện đi kèm"):
     e.g. laptops ship with a charger → don't upsell a charger, but a bag/mouse is fine.
  3. Suggestions come from the catalog only (real id/name/price/url) — anti-hallucination.

Necessity is category- + spec-driven, exactly as required. Pure code, deterministic, $0.
"""
from __future__ import annotations

from typing import Any

# product category_name -> list of (accessory category_name, in-box skip keyword | None).
# If the product's "Phụ kiện đi kèm" text contains the keyword, that accessory type is
# already included and is skipped. Categories NOT listed here get NO suggestions.
ACCESSORY_MAP: dict[str, list[tuple[str, str | None]]] = {
    "Điện thoại": [
        ("Ốp lưng, miếng dán", None),
        ("Sạc, cáp", "sạc"),
        ("Sạc dự phòng", None),
        ("Miếng dán Camera", None),
    ],
    "Máy tính bảng": [
        ("Phụ kiện tablet", None),
        ("Ốp lưng, miếng dán", None),
        ("Sạc, cáp", "sạc"),
    ],
    "Laptop": [
        ("Balo, túi chống sốc", None),
        ("Chuột, bàn phím", None),
        ("Hub, cáp kết nối", None),
        ("Ổ cứng di động", None),
    ],
    "Pc, máy in": [
        ("Chuột, bàn phím", None),
        ("USB", None),
        ("Ổ cứng di động", None),
    ],
    "Tivi": [
        ("Khung treo Tivi", "khung treo"),
    ],
    "Đồng hồ thông minh": [
        ("Dây đồng hồ", None),
    ],
    "Máy ảnh và phụ kiện": [
        ("Thẻ nhớ", None),
        ("Túi đựng phụ kiện", None),
    ],
    "Camera": [
        ("Thẻ nhớ", None),
    ],
    "Máy lạnh": [
        ("Phụ kiện máy lạnh", None),
    ],
}


def _category(product: dict[str, Any]) -> str | None:
    """Handle both raw DMX (category_name) and canonical (category) shapes."""
    return product.get("category_name") or product.get("_category_name")


def _inbox_text(product: dict[str, Any]) -> str:
    v = product.get("Phụ kiện đi kèm") or product.get("accessories") or ""
    return str(v).lower()


def needed_accessory_categories(product: dict[str, Any]) -> list[str]:
    """Accessory categories worth suggesting for this product (necessity guard).

    [] when the product is standalone (not in ACCESSORY_MAP) or every relevant accessory
    is already bundled in the box.
    """
    cat = _category(product)
    rules = ACCESSORY_MAP.get(cat or "")
    if not rules:
        return []
    inbox = _inbox_text(product)
    out: list[str] = []
    for acc_cat, skip_kw in rules:
        if skip_kw and skip_kw in inbox:
            continue  # already included in the box
        out.append(acc_cat)
    return out


def _acc_item(p: dict[str, Any]) -> dict[str, Any]:
    """Grounded accessory card — only real record fields."""
    price = p.get("Giá khuyến mãi") or p.get("Giá gốc") or p.get("price")
    return {
        "product_id": p.get("product_id"),
        "name": p.get("tên sản phẩm") or p.get("name"),
        "brand": p.get("brand"),
        "category": p.get("category_name") or p.get("category"),
        "price": int(price) if isinstance(price, (int, float)) and price else None,
        "url": p.get("url"),
    }


def suggest_accessories(
    product: dict[str, Any], pool: list[dict[str, Any]], *, per_category: int = 2,
) -> list[dict[str, Any]]:
    """Real accessory suggestions for `product`, drawn only from `pool` (the catalog).

    `pool` = candidate accessory products (raw DMX or canonical dicts). Returns [] when
    nothing is needed. Within each needed category, picks the most-sold/best-rated real
    items — never fabricates.
    """
    wanted = needed_accessory_categories(product)
    if not wanted:
        return []
    wanted_set = set(wanted)

    by_cat: dict[str, list[dict[str, Any]]] = {}
    for p in pool:
        c = p.get("category_name") or p.get("category")
        if c in wanted_set:
            by_cat.setdefault(c, []).append(p)

    def _rank_key(p: dict[str, Any]):
        # more sold, then higher rating (both from the record; missing -> 0)
        sold = str(p.get("quantity_sold") or "0")
        try:
            sold_n = float(sold.lower().replace("k", "000").replace(",", "").replace(".", ""))
        except ValueError:
            sold_n = 0.0
        try:
            rating = float(str(p.get("rating_vote") or p.get("rating") or 0).replace(",", "."))
        except ValueError:
            rating = 0.0
        return (-sold_n, -rating)

    out: list[dict[str, Any]] = []
    for acc_cat in wanted:                       # preserve map order
        items = sorted(by_cat.get(acc_cat, []), key=_rank_key)[:per_category]
        out.extend(_acc_item(p) for p in items)
    return out
