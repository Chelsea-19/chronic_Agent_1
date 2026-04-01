"""
app.services.parser — NLP parsing utilities for health data and meals.

Preserved from the original chronic_agent/agent/parser.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ParsedTrack:
    event_type: str
    value_text: str
    value_num1: float | None = None
    value_num2: float | None = None
    unit: str = ""


GLUCOSE_PATTERN = re.compile(r"([0-9]+(?:\.[0-9]+)?)")
BP_PATTERN = re.compile(r"([0-9]{2,3})\s*/\s*([0-9]{2,3})")
WEIGHT_PATTERN = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*(?:kg|公斤)?", re.I)


def parse_track_message(raw: str) -> ParsedTrack:
    text = raw.replace("[TRACK]", "", 1).strip()
    if "血压" in text:
        m = BP_PATTERN.search(text)
        if m:
            return ParsedTrack("blood_pressure", text, float(m.group(1)), float(m.group(2)), "mmHg")
    if "空腹血糖" in text:
        m = GLUCOSE_PATTERN.search(text)
        if m:
            return ParsedTrack("fasting_glucose", text, float(m.group(1)), None, "mmol/L")
    if "餐后血糖" in text:
        m = GLUCOSE_PATTERN.search(text)
        if m:
            return ParsedTrack("postprandial_glucose", text, float(m.group(1)), None, "mmol/L")
    if "体重" in text:
        m = WEIGHT_PATTERN.search(text)
        if m:
            return ParsedTrack("weight", text, float(m.group(1)), None, "kg")
    if "症状" in text:
        return ParsedTrack("symptom", text.replace("症状", "", 1).strip())
    if "饮食" in text or "吃了" in text:
        return ParsedTrack("meal", text, None, None, "")
    return ParsedTrack("note", text, None, None, "")


def detect_meal_risks(text: str) -> list[str]:
    tags: list[str] = []
    lowered = text.lower()
    if any(k in text for k in ["奶茶", "可乐", "果汁", "糖水", "甜品"]) or "sugar" in lowered:
        tags.append("高糖饮食")
    if any(k in text for k in ["两碗", "米饭", "面条", "粥", "馒头", "粉", "年糕", "包子"]):
        tags.append("高碳水")
    if any(k in text for k in ["红烧肉", "肥牛", "火锅", "烧烤", "炸鸡", "排骨"]):
        tags.append("高脂")
    if any(k in text for k in ["咸菜", "火腿", "泡面", "卤味", "腊肉"]):
        tags.append("高盐")
    return tags


def estimate_meal_metrics(text: str) -> tuple[float | None, float | None]:
    carbs = 45.0
    sodium = 600.0
    if any(k in text for k in ["两碗", "大份", "加面", "双拼"]):
        carbs += 30
    if any(k in text for k in ["奶茶", "甜品", "可乐", "果汁"]):
        carbs += 25
    if any(k in text for k in ["火锅", "卤味", "泡面", "腊肉", "咸菜"]):
        sodium += 700
    if "沙拉" in text or "蔬菜" in text:
        carbs -= 10
    return max(carbs, 10), max(sodium, 100)
