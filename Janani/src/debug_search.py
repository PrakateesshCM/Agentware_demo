from dotenv import load_dotenv
load_dotenv()
from keenable import Keenable
from urllib.parse import urlparse

c = Keenable()
for q in ["men formal shirt amazon.in", "men formal shirt flipkart.com"]:
    print("\n==", q)
    for r in c.search(q, max_results=8):
        u = urlparse(r.url)
        print(u.hostname, u.path[:60])