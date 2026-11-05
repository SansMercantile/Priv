"""Image / product-photo suite -- Bedrock Stable Image edit models, in-house.

Creatify's static-ad + product-photography surface, rebuilt on Amazon Bedrock
(the same account that renders our plates). One place for every image edit we
need across the ecosystem:

  - remove-background   product cut-outs on a clean plate
  - inpaint             edit a masked region with a prompt
  - outpaint            extend an image past its frame
  - erase-object        remove an unwanted object
  - style-transfer      re-light / re-style a photo to brand
  - generate            text -> image (Stable Image Ultra, like the plates)

All calls go through boto3 Bedrock Runtime (us-west-2). No third-party API.
"""
import base64
import io
import json
import os
import time

import boto3

import brand as B

REGION = "us-west-2"
OUT = os.path.join(B.ASSETS, "images")

# The Stability edit models are NOT available for on-demand invoke by bare
# model ID in these regions -- they must go through the US cross-region
# inference profile ("us." prefix). Generation (Ultra) works either way.
MODELS = {
    "remove_background": "us.stability.stable-image-remove-background-v1:0",
    "inpaint": "us.stability.stable-image-inpaint-v1:0",
    "outpaint": "us.stability.stable-outpaint-v1:0",
    "erase_object": "us.stability.stable-image-erase-object-v1:0",
    "style_transfer": "us.stability.stable-style-transfer-v1:0",
}


def _client():
    return boto3.client("bedrock-runtime", region_name=REGION)


def _img_bytes(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        return bytes(path_or_bytes)
    with open(path_or_bytes, "rb") as fh:
        return fh.read()


def _invoke(model, body):
    r = _client().invoke_model(modelId=model, contentType="application/json",
                               accept="application/json", body=json.dumps(body))
    return json.loads(r["body"].read())


def _save(data, name, sub=""):
    d = os.path.join(OUT, sub) if sub else OUT
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, name)
    raw = base64.b64decode(data["images"][0] if "images" in data else data["image"])
    with open(path, "wb") as fh:
        fh.write(raw)
    return path


def remove_background(image, name=None):
    """Cut the subject out -> transparent-background PNG."""
    body = {"image": base64.b64encode(_img_bytes(image)).decode()}
    data = _invoke(MODELS["remove_background"], body)
    return _save(data, name or f"cutout-{time.strftime('%Y%m%d-%H%M%S')}.png")


def inpaint(image, prompt, name=None, mask=None, grow=0.05):
    """Edit a region with a prompt. mask = same-size black/white mask (white =
    edit), else the model auto-masks around the subject."""
    body = {
        "image": base64.b64encode(_img_bytes(image)).decode(),
        "prompt": prompt,
        "grow_mask": grow,
        "output_format": "png",
    }
    if mask is not None:
        body["mask"] = base64.b64encode(_img_bytes(mask)).decode()
    data = _invoke(MODELS["inpaint"], body)
    return _save(data, name or f"inpaint-{time.strftime('%Y%m%d-%H%M%S')}.png")


def outpaint(image, name=None, left=0, right=0, up=0, down=0, prompt=""):
    """Extend the canvas; the prompt guides the new area."""
    body = {
        "image": base64.b64encode(_img_bytes(image)).decode(),
        "left": left, "right": right, "up": up, "down": down,
        "prompt": prompt, "output_format": "png",
    }
    data = _invoke(MODELS["outpaint"], body)
    return _save(data, name or f"outpaint-{time.strftime('%Y%m%d-%H%M%S')}.png")


def erase_object(image, mask, name=None):
    """Remove an object given a same-size mask (white = erase)."""
    body = {
        "image": base64.b64encode(_img_bytes(image)).decode(),
        "mask": base64.b64encode(_img_bytes(mask)).decode(),
        "output_format": "png",
    }
    data = _invoke(MODELS["erase_object"], body)
    return _save(data, name or f"erase-{time.strftime('%Y%m%d-%H%M%S')}.png")


def style_transfer(image, prompt, name=None, strength=0.6):
    """Re-style / re-light a photo toward the brand look."""
    body = {
        "init_image": base64.b64encode(_img_bytes(image)).decode(),
        "prompt": prompt,
        "init_image_mode": "IMAGE_STRENGTH",
        "image_strength": max(0.0, min(1.0, 1.0 - strength)),
        "output_format": "png",
    }
    data = _invoke(MODELS["style_transfer"], body)
    return _save(data, name or f"style-{time.strftime('%Y%m%d-%H%M%S')}.png")


def generate(prompt, ratio="1:1", name=None, seed=None):
    """Text -> image via Stable Image Ultra (same as the plate foundry)."""
    import backgrounds
    return backgrounds.generate_one(prompt, ratio=ratio, name=name, seed=seed)


def product_shot(image, setting, name=None):
    """One product photo -> a branded editorial shot: cut the subject out, then
    inpaint a branded setting around it (product kept intact)."""
    cut = remove_background(image)
    prompt = (f"premium product photograph on {setting}, deep navy backdrop "
              "with soft gold rim light, editorial advertising photography, "
              "clean negative space, high-end studio lighting, no text")
    return inpaint(cut, prompt, name=name)


# ------------------------------------------------------------- studio bridge
def run(spec):
    """studio.py entry: spec carries {op, ...} -> {path, rel, url, op}."""
    op = spec.get("op")
    if op == "remove_background":
        p = remove_background(spec["image"], spec.get("name"))
    elif op == "inpaint":
        p = inpaint(spec["image"], spec["prompt"], spec.get("name"),
                    spec.get("mask"))
    elif op == "outpaint":
        p = outpaint(spec["image"], spec.get("name"),
                     spec.get("left", 0), spec.get("right", 0),
                     spec.get("up", 0), spec.get("down", 0),
                     spec.get("prompt", ""))
    elif op == "erase_object":
        p = erase_object(spec["image"], spec["mask"], spec.get("name"))
    elif op == "style_transfer":
        p = style_transfer(spec["image"], spec["prompt"], spec.get("name"),
                           spec.get("strength", 0.6))
    elif op == "generate":
        p, _prov = generate(spec["prompt"], spec.get("ratio", "1:1"),
                            spec.get("name"), spec.get("seed"))
    elif op == "product_shot":
        p = product_shot(spec["image"], spec["setting"], spec.get("name"))
    else:
        raise SystemExit(f"unknown op: {op}")
    rel = os.path.relpath(p, B.ASSETS).replace("\\", "/")
    return {"op": op, "rel": rel, "url": "/marketing-assets/" + rel,
            "exists": os.path.exists(p)}
