def choose_best(products):
    """Decision made in code, never by the model."""
    ok = [p for p in products if p.price_inr > 0]
    return min(ok, key=lambda p: p.price_inr) if ok else None

MAX_SPEND_INR = 2000
BLOCKED_ACTIONS = {"place_order", "pay", "confirm_purchase"}

def gate(action: str, amount: float = 0):
    if action in BLOCKED_ACTIONS:
        return False, "irreversible: needs human approval"
    if amount > MAX_SPEND_INR:
        return False, "over spend cap"
    return True, "ok"