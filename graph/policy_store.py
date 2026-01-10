# graph/policy_store.py

ALLOWED_CATEGORIES = {
    "order",
    "billing",
    "account",
    "technical",
}

OUT_OF_SCOPE_KEYWORDS = {
    "image generation",
    "dating advice",
    "medical advice",
    "legal advice",
    "stock prediction",
}

def is_category_allowed(category: str) -> bool:
    return category in ALLOWED_CATEGORIES
