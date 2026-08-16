"""Author dioscuri.streamingsector + dioscuri.streamingblock: the cache case
as a real world object at the Malorian factory site."""
import json
import copy

BASE = r"C:\Users\jtrac\AppData\Local\Temp\claude\C--Users-jtrac-dev\da229038-98a4-40f5-bf52-047296d0c59e\scratchpad\sector\mod\arman3_lizzies_bds\worlds"
STAGE = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\archive-staging\Dioscuri\mod\dioscuri"

# position/rotation from the user's in-game entSpawner placement
# (export\malorian_exported.json)
X, Y, Z = -835.75836181641, 328.62817382813, 7.8835067749023
ROT = {"i": 0, "j": 0, "k": 0.75298953056335, "r": 0.6580325961113}
BOX_MIN = (-985.75836181641, 178.62817382813, -142.1164932251)
BOX_MAX = (-685.75836181641, 478.62817382813, 157.8835067749)
CASE_ENT = "mod\\dioscuri\\cache_case.ent"
SECTOR_PATH = "mod\\dioscuri\\dioscuri.streamingsector"

def cname(v):
    return {"$type": "CName", "$storage": "string", "$value": v}

# ---- sector ---------------------------------------------------------
with open(BASE + r"\lizzies_bds_al_ads.streamingsector.json", encoding="utf-8") as fh:
    doc = json.load(fh)
root = doc["Data"]["RootChunk"]

node = copy.deepcopy(next(n for n in root["nodes"] if n["Data"]["$type"] == "worldEntityNode"))
nd = node["Data"]
nd["debugName"] = cname("dioscuri_cache_case")
nd["appearanceName"] = cname("default")
nd["entityTemplate"]["DepotPath"] = {"$type": "ResourcePath", "$storage": "string", "$value": CASE_ENT}
# instanceData: adapted from a WORKING modded ShardCaseContainer node
# (mesh-work\templates\reference_container_sector.json). Verified to
# deserialize; carries lootTables + quality + container type.
TMPL_DIR = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work\templates"
with open(TMPL_DIR + r"\reference_container_sector.json", encoding="utf-8") as fh:
    ref = json.load(fh)
ref_node = next(n["Data"] for n in ref["Data"]["RootChunk"]["nodes"]
                if isinstance(n["Data"].get("instanceData"), dict)
                and n["Data"]["instanceData"].get("Data"))
idata = copy.deepcopy(ref_node["instanceData"])
chunk = idata["Data"]["buffer"]["Data"]["Chunks"][0]
chunk["$type"] = "LootContainerObjectAnimatedByTransform"
for k in ("itemTDBID", "shardMesh"):
    chunk.pop(k, None)
chunk["lootTables"] = [
    {"$type": "TweakDBID", "$storage": "string", "$value": "LootTables.DioscuriCacheLoot"}
]
chunk["lootQuality"] = "Legendary"
chunk["containerType"] = "ClothingContainer"
chunk["displayName"] = {"unk1": "0", "value": "LocKey#Dioscuri-Cache-Name"}
nd["instanceData"] = idata

# CONTROL: an untouched vanilla lootable suitcase beside the case, same
# loot config — isolates custom-entity problems from sector problems
control = copy.deepcopy(node)
cd = control["Data"]
cd["debugName"] = cname("dioscuri_control_vanilla_case")
cd["entityTemplate"]["DepotPath"] = {"$type": "ResourcePath", "$storage": "string",
    "$value": "base\\gameplay\\loot\\containers\\common_suitcases\\common_suitcase_small.ent"}
# appearance referenced by its full NAME, exactly as entSpawner exports it
cd["appearanceName"] = cname("suitcase_small_neomilitary_a")
cidata = copy.deepcopy(ref_node["instanceData"])
cidata["HandleId"] = "980"                      # unique vs first node
cidata["Data"]["buffer"]["BufferId"] = "2"      # unique buffer id too
cchunk = cidata["Data"]["buffer"]["Data"]["Chunks"][0]
cchunk["$type"] = "LootContainerObjectAnimatedByTransform"
for k in ("itemTDBID", "shardMesh"):
    cchunk.pop(k, None)
cchunk["lootTables"] = [
    {"$type": "TweakDBID", "$storage": "string", "$value": "LootTables.DioscuriCacheLoot"}
]
cchunk["lootQuality"] = "Legendary"
cchunk["containerType"] = "ClothingContainer"
cd["instanceData"] = cidata

root["nodes"] = [node, control]

def make_entry(idx, x, y, z):
    e = copy.deepcopy(root["nodeData"]["Data"][0])
    e["Id"] = str(idx)
    e["NodeIndex"] = idx
    e["Position"] = {"$type": "Vector4", "W": 0, "X": x, "Y": y, "Z": z}
    e["Pivot"] = {"$type": "Vector3", "X": x, "Y": y, "Z": z}
    e["Orientation"] = {"$type": "Quaternion",
                        "i": ROT["i"], "j": ROT["j"], "k": ROT["k"], "r": ROT["r"]}
    e["Scale"] = {"$type": "Vector3", "X": 1, "Y": 1, "Z": 1}
    e["QuestPrefabRefHash"] = {"$type": "NodeRef", "$storage": "uint64", "$value": "0"}
    if "Bounds" in e:
        e["Bounds"] = {"$type": "Box",
            "Max": {"$type": "Vector4", "W": 1, "X": x + 2, "Y": y + 2, "Z": z + 2},
            "Min": {"$type": "Vector4", "W": 1, "X": x - 2, "Y": y - 2, "Z": z - 2}}
    return e

root["nodeData"]["Data"] = [make_entry(0, X, Y, Z),
                            make_entry(1, X + 1.5, Y, Z)]
root["category"] = "Exterior"
root["level"] = 1

for k in ("nodeRefs", "persistentNodes", "variantNodes", "variantIndices"):
    if isinstance(root.get(k), list):
        root[k] = []
print("sector fields trimmed; persistentNodeIndex:", root.get("persistentNodeIndex"))

with open(STAGE + r"\dioscuri.streamingsector.json", "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1)
print("SECTOR written")

# ---- block ----------------------------------------------------------
with open(BASE + r"\lizzies_bds.streamingblock.json", encoding="utf-8") as fh:
    bdoc = json.load(fh)
broot = bdoc["Data"]["RootChunk"]
desc = copy.deepcopy(next(d for d in broot["descriptors"] if d.get("category") == "AlwaysLoaded"))
desc["data"]["DepotPath"] = {"$type": "ResourcePath", "$storage": "string", "$value": SECTOR_PATH}
desc["questPrefabNodeRef"] = {"$type": "NodeRef", "$storage": "string", "$value": "$/03_night_city/#DioscuriCache"}
desc["category"] = "Exterior"
desc["level"] = 1
desc["streamingBox"] = {"$type": "Box",
    "Max": {"$type": "Vector4", "W": 1, "X": BOX_MAX[0], "Y": BOX_MAX[1], "Z": BOX_MAX[2]},
    "Min": {"$type": "Vector4", "W": 1, "X": BOX_MIN[0], "Y": BOX_MIN[1], "Z": BOX_MIN[2]}}
broot["descriptors"] = [desc]
with open(STAGE + r"\dioscuri.streamingblock.json", "w", encoding="utf-8") as fh:
    json.dump(bdoc, fh, indent=1)
print("BLOCK written")
print("SECTOR BUILD DONE")
