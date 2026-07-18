"""Module to parse chat history and provide few-shot examples from historical dialogues.

Provides robust parsing of the malformed chat_history_buy_product.json.
"""
from __future__ import annotations

import os
import re
import json
import logging
from typing import Any
import dirtyjson

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_PATH = os.path.join(BASE_DIR, "chat_history_buy_product.json")
SAMPLE_HISTORY_PATH = os.path.join(BASE_DIR, "35sample_chat_history (1).json")

def load_and_clean_history() -> list[dict[str, Any]]:
    """Load both history files and clean them for parsing."""
    conversations = []
    
    # 1. Load chat_history_buy_product.json (malformed)
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            fixed = re.sub(r'\{\s*\{\s*"role":', '{\n    "messages": [\n      {"role":', content)
            fixed = re.sub(r'\}\s*\{\s*"role":', '},\n      {"role":', fixed)
            data = dirtyjson.loads(fixed)
            conversations.extend([dict(conv) for conv in data])
        except Exception as e:
            logger.error(f"Failed to parse chat_history_buy_product.json: {e}")
            
    # 2. Load 35sample_chat_history (1).json (clean JSON)
    if os.path.exists(SAMPLE_HISTORY_PATH):
        try:
            with open(SAMPLE_HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            conversations.extend([dict(conv) for conv in data])
        except Exception as e:
            logger.error(f"Failed to parse 35sample_chat_history (1).json: {e}")
            
    return conversations

def extract_dialogue_turns(conversations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract turns, combining consecutive user or assistant messages."""
    turns = []
    
    for conv in conversations:
        messages = conv.get("messages", [])
        msg_dicts = [dict(m) for m in messages if m is not None]
        
        # Merge consecutive messages of the same role
        merged_msgs = []
        current_msg = None
        for msg in msg_dicts:
            role = msg.get("role")
            content = msg.get("content") or ""
            if not role or not content.strip():
                continue
            
            if current_msg and current_msg["role"] == role:
                current_msg["content"] += " " + content.strip()
            else:
                if current_msg:
                    merged_msgs.append(current_msg)
                current_msg = {"role": role, "content": content.strip(), "web_url": msg.get("web_url", "")}
        if current_msg:
            merged_msgs.append(current_msg)
            
        # Build dialogue turns
        context_turns = []
        for i in range(len(merged_msgs)):
            msg = merged_msgs[i]
            role = msg["role"]
            content = msg["content"]
            
            if role == "user" and content:
                # Find the next assistant message
                assistant_reply = ""
                if i + 1 < len(merged_msgs) and merged_msgs[i + 1]["role"] == "assistant":
                    assistant_reply = merged_msgs[i + 1]["content"]
                
                if assistant_reply:
                    context_str = ""
                    if context_turns:
                        context_str = "\n".join([f"{t['role']}: {t['content']}" for t in context_turns[-3:]])
                        
                    turns.append({
                        "user_query": content,
                        "assistant_response": assistant_reply,
                        "context": context_str,
                        "web_url": msg.get("web_url", "")
                    })
                    
            context_turns.append({"role": "Khách hàng" if role == "user" else "Trợ lý", "content": content})
            
    return turns

def get_few_shot_prompt(few_shots: list[dict[str, Any]]) -> str:
    """Format a list of few-shot examples into a system prompt segment."""
    if not few_shots:
        return ""
        
    prompt = "Dưới đây là một số ví dụ tham khảo về cách tư vấn cskh của Điện Máy Xanh:\n\n"
    for idx, fs in enumerate(few_shots, 1):
        prompt += f"Ví dụ {idx}:\n"
        if fs.get("context"):
            prompt += f"Bối cảnh:\n{fs['context']}\n"
        prompt += f"Khách hàng: {fs['user_query']}\n"
        prompt += f"Trợ lý Điện Máy Xanh: {fs['assistant_response']}\n"
        prompt += "-" * 20 + "\n"
    return prompt

def load_price_segments() -> dict[str, dict[str, float]]:
    """Load price segment percentiles from Moc_Phan_Khuc_119_Category.xlsx."""
    path = "d:/download/Moc_Phan_Khuc_119_Category.xlsx"
    segments = {}
    
    # Static fallback for core categories
    fallback = {
        "Laptop": {"low": 15490000.0, "budget": 24690000.0, "mid": 30490000.0, "premium": 39990000.0, "high": 149990000.0},
        "Tủ lạnh": {"low": 2550000.0, "budget": 11260000.0, "mid": 17190000.0, "premium": 26040000.0, "high": 129000000.0},
        "Pc, máy in": {"low": 170000.0, "budget": 2490000.0, "mid": 4290000.0, "premium": 13067500.0, "high": 250000000.0},
        "Máy lạnh": {"low": 7190000.0, "budget": 10990000.0, "mid": 15040000.0, "premium": 25340000.0, "high": 69790000.0}
    }
    
    if not os.path.exists(path):
        return fallback
        
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        sheet = wb.active
        for row in sheet.iter_rows(min_row=6):
            vals = [cell.value for cell in row]
            if len(vals) >= 8 and vals[1] is not None:
                cat_name = str(vals[1]).strip()
                segments[cat_name] = {
                    "low": float(vals[3]) if vals[3] is not None else 0.0,
                    "budget": float(vals[4]) if vals[4] is not None else 0.0,
                    "mid": float(vals[5]) if vals[5] is not None else 0.0,
                    "premium": float(vals[6]) if vals[6] is not None else 0.0,
                    "high": float(vals[7]) if vals[7] is not None else 0.0
                }
    except Exception as e:
        logger.error(f"Failed to load price segments Excel: {e}")
        return fallback
        
    # Merge missing defaults
    for k, v in fallback.items():
        if k not in segments:
            segments[k] = v
            
    return segments

def get_segment_guidelines_prompt(category_name: str) -> str:
    """Build rules for the LLM to map abstract segment words to exact numeric prices."""
    segments = load_price_segments()
    
    # Normalize category name matching
    matched_cat = None
    for cat in segments:
        if category_name.lower() in cat.lower() or cat.lower() in category_name.lower():
            matched_cat = cat
            break
            
    if not matched_cat:
        return ""
        
    s = segments[matched_cat]
    prompt = f"\nQUY TẮC MỐC PHÂN KHÚC GIÁ cho ngành hàng '{matched_cat}' (áp dụng khi khách hàng đề cập phân khúc thay vì số tiền cụ thể):\n"
    prompt += f"  - 'giá rẻ' / 'bình dân' / 'tiết kiệm': budget_max = {int(s['budget']):,}đ\n"
    prompt += f"  - 'tầm trung' / 'trung cấp' / 'vừa phải': budget_min = {int(s['budget']):,}đ, budget_max = {int(s['premium']):,}đ\n"
    prompt += f"  - 'cao cấp' / 'sang trọng' / 'đắt tiền': budget_min = {int(s['premium']):,}đ\n"
    return prompt
