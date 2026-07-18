"""Order intent + create_order_dmx tests. Pure code, no LLM/API."""
from __future__ import annotations

from antigravity import order, nlu


def test_detect_order_intent_positive():
    for t in ["đặt hàng", "mua con này", "chốt Daikin", "order luôn", "tạo đơn", "mua"]:
        assert order.detect_order_intent(t) is True


def test_detect_order_intent_negative():
    for t in ["so sánh giá", "tư vấn máy lạnh", "phòng 18m2", "cái nào tiết kiệm điện"]:
        assert order.detect_order_intent(t) is False


def test_order_response_grounded_and_action():
    sel = {"product_id": "A", "name": "Daikin demo", "brand": "Daikin",
           "price": 15_390_000, "url": "http://dmx/A"}
    r = order.build_order_response(sel)
    assert r["mode"] == "order" and r["action"] == "create_order_dmx"
    assert r["order"]["product_id"] == "A" and r["order"]["price"] == 15_390_000
    assert r["order"]["stock_status"] == "unknown"       # never claims availability
    assert "15.4 triệu" in r["message"]


def test_order_response_no_selection_asks():
    r = order.build_order_response(None)
    assert r["mode"] == "order" and r["action"] is None and r["order"] is None
    assert "sản phẩm nào" in r["message"]


def test_build_chat_response_routes_order():
    sel = {"product_id": "A", "name": "Daikin demo", "brand": "Daikin", "price": 9_000_000}
    r = nlu.build_chat_response("đặt hàng", selected_product=sel, explain=False)
    assert r["mode"] == "order" and r["action"] == "create_order_dmx"
    import json
    json.dumps(r, ensure_ascii=False)   # JSON-safe
