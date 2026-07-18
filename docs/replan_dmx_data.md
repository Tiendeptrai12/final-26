# Replan — DMX real data drop (schema + mapping overhaul)

Organizer shipped real DMX data + policies + chat logs. This **obsoletes the sparse-Excel
Phase 1 model** and unlocks a much stronger product. NDA: all raw dumps are gitignored; only
derived/aggregate artifacts + this plan are committed.

## What arrived

| Resource | Content | Use |
|----------|---------|-----|
| `products_detail.json` | **13,754 SP · 119 ngành · 100% có giá** (float). Fields: tên, brand, url_image, Giá gốc, Giá khuyến mãi, rating_vote, quantity_sold, màu sắc, phụ kiện, chính sách bảo hành, promotion, outstanding, **spec_product (dict label VN theo ngành)**, onlineSaleOnly, url | New catalog source |
| `products_detail.xlsx` | Same data, Excel | ref |
| `35sample_chat_history.json` | 35 hội thoại thật `{id, messages[{role,content}]}` | eval set + few-shot + intent design |
| `chat_history_buy_product.json` | Luồng mua hàng (có `img_url`,`web_url`; JSON hơi lệch format) | order-flow reference |
| `create_order_dmx` token | `{"role":"assistant","content":"create_order_dmx"}` = tín hiệu tạo đơn | NEW intent/action |
| 6 policy `.md` (bảo hành/đổi trả, giao hàng/lắp đặt, khui hộp Apple, dữ liệu cá nhân, điều khoản, nội quy) + `chat_luong_phuc_vu.md` | Chính sách DMX | policy Q&A (RAG) |

## Delta vs data cũ (sparse Excel)

| | Excel cũ | DMX json mới |
|--|----------|--------------|
| SKU | 1039 aircon | 13,754 toàn ngành |
| Giá | ~25% | **100%** |
| Tên/ảnh/URL | KHÔNG | **CÓ** (demo cards đẹp + click ra DMX) |
| rating / đã bán | KHÔNG | **CÓ** (rating_vote, quantity_sold) → tín hiệu xếp hạng thật |
| bảo hành/promotion/màu/phụ kiện | KHÔNG | CÓ |
| spec | Excel cột phẳng | `spec_product` dict, **label khác** → phải remap |
| stock | unknown | vẫn KHÔNG có (giữ unknown) |

---

## PLAN — chỉnh schema + ánh xạ + hạ nguồn

### P0. NDA (DONE)
`.gitignore` chặn `products_detail.*`, `DMX_product.zip`, `*chat_history*.json`, tất cả policy `.md`, `newnotefromref.md`. Verified untracked.

### P1. Ingest + registry mới (data model đổi hẳn)
- **Nguồn**: đọc thẳng `products_detail.json` (không còn 14 sheet Excel). Copy vào `data/raw/dmx/` (gitignored).
- **Registry mới** (`schemas/registry.json` viết lại): key = `category_name` (119), value = { spec-label→canonical map, parse rules }. Chỉ cần build map cho ngành sẽ rank (aircon trước, rồi top ngành: tủ lạnh, máy giặt, tivi, laptop, quạt…). Ngành chưa map → giữ raw spec, chưa rank.
- **Top-level mapping** (chung mọi ngành):
  `tên sản phẩm`→name · `brand` · `url_image`→image · `url` · `Giá gốc`→original_price · `Giá khuyến mãi`→promotion_price · `rating_vote`→rating(float) · `quantity_sold`→quantity_sold(parse "14,5k"→14500) · `màu sắc`→color · `Phụ kiện đi kèm`→accessories · `chính sách bảo hành`→warranty · `promotion` · `category_name`→category · `onlineSaleOnly` · `product_id`.

