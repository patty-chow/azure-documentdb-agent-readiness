import os
import numpy as np
from typing import List

# Try to import heavy ML packages lazily; fallbacks used in seed if unavailable.
_model = None
_processor = None


def load_model():
    global _model, _processor
    if _model is not None:
        return
    try:
        from transformers import CLIPProcessor, CLIPModel
        import torch
    except Exception as ex:
        raise RuntimeError("Transformer/torch packages required for CLIP encoding: %s" % ex)
    _model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    _model.eval()


def encode_image_pil(pil_image) -> List[float]:
    """Return a 512-d float list encoding for the given PIL Image.
    Raises RuntimeError if model packages are unavailable.
    """
    if _model is None or _processor is None:
        load_model()
    import torch
    inputs = _processor(images=pil_image, return_tensors="pt")
    with torch.no_grad():
        outputs = _model.get_image_features(**inputs)
    vec = outputs[0].cpu().numpy()
    # Normalize to unit length (common for CLIP embeddings)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.astype("float32").tolist()


def encode_image_fallback(pil_image) -> List[float]:
    """Fallback encoder that produces a deterministic pseudo-embedding from the image bytes.
    Produces 512 float32 values in a stable numeric range, then L2-normalizes.
    """
    import hashlib
    arr = pil_image.tobytes()
    h = hashlib.sha512(arr).digest()
    out = []
    i = 0
    while len(out) < 512:
        # Derive a 4-byte chunk and interpret as unsigned int, map to float
        chunk = h[i % len(h):(i % len(h)) + 4]
        if len(chunk) < 4:
            # extend by hashing again
            h = hashlib.sha512(h).digest()
            continue
        val = int.from_bytes(chunk, "little")
        f = (val / 0xFFFFFFFF) * 2.0 - 1.0  # map to [-1,1]
        out.append(f)
        i += 1
    a = np.array(out, dtype="float32")
    n = np.linalg.norm(a)
    if n > 0:
        a = a / n
    return a.tolist()
