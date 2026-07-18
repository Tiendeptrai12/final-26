"""Order intent + create_order_dmx action (buy-flow close, UI-only demo).

Organizer convention: the assistant emits {"role":"assistant","content":"create_order_dmx"}
to signal a successful order creation. This module detects buy intent in code (deterministic,
$0, no LLM) and builds a grounded order payload from ONLY the selected product's real fields —
no fabricated price/spec, and stock stays unknown (never claim "còn hàng"). No cart backend:
the demo confirms in the UI and returns the action signal.
"""
from __future__ import annotations

import re
from typing import Any

CREATE_ORDER_ACTION = "create_order_dmx"

# buy / confirm intent — Vietnamese. Kept tight so "so sánh giá" etc. don't trip it.
_ORDER_PATTERNS = [
    r"\bđặt\s*(hàng|mua|đơn)\b", r"\bmua\s*(ngay|luôn|con|cái|máy|này|nó)\b",
    r"\bchốt\b", r"\blấy\s*(con|cái|máy)?\s*này\b", r"\border\b",
    r"\btạo\s*đơn\b", r"\bmua\s*nó\b", r"^mua$",
]
_ORDER_RE = re.compile("|".join(_ORDER_PATTERNS), re.IGNORECASE)


def detect_order_intent(text: str) -> bool:
    """True when the user wants to buy/confirm (deterministic keyword match)."""
    return bool(_ORDER_RE.search((text or "").strip().lower()))


def build_order_response(selected: dict[str, Any] | None) -> dict[str, Any]:
    """Grounded order confirmation. `selected` is a ranked item dict (real fields only).

    Returns the flat chat contract shape with mode="order" + action=create_order_dmx.
    Never invents price/stock; if no product is selected, ask which one.
    """
    base: dict[str, Any] = {
        "mode": "order",
        "action": None,
        "order": None,
        "items": [],
        "questions": [],
        "safety_checked": True,
    }
    if not selected or not selected.get("product_id"):
        base["message"] = "Bạn muốn đặt sản phẩm nào? Vui lòng chọn một trong các gợi ý trên."
        return base

    name = selected.get("name") or selected.get("brand") or selected.get("product_id")
    price = selected.get("price")
    order = {
        "product_id": selected.get("product_id"),
        "name": name,
        "brand": selected.get("brand"),
        "price": price,                       # from record only
        "url": selected.get("url"),
        "quantity": 1,
        "stock_status": "unknown",            # never claim availability
    }
    price_txt = f" — {price/1_000_000:.1f} triệu" if isinstance(price, (int, float)) else ""
    base["action"] = CREATE_ORDER_ACTION
    base["order"] = order
    base["message"] = (
        f"Đã tạo đơn hàng cho {name}{price_txt}. Nhân viên Điện Máy Xanh sẽ liên hệ xác nhận "
        f"tồn kho và giao hàng. Cảm ơn bạn đã tin tưởng ạ!"
    )
    return base
