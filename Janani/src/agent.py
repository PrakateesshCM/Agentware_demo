import sys

from parse_request import parse_request
from discovery import find_products, trace


def pick_best(products, max_price, color):
    """Decision made in plain code. The model never chooses."""
    in_budget = [p for p in products if max_price is None or p.price_inr <= max_price]
    if not in_budget:
        return None, "no product within budget"

    def color_match(p):
        return bool(color) and color.lower() in p.title.lower()

    # Prefer: colour match, then a stated rating, then higher rating, then lower price
    in_budget.sort(key=lambda p: (
        not color_match(p),
        p.rating is None,
        -(p.rating or 0),
        p.price_inr,
    ))
    best = in_budget[0]
    reason = f"within budget; colour match={color_match(best)}; rating={best.rating}"
    return best, reason


def run(request_text: str):
    trace("run_start", request=request_text[:200])
    req = parse_request(request_text)

    query = f"{req.item} {req.color or ''} india".replace("  ", " ").strip()
    products = find_products(query)
    trace("candidates", count=len(products))

    best, reason = pick_best(products, req.max_price_inr, req.color)
    if best is None:
        trace("no_selection", reason=reason)
        print(f"No suitable product found ({reason}).")
        return None

    trace("selected", url=best.url, price=best.price_inr, reason=reason)
    print(f"Selected: {best.title[:80]}")
    print(f"Price: ₹{best.price_inr:.0f} | Rating: {best.rating} | {best.url}")
    print(f"Why: {reason}")
    return best


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or "navy formal shirt under 1000 rupees"
    run(text)