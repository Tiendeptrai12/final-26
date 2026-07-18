"""Tests for employee code of conduct and safety guardrails."""
from __future__ import annotations

from antigravity.guardrails import check_input_safety, check_output_safety


def test_input_safety_triggers():
    # Compliant query
    assert check_input_safety("tôi muốn mua máy lạnh inverter Daikin") is None

    # Competitor keyword trigger
    resp1 = check_input_safety("bên điện máy chợ lớn bán rẻ hơn không")
    assert resp1 is not None
    assert "chúng tôi không bình luận về các đối thủ" in resp1["message"]

    # Sensitive/legal trigger
    resp2 = check_input_safety("chính sách chính trị của công ty")
    assert resp2 is not None
    assert "tôi là trợ lý tư vấn sản phẩm" in resp2["message"]


def test_output_safety_filter():
    # Compliant response
    orig = "Dòng Daikin này chạy rất êm và tiết kiệm điện."
    assert check_output_safety(orig) == orig

    # Contains competitor name
    raw1 = "Sản phẩm này có bán ở Nguyễn Kim và Điện Máy Chợ Lớn."
    sanitized1 = check_output_safety(raw1)
    assert "Nguyễn Kim" not in sanitized1
    assert "Chợ Lớn" not in sanitized1

    # Inappropriate phrasing
    raw2 = "máy lạnh này ngu ngốc không nên mua đâu khách hàng khốn nạn"
    sanitized2 = check_output_safety(raw2)
    assert "ngu ngốc" not in sanitized2
    assert "khốn nạn" not in sanitized2
