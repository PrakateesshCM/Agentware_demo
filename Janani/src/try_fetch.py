from dotenv import load_dotenv
load_dotenv()

from keenable import Keenable

client = Keenable()
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "price_inr": {"type": "number"},
        "rating": {"type": "number"},
    },
    "required": ["title", "price_inr"],
}
url = "https://amazon.in/Arrow-Mens-Checkered-Formal-Shirt/dp/B0FWCVC1X3"
resp = client.fetch([url], schema=schema, max_chars=6000)
for p in resp.results:
    print("title:", p.title)
    print("error:", p.error)
    print("structured:", p.structured)