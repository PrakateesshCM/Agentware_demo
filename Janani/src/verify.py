import re


def first_price(content: str):
    """The first rupee amount in the page text (the selling price on Amazon)."""
    m = re.search(r"₹\s?([\d,]+(?:\.\d\d)?)", content)
    return float(m.group(1).replace(",", "")) if m else None


def price_in_content(price, content: str) -> bool:
    """True only if the extracted price equals the first price shown on the page."""
    fp = first_price(content)
    return bool(price) and fp is not None and abs(fp - float(price)) < 1


def find_rating(content: str):
    """Return a rating only if the page text actually states one."""
    m = re.search(r"(\d(?:\.\d)?)\s*out of 5", content)
    return float(m.group(1)) if m else None