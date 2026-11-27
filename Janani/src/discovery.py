import json
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv
load_dotenv()

from keenable import Keenable
from keenable.errors import KeenableConnectionError
from models import Product, PRODUCT_SCHEMA
from verify import price_in_content, find_rating

ALLOWED_DOMAINS = {"amazon.in", "flipkart.com", "localhost"}

# Search each store separately and keep only real product-page URLs
STORES = {
    "amazon.in":    {"hint": "amazon.in",    "product_path": "/dp/"},
    "flipkart.com": {"hint": "flipkart.com", "product_path": "/p/"},
}

TRACE_FILE = Path(__file__).resolve().parent.parent / "traces" / "run.jsonl"

client = Keenable()  # reads KEENABLE_API_KEY from the environment


def trace(event: str, **data):
    TRACE_FILE.parent.mkdir(exist_ok=True)
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.time(), "event": event, **data}, default=str) + "\n")


def with_retry(fn, *args, tries=3, **kwargs):
    """Retry on network errors, logging each attempt. Re-raises after the last try."""
    for attempt in range(1, tries + 1):
        try:
            return fn(*args, **kwargs)
        except KeenableConnectionError as e:
            trace("network_error", attempt=attempt, error=str(e)[:200])
            if attempt == tries:
                raise
            time.sleep(2 ** attempt)  # waits 2s, then 4s


def host_matches(url: str, domain: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host == domain or host.endswith("." + domain)


def is_allowed(url: str) -> bool:
    """Exact domain or a real subdomain. 'amazon.in.evil.com' does not match."""
    return any(host_matches(url, d) for d in ALLOWED_DOMAINS)


def is_product_page(url: str) -> bool:
    path = urlparse(url).path
    for domain, cfg in STORES.items():
        if host_matches(url, domain):
            return cfg["product_path"] in path
    return True  # localhost mock shop etc.


def clean_url(url: str) -> str:
    """Strip Amazon tracking junk (?psc=..., /ref=...). Other sites keep their query."""
    p = urlparse(url)
    if host_matches(url, "amazon.in"):
        return urlunparse((p.scheme, p.netloc, p.path.split("/ref=")[0], "", "", ""))
    return url


def search_urls(query: str, max_results: int = 8) -> list[str]:
    urls = []
    for domain, cfg in STORES.items():
        q = f"{query} {cfg['hint']}"
        try:
            results = with_retry(client.search, q, max_results=max_results, disable_cards=True)
        except TypeError:  # older SDK without disable_cards
            results = with_retry(client.search, q, max_results=max_results)

        for r in results:
            cleaned = clean_url(r.url)
            if not is_allowed(r.url):
                trace("url_dropped", url=r.url, reason="host not allowlisted")
            elif not is_product_page(r.url):
                trace("url_dropped", url=r.url, reason="not a product page")
            elif cleaned not in urls:
                urls.append(cleaned)
        trace("search_done", query=q, kept_so_far=len(urls))
    return urls


def find_products(query: str, max_results: int = 8, per_store: int = 3) -> list[Product]:
    urls = search_urls(query, max_results)
    if not urls:
        return []

    # Take a few URLs from EACH store so Flipkart isn't crowded out by Amazon.
    batch = []
    for domain in STORES:
        batch += [u for u in urls if host_matches(u, domain)][:per_store]
    if not batch:
        return []
    trace("fetching", urls=batch)

    resp = with_retry(client.fetch, batch, schema=PRODUCT_SCHEMA, max_chars=6000)
    products = []

    for page in resp.results:
        if page.error:
            trace("fetch_failed", url=page.url, error=str(page.error))
            continue

        # Re-check after redirects: the final URL must still be allowlisted.
        if not is_allowed(page.url):
            trace("rejected", url=page.url, reason="final host not allowlisted")
            continue

        content = page.content or ""
        price = (page.structured or {}).get("price_inr")

        # Never trust the extractor alone: the price must match the page text.
        if not price_in_content(price, content):
            trace("rejected", url=page.url, reason="price not found in page text",
                  extracted_price=price)
            continue

        try:
            product = Product(
                title=(page.title or "")[:200],
                price_inr=price,
                rating=find_rating(content),  # None if the page states none
                url=clean_url(page.url),
            )
        except Exception as e:
            trace("rejected", url=page.url, reason=str(e))
            continue

        products.append(product)
        trace("accepted", url=product.url, price=product.price_inr, rating=product.rating)

    return products


if __name__ == "__main__":
    try:
        found = find_products("men formal shirt india")
    except KeenableConnectionError:
        print("Could not reach Keenable after 3 tries. Check your internet and rerun.")
        raise SystemExit(1)
    for p in found:
        print(p.price_inr, p.rating, p.title[:70], p.url)
    print(f"{len(found)} product(s) accepted. See traces/run.jsonl")