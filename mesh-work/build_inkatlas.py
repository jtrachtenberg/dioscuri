"""Author mod\dioscuri\icons.inkatlas from the avatars0 template:
single part 'dioscuri_icon' covering the whole of our xbm texture."""
import json
import copy

SRC = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work\source"
STAGE = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\archive-staging\Dioscuri\mod\dioscuri"
TMPL = SRC + r"\base\gameplay\gui\common\icons\avatars\avatars0.inkatlas.json"

with open(TMPL, "r", encoding="utf-8") as fh:
    doc = json.load(fh)
root = doc["Data"]["RootChunk"]
print("root keys:", list(root.keys()))

slots = root["slots"]["Elements"] if isinstance(root.get("slots"), dict) else root.get("slots")
print("slot count:", len(slots))
s0 = slots[0]
print("slot0 keys:", list(s0.keys()))
parts = s0.get("parts", [])
print("part sample:", json.dumps(parts[0], default=str)[:400] if parts else "none")

TEX = "mod\\dioscuri\\icons\\dioscuri_icon.xbm"
part = copy.deepcopy(parts[0])
part["partName"] = {"$type": "CName", "$storage": "string", "$value": "dioscuri_icon"}
# centered 46.9% x 28.9% region = 600x208 effective px at HD_1280_720
cr = part["clippingRectInUVCoords"]
cr["Left"] = 0.2656
cr["Right"] = 0.7344
cr["Top"] = 0.3555
cr["Bottom"] = 0.6445
root["textureResolution"] = "HD_1280_720"

for s in slots:
    s["texture"]["DepotPath"] = {"$type": "ResourcePath", "$storage": "string", "$value": TEX}
    s["parts"] = [copy.deepcopy(part)]

# root-level single-texture fields
if isinstance(root.get("texture"), dict) and "DepotPath" in root["texture"]:
    root["texture"]["DepotPath"] = {"$type": "ResourcePath", "$storage": "string", "$value": TEX}
if isinstance(root.get("activeTexture"), dict) and "DepotPath" in root.get("activeTexture", {}):
    root["activeTexture"]["DepotPath"] = {"$type": "ResourcePath", "$storage": "string", "$value": TEX}
if isinstance(root.get("parts"), list):
    root["parts"] = [copy.deepcopy(part)]

with open(STAGE + r"\icons.inkatlas.json", "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1)
print("INKATLAS written")
