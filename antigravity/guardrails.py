"""Code of Conduct (SOP) Guardrails for Điện Máy Xanh AI Advisor.

Provides input interception (safety checks) for special customer scenarios and
output sanitization to guarantee polite tone and brand neutrality.
"""
from __future__ import annotations

import re
from typing import Any

# Forbidden hyperbolic words -> neutral alternatives (case-insensitive regex)
BANNED_REPLACEMENTS = {
    re.compile(r"\bđỉnh\b", re.IGNORECASE): "phù hợp",
    re.compile(r"\bbá đạo\b", re.IGNORECASE): "đáp ứng tốt",
    re.compile(r"\bsố\s*một\b", re.IGNORECASE): "nổi bật",
    re.compile(r"\bngon\b", re.IGNORECASE): "thích hợp",
    re.compile(r"\bbest\b", re.IGNORECASE): "ưu tiên",
    re.compile(r"\bhoàn\s*hảo\b", re.IGNORECASE): "phù hợp nhất",
}


def check_input_safety(text: str) -> dict[str, Any] | None:
    """Check user input against special SOP scenarios and return predefined response if matched.

    If no special scenario matches, returns None to allow the normal pipeline to run.
    """
    if not text:
        return None

    low = text.lower()

    # Competitor check
    if any(k in low for k in ("chợ lớn", "cho lon", "nguyễn kim", "nguyen kim", "mediamart", "đối thủ", "doi thu")):
        return {
            "query": text,
            "mode": "safety_block",
            "message": (
                "Dạ, chúng tôi không bình luận về các đối thủ cạnh tranh. Nếu anh/chị cần so sánh thông số kỹ thuật của các sản phẩm, em rất sẵn lòng hỗ trợ ạ."
            ),
            "profile": {},
            "safety_checked": True,
        }

    # Sensitive / Political / Legal check
    if any(k in low for k in ("chính trị", "chinh tri", "tôn giáo", "ton giao", "phản động", "phan dong", "đảng", "dang")):
        return {
            "query": text,
            "mode": "safety_block",
            "message": (
                "Dạ, tôi là trợ lý tư vấn sản phẩm của Điện Máy Xanh, em không thể trả lời các câu hỏi ngoài phạm vi tư vấn sản phẩm và dịch vụ của Điện Máy Xanh được ạ."
            ),
            "profile": {},
            "safety_checked": True,
        }

    # Situation 1: Complex questions, complaints, out of stock, lottery info
    if any(k in low for k in ("khiếu nại", "lỗi nặng", "thái độ", "trúng thưởng", "hết hàng toàn quốc", "lừa đảo")):
        return {
            "query": text,
            "mode": "handoff",
            "message": (
                "Dạ, để tư vấn/hỗ trợ về vấn đề này một cách tốt nhất và nhanh chóng, anh/chị có thể để lại số điện thoại "
                "để bên em gọi lại ngay, hoặc gọi trực tiếp đến tổng đài miễn phí 1900.232.461 (7:30 - 22:00) / "
                "chat qua Zalo OA Điện máy XANH để các bạn nhân viên hỗ trợ xử lý ngay lập tức cho mình ạ."
            ),
            "profile": {},
            "safety_checked": True,
        }

    # Situation 2: Used or display clearance products
    if any(k in low for k in ("máy cũ", "máy trưng bày", "thanh lý", "qua sử dụng", "hàng cũ", "trưng bày thanh lý")):
        return {
            "query": text,
            "mode": "clearance",
            "message": (
                "Dạ Anh/Chị ơi, các dòng máy trưng bày hoặc máy đã qua sử dụng bên em sẽ có chính sách bảo hành riêng "
                "theo tình trạng từng máy chứ không áp dụng gói bảo hành 12 tháng như máy mới hoàn toàn đâu ạ. "
                "Để xem chính xác máy đó còn bảo hành bao lâu và ngoại hình thực tế thế nào, anh/chị nhắn giúp em "
                "Số điện thoại để các bạn nhân viên tại siêu thị gần mình chụp hình gửi anh/chị xem trực tiếp nha!"
            ),
            "profile": {},
            "safety_checked": True,
        }

    # Situation 3: Data privacy/security concerns
    if any(k in low for k in ("bảo mật", "lộ thông tin", "sợ mất sđt", "bảo mật dữ liệu", "an toàn thông tin")):
        return {
            "query": text,
            "mode": "privacy",
            "message": (
                "Dạ anh/chị hoàn toàn yên tâm ạ! Hệ thống bên em luôn tuân thủ nghiêm ngặt Chính sách xử lý dữ liệu cá nhân. "
                "Mọi thông tin anh/chị cung cấp (Họ tên, SĐT, địa chỉ) đều được bảo mật tuyệt đối và chỉ sử dụng minh bạch "
                "vào mục đích lên đơn, giao hàng và làm phiếu bảo hành chính hãng cho mình thôi ạ."
            ),
            "profile": {},
            "safety_checked": True,
        }

    # Situation 5: Apple rules (payment, khui seal)
    if ("apple" in low or "iphone" in low or "ipad" in low or "macbook" in low) and any(
        k in low for k in ("nhận hàng", "quy trình", "kiểm tra", "khui seal", "mở hộp", "seal", "active", "kích hoạt")
    ):
        return {
            "query": text,
            "mode": "apple_policy",
            "message": (
                "Dạ anh/chị lưu ý giúp em một chút đối với sản phẩm Apple ạ: Theo quy định bắt buộc của hãng, "
                "mình cần thanh toán 100% giá trị sản phẩm trước khi khui (mở) hộp. Ngay khi mở hộp, anh/chị và "
                "nhân viên giao hàng sẽ cùng kiểm tra lỗi thẩm mỹ ngoại quan (bụi màn hình, trầy xước) và tiến hành "
                "kích hoạt bảo hành điện tử ngay tại chỗ để đảm bảo quyền lợi đổi mới nếu có lỗi cho mình nhé ạ."
            ),
            "profile": {},
            "safety_checked": True,
        }

    # Situation 6: Late night / remote delivery (>30km)
    if any(k in low for k in ("giao đêm", "giao khuya", "giao trễ", "giao muộn", "giao sau 18h", "giao sau 22h", "giao vượt mốc")):
        return {
            "query": text,
            "mode": "delivery_policy",
            "message": (
                "Dạ Anh/Chị thông cảm giúp em, do đặc thù kỹ thuật lắp đặt an toàn nên mốc giờ giao muộn nhất trong ngày "
                "bên em là trước 18h00 (đối với máy lạnh) và trước 22h00 (đối với tivi, tủ lạnh, máy giặt...) ạ. "
                "Do đơn mình đặt muộn/địa chỉ hơi xa kho xuất hàng nên em xin phép hẹn giao sản phẩm cho mình từ 14h00 "
                "ngày mai trở đi nha, trước khi đi các bạn giao hàng sẽ alo trước cho mình ạ."
            ),
            "profile": {},
            "safety_checked": True,
        }

    # Situation 7: Over-booking / Hoarding (>3 items)
    if re.search(r"\b(mua|đặt|giữ|giữ\s*chỗ)\s*([4-9]|\d{2,})\s*(cái|chiếc|máy|tivi|điện\s*thoại)", low):
        return {
            "query": text,
            "mode": "hoarding_prevent",
            "message": (
                "Dạ Anh/Chị ơi, để đảm bảo công bằng cho tất cả khách hàng đều mua được sản phẩm giá tốt, "
                "quy định hệ thống bên em là một số điện thoại chỉ đặt giữ chỗ được tối đa 3 sản phẩm cùng lúc và không trùng loại với nhau ạ. "
                "Nếu mình cần mua số lượng lớn cho công ty hoặc công trình, anh/chị cho em xin SĐT để phòng kinh doanh "
                "bên em liên hệ làm hợp đồng và tính mức chiết khấu tốt nhất cho mình nha!"
            ),
            "profile": {},
            "safety_checked": True,
        }

    # Situation 8: Change of mind return (no defect)
    if any(k in low for k in ("đổi ý", "không thích nữa", "trả lại máy không lỗi", "trả hàng không lỗi")):
        return {
            "query": text,
            "mode": "return_policy",
            "message": (
                "Dạ Anh/Chị ơi, chính sách 'Hư gì đổi nấy' trong 1 tháng đầu tiên bên em là dành riêng cho sản phẩm bị lỗi kỹ thuật "
                "từ nhà sản xuất ạ. Trường hợp máy dùng hoàn toàn bình thường nhưng mình đổi ý muốn trả lại hoặc đổi dòng khác, "
                "bên em sẽ tiến hành tính phí đổi trả theo quy định của hệ thống. Anh/Chị cho em xin số điện thoại mua hàng để "
                "em chuyển các bạn kiểm tra mức phí chính xác nhất cho mình nhé."
            ),
            "profile": {},
            "safety_checked": True,
        }

    # Situation 9: Lost accessory return
    if any(k in low for k in ("mất phụ kiện", "mất sạc", "mất remote", "mất tai nghe", "mất dây cáp", "lạc mất")):
        return {
            "query": text,
            "mode": "lost_accessory",
            "message": (
                "Dạ không sao đâu anh/chị đừng lo ạ! Máy mình bị lỗi kỹ thuật trong tháng đầu thì bên em vẫn hỗ trợ đổi máy mới cho mình. "
                "Tuy nhiên, do mình làm lạc mất phụ kiện đi kèm, nên theo quy định bên em sẽ trừ một khoản phí nhỏ (tối đa bằng 5% giá trị máy) "
                "để bù lại phụ kiện đó ạ. Anh/chị cứ mang máy ra siêu thị gần nhất, các bạn nhân viên sẽ hỗ trợ xử lý đổi máy mới cho mình liền ạ."
            ),
            "profile": {},
            "safety_checked": True,
        }

    # Situation 10: Commercial usage
    if any(k in low for k in ("kinh doanh", "thương mại", "mở tiệm", "tiệm giặt", "nhà hàng", "quán ăn", "tiệm giặt ủi")):
        return {
            "query": text,
            "mode": "commercial_use",
            "message": (
                "Dạ Anh/Chị lưu ý giúp em một chút ạ, các chính sách ưu đãi đổi trả '1 đổi 1' tại hệ thống bên em áp dụng cho nhu cầu "
                "sử dụng cá nhân hoặc gia đình. Nếu mình mua máy để phục vụ mục đích kinh doanh thương mại (như tiệm giặt ủi, nhà hàng, "
                "quán ăn...), sản phẩm sẽ được áp dụng chế độ bảo hành sửa chữa tận nơi của hãng theo đúng quy định của nhà sản xuất "
                "chứ không áp dụng chính sách đổi trả miễn phí của siêu thị ạ."
            ),
            "profile": {},
            "safety_checked": True,
        }

    return None


def check_output_safety(text: str) -> str:
    """Sanitize the chatbot response to guarantee polite tone and replace prohibited hyperbolic words.
    """
    if not text:
        return text

    cleaned = text.strip()

    # Replace competitor names
    cleaned = re.sub(r"Nguyễn Kim", "siêu thị khác", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"Điện Máy Chợ Lớn", "siêu thị khác", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"Chợ Lớn", "siêu thị khác", cleaned, flags=re.IGNORECASE)

    # Replace inappropriate phrasing
    cleaned = re.sub(r"ngu ngốc", "chưa tối ưu", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"khốn nạn", "khách hàng", cleaned, flags=re.IGNORECASE)

    # Replace forbidden marketing/hyperbolic words
    for pat, rep in BANNED_REPLACEMENTS.items():
        cleaned = pat.sub(rep, cleaned)

    return cleaned
