"""Run a single visual search request against the app without running a server using TestClient."""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from app.main import app
import requests

client = TestClient(app)

img_url = "https://picsum.photos/seed/5/400/400"
resp = requests.get(img_url)
files = {"file": ("q.jpg", resp.content, "image/jpeg")}
res = client.post("/visual-search", files=files)
print('status', res.status_code)
print(res.json())