### P2. Schema redesign
- `_base.schema.json`: thêm name, image, url, rating, quantity_sold, color, accessories, warranty, promotion, original_price, promotion_price, category (giữ product_id, stock_status=unknown).
- Per-category spec schema: **sinh lại từ spec_product keys thật** (script quét keys theo category, giống `gen_schemas.py` nhưng đọc json). 119 ngành → chỉ validate ngành đã map, còn lại lax.

### P3. Builder viết lại (`build_dmx_catalog.py`)
- Thay `build_btc_catalog.py` (giữ file cũ cho BTC). Đọc json → apply top-level map + per-category spec parse → emit `data/processed/dmx_<cat>.jsonl` + eligible + quality report.
- **effective_price**: `Giá khuyến mãi` nếu >0 else `Giá gốc`. eligibility nới (gần như 100% có giá).
- Aircon spec **remap label mới**:
  - "Phạm vi làm lạnh hiệu quả" → parse area_min/max m²
  - "Độ ồn trung bình…" → indoor_noise_db (1 giá trị, không còn 3)
  - "Công suất làm lạnh" → cooling_capacity_btu
  - "Inverter" (field riêng) → inverter bool
  - "Loại Gas", "Tiêu thụ điện"(W), "Công nghệ tiết kiệm điện" → gas, power_w, energy_tech
  - ⚠️ **KHÔNG có CSPF/energy_stars** như cũ → đổi tín hiệu energy sang `power_w` (thấp hơn = tốt) hoặc energy_tech. Ranking energy phải sửa.

### P4. Ranking cập nhật
- `aircon_ranking.py`: đổi field đọc theo canonical mới; energy score từ CSPF→`power_w`/energy_tech. Thêm tín hiệu mới: **rating + quantity_sold** (đã bán nhiều + rating cao = boost nhẹ, có thật trong data). Tie-break: rating → quantity_sold → giá (thay tie-break stock đã bỏ).
- Cards/explainer thêm name, image, url, rating, promotion → grounding giàu hơn (đúng data 10%).

### P5. Năng lực MỚI mở khóa
- **create_order intent** (Call C mở rộng): phát hiện ý định chốt/mua → xác nhận → emit `create_order_dmx` (UI-only demo, không backend giỏ hàng). Thêm nhánh vào flow.
- **Policy Q&A (RAG nhẹ)**: 6 policy md → chunk + retrieve (keyword hoặc FPT `Vietnamese_Embedding`) → trả lời bảo hành/giao hàng/đổi trả/dữ liệu grounded. Lưu ý: flow cũ "no vector DB" — policy Q&A là lý do chính đáng để thêm retrieval nhẹ.
- **Eval set**: 35 hội thoại thật → trích cặp (user query → slot/intent kỳ vọng) làm test độ chính xác extract + intent (#7 cũ). Few-shot cho prompt.
- Cards click ra `url` DMX thật (name/image) → demo thuyết phục.

### P6. Migration / cái gì vỡ
- `CATALOG_SOURCE`: thêm giá trị `dmx` (giữ `btc`/`mock`). `load_category` đọc `dmx_<cat>.jsonl`.
- Tests: builder cũ (`test_extract.py`) giữ cho BTC; thêm `test_dmx_build.py` cho parser mới. Ranking test cập nhật field mới.
- guard_agent.yaml: stock vẫn unknown (giữ `no_stock_claims`). Scope mở rộng 119 ngành nhưng rank chỉ vài ngành → `scope_guard` message "ngành X chưa hỗ trợ so sánh sâu".

## Đề xuất thứ tự (48h)
1. **P1+P3 aircon-only trên data mới** — giữ pipeline chạy, đổi nguồn sang DMX thật (name/image/url/rating). ROI cao nhất, demo nhảy vọt.
2. **P4** tận dụng rating/quantity_sold + cards giàu.
3. **P5 create_order** (nhánh chốt đơn) — có trong note BTC, ăn điểm AI-native.
4. **P5 policy RAG** nếu dư giờ.
5. Mở thêm 2-3 ngành hot (tủ lạnh/máy giặt/tivi) nếu còn thời gian.
