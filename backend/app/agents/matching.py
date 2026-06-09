"""Lightweight phrase/item matching used by the checklist agent.

Deterministic token matching with a small synonym map so user phrases like
"bedsheets" line up with catalog items like "Twin XL Sheet Set". A phrase
matches an item only when *all* of the phrase's significant tokens are present
in the item's tokens, which avoids false positives (e.g. "desk lamp" should not
match "Desk Organizer").
"""

from __future__ import annotations

import re

from app.models.schemas import DormItem

# Map normalized synonyms onto a shared canonical token.
SYNONYMS: dict[str, str] = {
    "bedsheet": "sheet",
    "sheet": "sheet",
    "bedding": "sheet",
    "linen": "sheet",
    "duvet": "comforter",
    "blanket": "comforter",
    "refrigerator": "fridge",
    "minifridge": "fridge",
    "hanger": "hanger",
    "lamp": "lamp",
    "towel": "towel",
    "pillow": "pillow",
}

# Tokens that carry no matching signal and are dropped from phrases.
_STOPWORDS = {
    "set", "pack", "piece", "pieces", "pc", "pcs", "new", "of", "and",
    "the", "a", "an", "my", "some", "with", "for",
}


def _normalize_token(word: str) -> str:
    w = re.sub(r"[^a-z]", "", word.lower())
    if len(w) > 3 and w.endswith("s"):
        w = w[:-1]
    return SYNONYMS.get(w, w)


def tokenize(text: str) -> set[str]:
    tokens = {_normalize_token(part) for part in re.split(r"[^a-zA-Z]+", text)}
    return {t for t in tokens if t}


def _item_tokens(item: DormItem) -> set[str]:
    return tokenize(item.item_id) | tokenize(item.name)


def phrase_matches_item(phrase: str, item: DormItem) -> bool:
    phrase_tokens = {t for t in tokenize(phrase) if t not in _STOPWORDS}
    if not phrase_tokens:
        return False
    return phrase_tokens.issubset(_item_tokens(item))


def match_any(phrases: list[str], item: DormItem) -> bool:
    return any(phrase_matches_item(p, item) for p in phrases)
