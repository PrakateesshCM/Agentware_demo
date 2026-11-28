from pydantic import BaseModel, Field, field_validator

class Product(BaseModel):
    title: str = Field(max_length=200)
    price_inr: float = Field(gt=0, lt=1_000_000)
    rating: float | None = Field(default=None, ge=0, le=5)
    url: str

    @field_validator("title")
    @classmethod
    def no_instructions(cls, v):
        bad = ("ignore previous", "ignore all", "system prompt", "AGW-CANARY")
        if any(b in v.lower() for b in bad):
            raise ValueError("suspicious text in title")
        return v

PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "price_inr": {"type": "number"},
        "rating": {"type": "number"},
    },
    "required": ["title", "price_inr"],
}