"""
Текстовые ресурсы бота: системный промпт, реплики, имена, NSFW-паттерны.
Загружает данные из resources/ при импорте модуля.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

from config import RESOURCES_DIR

# ---------------------------------------------------------------------------
# Загрузка системного промпта (лор персонажа)
# ---------------------------------------------------------------------------
_PROMPT_PATH = Path(RESOURCES_DIR) / "prompt.md"


def _load_prompt() -> str:
    """Читает resources/prompt.md один раз при старте."""
    with open(_PROMPT_PATH, encoding="utf-8") as f:
        return f.read().strip()


def_prompt: str = _load_prompt()


# ---------------------------------------------------------------------------
# Загрузка реплик из phrases.json
# ---------------------------------------------------------------------------
_PHRASES_PATH = Path(RESOURCES_DIR) / "phrases.json"


def _load_phrases() -> dict:
    """Читает resources/phrases.json."""
    with open(_PHRASES_PATH, encoding="utf-8") as f:
        return json.load(f)


_phrases = _load_phrases()

# Списки реплик (доступны как texts.ping_an, texts.image_responses и т.д.)
bot_names: list[str] = _phrases["bot_names"]
image_responses: list[str] = _phrases["image_responses"]
ping_an: list[str] = _phrases["ping_an"]
pic_comments: list[str] = _phrases["pic_comments"]
hug_pleased: list[str] = _phrases["hug_pleased"]
censor_phrases: list[str] = _phrases["censor_phrases"]
expie_censor_replies: list[str] = _phrases["expie_censor_replies"]

_couple_phrases: list[str] = _phrases["couple_phrases"]
_hug_phrases: list[str] = _phrases["hug_phrases"]


# ---------------------------------------------------------------------------
# Шаблоны (функции)
# ---------------------------------------------------------------------------
def couple(name1: str, name2: str) -> str:
    """Случайная реплика для команды /шип."""
    template = random.choice(_couple_phrases)
    return template.format(name1=name1, name2=name2)


def hug(mention: str) -> str:
    """Случайная реплика для команды /обнять."""
    template = random.choice(_hug_phrases)
    return template.format(mention=mention)


# ---------------------------------------------------------------------------
# NSFW-паттерны (regex — остаётся в коде, а не в JSON)
# ---------------------------------------------------------------------------
nsfw_patterns: list[str] = [
    r"\bnsfw\b",
    r"\bexplicit\b",
    r"\bporn\b",
    r"\bsex(?:ual)?\b",
    r"\bnude\b",
    r"\bnaked\b",
    r"\bpenis\b",
    r"\bvagina\b",
    r"\bbreasts?\b",
    r"\bnipple\b",
    r"\berection\b",
    r"\borgasm\b",
    r"\bhentai\b",
    r"\bgore\b",
    r"\bviolence\b",
    r"\bcum\b",
    r"\bsemen\b",
    r"\b\+18\b",
    r"\b18\+\b",
    r"\bxxx\b",
]
