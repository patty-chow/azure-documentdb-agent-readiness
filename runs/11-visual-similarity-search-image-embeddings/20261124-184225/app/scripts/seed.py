"""Seed the sample_retail_11.products collection with example products.
Downloads images from picsum.photos, encodes with CLIP, and inserts docs with embedding binary subtype 0x09.
"""
import os
import io
import sys
import requests
import numpy as np
import bson
import torch
from PIL import Image
from dotenv import load_dotenv
from pymongo import MongoClient
from transformers import CLIPProcessor, CLIPModel

load_dotenv()
DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
if not DOCUMENTDB_URI:
    print("DOCUMENTDB_URI not set in environment")
    sys.exit(1)

model_name = "openai/clip-vit-base-patch32"
processor = CLIPProcessor.from_pretrained(model_name)
model = CLIPModel.from_pretrained(model_name)

client = MongoClient(DOCUMENTDB_URI, tls=True)
db = client["sample_retail_11"]
coll = db["products"]

# Idempotent: keep existing docs if present
if coll.count_documents({}) > 0:
    print("Collection already has documents; exiting to avoid duplicates. Drop the collection to reseed.")
    sys.exit(0)

products = []
for i in range(1,21):
    name = f"Sample Product {i}"
    image_url = f"https://picsum.photos/seed/{i}/400/400"
    products.append({"name": name, "image_url": image_url, "schemaVersion": 1})

# Download images and compute embeddings
for p in products:
    print("Processing", p["image_url"])
    resp = requests.get(p["image_url"])
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
    vec = features[0].cpu().numpy()
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    vec = vec.astype(np.float32)
    p["embedding"] = bson.Binary(vec.tobytes(), subtype=0x09)

# Insert
res = coll.insert_many(products)
print(f"Inserted {len(res.inserted_ids)} documents into sample_retail_11.products")
