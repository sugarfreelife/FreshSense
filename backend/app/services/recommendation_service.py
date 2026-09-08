"""Human-readable recommendation helper."""

RECOMMENDATION_TEXT = {
    "CONSUME_NOW": "Product appears fresh. Consume normally.",
    "CONSUME_SOON": "Product is still usable but should be consumed soon.",
    "CAUTION_DO_NOT_CONSUME": "Caution: signs of spoilage or expiry. Do not consume.",
    "CHECK_EXPIRY": "Unable to determine freshness reliably. Check the expiry label manually.",
}


def describe(recommendation: str) -> str:
    return RECOMMENDATION_TEXT.get(recommendation, "No recommendation available.")
