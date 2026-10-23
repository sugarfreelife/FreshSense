"""Recognize packaged-food categories from visible label text, with evidence."""

import re

_CATEGORIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Canned fish", ("fish", "tuna", "sardine", "mackerel", "anchovy", "salmon", "pilchard")),
    ("Dairy", ("milk", "curd", "yogurt", "yoghurt", "cheese", "butter", "paneer", "cream", "ghee", "buttermilk")),
    ("Eggs", ("egg", "eggs", "hen egg", "chicken egg", "free range eggs")),
    ("Bread & bakery", ("bread", "loaf", "bun", "rolls", "bakery", "bagel", "toast", "croissant")),
    ("Meat & poultry", ("chicken", "beef", "pork", "mutton", "sausage", "bacon", "ham", "turkey")),
    ("Canned goods", ("canned", "tinned", "tin can", "canned beans", "canned corn", "canned soup")),
    ("Produce", ("apple", "banana", "orange", "tomato", "potato", "onion", "carrot", "lettuce", "spinach", "fruit", "vegetable")),
    ("Beverages", ("juice", "drink", "beverage", "water", "coffee", "tea", "soda", "cola")),
    ("Frozen food", ("frozen", "ice cream", "frozen peas", "frozen meal")),
    ("Snacks & confectionery", ("chips", "crisps", "chocolate", "biscuit", "cookie", "cracker", "candy", "snack")),
    ("Baby food", ("baby food", "infant formula", "infant cereal")),
)

_CAN_WORDS = ("canned", "tinned", "tin can", "in brine", "in oil", "in water")
_NOISE_LINE = re.compile(
    r"\b(exp(?:iry|iration)?|best\s*before|use\s*by|mfg|mfd|packed|batch|lot|net\s*wt|nutrition|ingredients)\b|\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}",
    re.IGNORECASE,
)


def _has_term(text: str, term: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None


def _product_name(raw_text: str, matched_terms: list[str]) -> str | None:
    lines = [re.sub(r"\s+", " ", line).strip(" :-|\t") for line in raw_text.splitlines()]
    for line in lines:
        cleaned = _NOISE_LINE.sub(" ", line)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" :-|\t.,")
        if cleaned and any(_has_term(cleaned.lower(), term) for term in matched_terms):
            return cleaned[:80]
    return matched_terms[0].title() if matched_terms else None


def recognize_product(raw_text: str, user_label: str | None = None) -> dict:
    """Return a conservative category match and the exact text used to make it."""
    text = re.sub(r"\s+", " ", raw_text or "").strip().lower()
    matches = [(category, [term for term in terms if _has_term(text, term)]) for category, terms in _CATEGORIES]
    matches = [(category, terms) for category, terms in matches if terms]

    fish_terms = next((terms for category, terms in matches if category == "Canned fish"), [])
    has_can_cue = any(_has_term(text, term) for term in _CAN_WORDS)
    if fish_terms:
        category = "Canned fish" if has_can_cue else "Seafood"
        matched = fish_terms + ([term for term in _CAN_WORDS if _has_term(text, term)][:1] if has_can_cue else [])
        return {
            "category": category,
            "product_name": _product_name(raw_text, fish_terms),
            "confidence": min(0.95, 0.72 + 0.08 * (len(matched) - 1)),
            "evidence": matched,
            "source": "package_text",
        }

    if matches:
        category, matched = max(matches, key=lambda item: len(item[1]))
        return {
            "category": category,
            "product_name": _product_name(raw_text, matched),
            "confidence": min(0.92, 0.68 + 0.08 * (len(matched) - 1)),
            "evidence": matched,
            "source": "package_text",
        }

    label = (user_label or "").strip()
    if label:
        lowered = label.lower()
        if _has_term(lowered, "fish") and any(_has_term(lowered, term) for term in _CAN_WORDS):
            return {
                "category": "Canned fish",
                "product_name": label[:80],
                "confidence": None,
                "evidence": [f"User label: {label[:80]}"],
                "source": "user_label",
            }
        for category, terms in _CATEGORIES:
            found = [term for term in terms if _has_term(lowered, term)]
            if found:
                return {
                    "category": "Canned fish" if category == "Canned fish" else category,
                    "product_name": label[:80],
                    "confidence": None,
                    "evidence": [f"User label: {label[:80]}"],
                    "source": "user_label",
                }
        return {
            "category": None,
            "product_name": label[:80],
            "confidence": None,
            "evidence": [f"User label: {label[:80]}"],
            "source": "user_label",
        }

    return {"category": None, "product_name": None, "confidence": None, "evidence": [], "source": "unrecognized"}
