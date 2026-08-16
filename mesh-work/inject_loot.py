"""Inject loot instanceData into the OFFICIAL entSpawner-generated sector.
Minimal change: everything else in the file stays byte-identical."""
import json
import copy

SEC = r"C:\Users\jtrac\dev\Dioscuri\Dioscuri\source\archive\malorian\sectors\malorian.streamingsector.json"
REF = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work\templates\reference_container_sector.json"

with open(SEC, encoding="utf-8") as fh:
    doc = json.load(fh)
with open(REF, encoding="utf-8") as fh:
    ref = json.load(fh)

ref_node = next(n["Data"] for n in ref["Data"]["RootChunk"]["nodes"]
                if isinstance(n["Data"].get("instanceData"), dict)
                and n["Data"]["instanceData"].get("Data"))

idata = copy.deepcopy(ref_node["instanceData"])
idata["HandleId"] = "500"
idata["Data"]["buffer"]["BufferId"] = "9"
chunk = idata["Data"]["buffer"]["Data"]["Chunks"][0]
chunk["$type"] = "LootContainerObjectAnimatedByTransform"
for k in ("itemTDBID", "shardMesh"):
    chunk.pop(k, None)
chunk["lootTables"] = [
    {"$type": "TweakDBID", "$storage": "string", "$value": "LootTables.DioscuriCacheLoot"}
]
chunk["lootQuality"] = "Legendary"
chunk["containerType"] = "ClothingContainer"

nodes = doc["Data"]["RootChunk"]["nodes"]
target = next(n["Data"] for n in nodes if n["Data"].get("$type") == "worldEntityNode")
target["instanceData"] = idata
print("injected into node:", target.get("debugName", {}).get("$value", "?"))

with open(SEC, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1)
print("INJECT DONE")
