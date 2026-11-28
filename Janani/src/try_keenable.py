from dotenv import load_dotenv
load_dotenv()

from keenable import Keenable

client = Keenable()
for r in client.search("men's formal shirt india", max_results=3):
    print(r.title, r.url)