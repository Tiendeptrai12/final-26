"""Direct product comparison + abstract-criterion steering (grounded, deterministic).

Two edge behaviors for the "3 best products" flow:

1. COMPARISON MODE — the customer already knows ≥2 specific products and just wants them
   compared. Follow-up questions (hỏi ngược) and ranking/relaxation are pointless here, so
   the caller skips straight to `compare()`, a spec-by-spec table built ONLY from real record
   fields (never fabricated; missing field -> "chưa có dữ liệu").

2. ABSTRACT NEED — a soft need like "mua cho trẻ em" / "cho người già" / "cho sinh viên".
   `priority_rerank_query()` turns that into the top signal for the semantic reranker so it
   drives selection, instead of being buried in the raw query.

Pure code, $0, no LLM. The caller (pipeline) decides routing; this module supplies the
grounded engine.
"""
from __future__ import annotations

import re
from typing import Any

# --------------------------------------------------------------------------- #
# 1. comparison intent
# --------------------------------------------------------------------------- #
_COMPARE_PATTERNS = [
    r"\bso\s*sánh\b", r"\bkhác\s*(nhau|biệt)\b", r"\bcái\s*nào\s*(tốt|hơn|ngon)\b",
    r"\bnên\s*(chọn|mua|lấy)\b.+\b(hay|hoặc|với)\b", r"\b(giữa)\b.+\b(và|hay)\b",
    r"\bcon\s*nào\b", r"\b(vs|versus)\b",
]
_COMPARE_RE = re.compile("|".join(_COMPARE_PATTERNS), re.IGNORECASE)


def detect_comparison_intent(text: str) -> bool:
    """True when the user wants to compare specific products (not seek a recommendation)."""
    return bool(_COMPARE_RE.search((text or "").strip().lower()))


# --------------------------------------------------------------------------- #
# grounded spec-by-spec comparison
# --------------------------------------------------------------------------- #
def _num(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


# (accessor, label, direction) — direction: "low" better small, "high" better large, None neutral
_FIELDS = [
    (lambda it, s: it.get("price"), "Giá", "low", lambda v: f"{v/1_000_000:.1f} triệu"),
    (lambda it, s: it.get("rating"), "Đánh giá", "high", lambda v: f"{v}/5"),
    (lambda it, s: it.get("quantity_sold"), "Đã bán", "high", lambda v: f"{int(v):,}".replace(",", ".")),
    (lambda it, s: s.get("indoor_noise_min_db"), "Độ ồn (dB)", "low", lambda v: f"{v:g} dB"),
    (lambda it, s: s.get("power_kwh"), "Tiêu thụ điện", "low", lambda v: f"{v:g} kWh"),
    (lambda it, s: s.get("cspf"), "CSPF", "high", lambda v: f"{v:g}"),
]


def compare(products: list[dict[str, Any]]) -> dict[str, Any]:
    """Grounded comparison of ≥2 real products. Rows use only fields present on records.

    Returns {mode, products[], rows[{label, values[], winner_idx|None}]}. `winner_idx` is the
    index of the best product for that row (or None when tied / not enough data). Never invents.
    """
    prods = [
        {"product_id": p.get("product_id"), "name": p.get("name") or p.get("tên sản phẩm"),
         "brand": p.get("brand"), "price": p.get("price") or p.get("effective_price"),
         "url": p.get("url")}
        for p in products
    ]
    rows: list[dict[str, Any]] = []
    for accessor, label, direction, fmt in _FIELDS:
        raw_vals = []
        for p in products:
            spec = p.get("spec") or {}
            v = accessor(p, spec)
            # normalize price from top-level fallback
            if v is None and label == "Giá":
                v = p.get("effective_price")
            raw_vals.append(_num(v))
        if sum(1 for v in raw_vals if v is not None) < 2:
            continue  # need at least 2 real values to compare this field
        display = [fmt(v) if v is not None else "chưa có dữ liệu" for v in raw_vals]
        present = [(i, v) for i, v in enumerate(raw_vals) if v is not None]
        winner_idx = None
        if direction in ("low", "high") and present:
            winner_idx = (min if direction == "low" else max)(present, key=lambda t: t[1])[0]
        rows.append({"label": label, "values": display, "winner_idx": winner_idx})
    return {"mode": "comparison", "products": prods, "rows": rows}


# --------------------------------------------------------------------------- #
# 2. abstract-need steering for the reranker
# --------------------------------------------------------------------------- #
# abstract lifestyle needs -> the concrete relevance phrase the reranker should prioritize.
_ABSTRACT_NEEDS = {
    r"trẻ\s*em|em\s*bé|con\s*nhỏ|baby": "an toàn cho trẻ em, kháng khuẩn, vận hành êm",
    r"người\s*già|ông\s*bà|cao\s*tuổi": "dễ sử dụng, vận hành êm, an toàn cho người già",
    r"sinh\s*viên|phòng\s*trọ|giá\s*rẻ": "giá rẻ, tiết kiệm điện, gọn nhẹ",
    r"gia\s*đình\s*đông|nhiều\s*người": "công suất lớn, dung tích lớn cho gia đình đông người",
    r"phòng\s*ngủ": "vận hành êm, ít ồn cho phòng ngủ",
}


def extract_abstract_need(text: str) -> str | None:
    """Return the concrete relevance phrase for an abstract lifestyle need, else None."""
    low = (text or "").lower()
    for pat, phrase in _ABSTRACT_NEEDS.items():
        if re.search(pat, low):
            return phrase
    return None


def priority_rerank_query(base_query: str, text: str | None = None) -> str:
    """Front-load an abstract need so the reranker treats it as the TOP criterion.

    If `text` (or base_query) carries an abstract need, its concrete phrase is placed first
    and emphasized; otherwise the base query is returned unchanged.
    """
    phrase = extract_abstract_need(text or base_query)
    if not phrase:
        return base_query
    return f"{phrase}. {base_query}"
