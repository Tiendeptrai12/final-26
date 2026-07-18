"""Evaluation script for few-shot and price-segment NLU slot extraction.
"""
from __future__ import annotations

import sys
import os
import json

# Setup path and encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from antigravity.vector_db import search_few_shots, initialize_vector_db
from antigravity.fpt_client import chat_completion, NLU_MODEL
from antigravity.nlu import _SYSTEM_PROMPT, coerce_profile, extract_need_profile

# Test queries for few-shot & price segment experiments
TEST_QUERIES = [
    # 1. Segment-based queries (using Moc_Phan_Khuc_119_Category.xlsx thresholds)
    "Tôi muốn mua điều hòa Daikin phân khúc bình dân",
    "Tư vấn cho mình tủ lạnh Toshiba cao cấp cỡ lớn",
    "Cần mua laptop Asus phục vụ văn phòng phân khúc trung cấp",
    
    # 2. Traditional queries
    "Tìm cho mình tủ lạnh Toshiba hoặc LG cỡ 300 lít tầm 10 triệu đổ lại",
    "Cần một con laptop Asus mỏng nhẹ học tập văn phòng khoảng 15 triệu"
]

def run_experiment(query: str):
    print("=" * 60)
    print(f"TRUY VẤN: {query}\n")
    
    # 1. Zero-shot slot extraction (Standard Prompt only)
    print("--- 1. Kết quả Zero-shot (Không có ví dụ & Không có mốc phân khúc) ---")
    zero_shot_messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]
    try:
        zero_shot_raw = chat_completion(NLU_MODEL, zero_shot_messages, timeout=5.0)
        print("Raw LLM response:")
        print(zero_shot_raw)
        try:
            profile = coerce_profile(json.loads(zero_shot_raw))
            print("Parsed NeedProfile:", vars(profile))
        except Exception:
            print("Failed to parse JSON")
    except Exception as e:
        print(f"Zero-shot LLM call failed: {e}")
        
    print()
    
    # 2. Retrieve matched examples from Qdrant
    print("--- 2. Truy xuất ví dụ tương tự từ Qdrant ---")
    few_shots = search_few_shots(query, limit=2)
    for idx, fs in enumerate(few_shots, 1):
        print(f"Ví dụ {idx}:")
        print(f"  Khách hàng: {fs['user_query']}")
        print(f"  Trợ lý: {fs['assistant_response'][:120]}...")
    print()
    
    # 3. Combined NLU Pipeline (Few-Shots + Price Segment thresholds from Excel)
    print("--- 3. Kết quả Pipeline NLU (Có Few-Shots Qdrant + Mốc giá Excel) ---")
    try:
        profile, missing, raw_obj = extract_need_profile(query, timeout=5.0)
        print("Raw LLM response:")
        print(json.dumps(raw_obj, ensure_ascii=False))
        print("Parsed NeedProfile:", vars(profile))
        print("Missing slots:", missing)
    except Exception as e:
        print(f"Pipeline NLU call failed: {e}")
    print("=" * 60 + "\n")

def main():
    initialize_vector_db()
    for query in TEST_QUERIES:
        run_experiment(query)

if __name__ == "__main__":
    main()
