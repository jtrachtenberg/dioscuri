"""Edit dioscuri_body.mesh.json: single 'default' appearance with our 3 chunks."""
import json

P = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work\mesh-import\dioscuri_body.mesh.json"
with open(P, "r", encoding="utf-8") as f:
    doc = json.load(f)

root = doc["Data"]["RootChunk"]
apps = root["appearances"]
print("appearances:", [a["Data"]["name"].get("$value", "?") for a in apps])
print("chunkMaterials[0]:", [c.get("$value", "") for c in apps[0]["Data"]["chunkMaterials"]])
print("materialEntries:", [e["name"].get("$value", "?") for e in root["materialEntries"]])

CHUNKS = ["pasted__malorian_ml_base", "malorian_ml_handle2", "pasted__malorian_ml_base"]

first = apps[0]
first["Data"]["name"] = {"$type": "CName", "$storage": "string", "$value": "default"}
first["Data"]["chunkMaterials"] = [
    {"$type": "CName", "$storage": "string", "$value": n} for n in CHUNKS
]
root["appearances"] = [first]

with open(P, "w", encoding="utf-8") as f:
    json.dump(doc, f, indent=2)
print("MATERIALS EDITED: default ->", CHUNKS)
