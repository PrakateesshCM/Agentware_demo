import re
import sys

from pydantic import BaseModel, Field

from llm import ask_json
from discovery import trace

SYSTEM = (
    "You extract shopping requirements from a user request. "
    'Return JSON with keys: "item" (short product name, e.g. "men formal shirt"), '
    '"max_price_inr" (number or null), "color" (string or null). '
    "Return only JSON."
)


class Request(BaseModel):
    item: str = Field(min_length=2, max_length=80)
    max_price_inr: float | None = Field(default=None, gt=0, lt=1_000_000)
    color: str | None = Field(default=None, max_length=30)


def parse_request(text: str) -> Request:
    try:
        req = Request(**ask_json(SYSTEM, text[:300]))
    except Exception as e:
        trace("parse_failed", error=str(e), fallback="raw text")
        req = Request(item=re.sub(r"[^\w\s'-]", "", text)[:80] or "shirt")
    req.item = re.sub(r"[^\w\s'-]", "", req.item).strip()   # plain words only
    trace("request_parsed", item=req.item, max_price=req.max_price_inr, color=req.color)
    return req


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or "navy formal shirt under 1000 rupees"
    print(parse_request(text))