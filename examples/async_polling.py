"""Fire-and-poll: submit without blocking, do other work, then collect the result."""
import time
from rife_api import Client

client = Client()  # reads SYNEXA_API_KEY
prediction = client.run({"image_url": "https://example.com/input.png"}, wait=False)
print("submitted", prediction["id"], prediction["status"])
while prediction["status"] not in ("succeeded", "failed"):
    time.sleep(2)
    prediction = client.get(prediction["id"])
print(prediction["status"], prediction.get("output"))
