"""The same client drives every hosted model listed in rife_api.MODELS."""
from rife_api import Client, MODELS

client = Client()
for slug, info in MODELS.items():
    print(slug, "->", info["category"], "required:", info["required"])
# pick one explicitly
output = client.run({"video_urls": ["https://example.com/input.png"]}, model="synexa/merge-videos")
print(output)
