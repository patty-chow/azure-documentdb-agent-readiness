import os
import io
import sys
import math
import logging
from PIL import Image, ImageDraw
import numpy as np
from app.db import get_client, DB_NAME, COLLECTION_NAME, pack_embedding, ensure_vector_index
from app.encoder import encode_image_pil, encode_image_fallback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_DIR = "sample_data"
NUM_IMAGES = 20


def make_placeholder_images(n=NUM_IMAGES):
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    paths = []
    for i in range(n):
        img = Image.new("RGB", (224, 224), (int(255 * (i / n)), int(128 * (i / n)), 200))
        d = ImageDraw.Draw(img)
        d.text((10, 10), f"Product {i}", fill=(255, 255, 255))
        path = os.path.join(SAMPLE_DIR, f"product_{i}.jpg")
        img.save(path, quality=85)
        paths.append(path)
    return paths


def seed_database():
    paths = make_placeholder_images()
    try:
        client = get_client()
    except Exception as ex:
        logger.error("DOCUMENTDB_URI is not set or cluster unreachable: %s", ex)
        sys.exit(1)
    db = client[DB_NAME]
    coll = db[COLLECTION_NAME]
    # Create index (best-effort)
    ensure_vector_index(db)

    for i, p in enumerate(paths):
        try:
            from PIL import Image
            img = Image.open(p).convert("RGB")
            try:
                vec = encode_image_pil(img)
            except Exception:
                vec = encode_image_fallback(img)
        except Exception as ex:
            logger.warning("Failed to encode %s: %s", p, ex)
            continue
        emb_bin = pack_embedding(vec)
        doc = {"name": f"Product {i}", "image_path": p, "embedding": emb_bin}
        # Insert or upsert
        try:
            coll.update_one({"image_path": p}, {"$set": doc}, upsert=True)
            logger.info("Upserted %s", p)
        except Exception as ex:
            logger.error("Failed to insert document for %s: %s", p, ex)

    logger.info("Seeding complete. Inserted %d products.", len(paths))


if __name__ == "__main__":
    seed_database()
