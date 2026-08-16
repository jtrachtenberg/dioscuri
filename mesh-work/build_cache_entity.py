"""Build cache_case.app + cache_case.ent: lootable suitcase machinery
wearing the Malorian gun-case body with our embossed lid."""
import json
import copy

PROPS = r"C:\Users\jtrac\AppData\Local\Temp\claude\C--Users-jtrac-dev\da229038-98a4-40f5-bf52-047296d0c59e\scratchpad\props"
STAGE = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\archive-staging\Dioscuri\mod\dioscuri"

LID_MESH = "mod\\dioscuri\\meshes\\cache_case_top.mesh"
BOTTOM_MESH = "mod\\dioscuri\\meshes\\cache_case_bottom.mesh"
HANDLE_MESH = "base\\items\\quest\\q000__hym_gun_suitcase\\q000__gun_suitcase_handle.mesh"
APP_PATH = "mod\\dioscuri\\cache_case.app"

def cname(v):
    return {"$type": "CName", "$storage": "string", "$value": v}

def respath(v):
    return {"$type": "ResourcePath", "$storage": "string", "$value": v}

# ---- .app ------------------------------------------------------------
with open(PROPS + r"\base\gameplay\loot\containers\common_suitcases\appearances\suitcase_small.app.json", encoding="utf-8") as fh:
    app = json.load(fh)
aroot = app["Data"]["RootChunk"]
default = next(a for a in aroot["appearances"] if a["Data"]["name"].get("$value") == "default")
comps = default["Data"]["components"]

lid = next(c for c in comps if c.get("name", {}).get("$value") == "lid")
box = next(c for c in comps if c.get("name", {}).get("$value") == "box")

lid["mesh"]["DepotPath"] = respath(LID_MESH)
lid["meshAppearance"] = cname("default")
box["mesh"]["DepotPath"] = respath(BOTTOM_MESH)
box["meshAppearance"] = cname("default")

handle = copy.deepcopy(box)
handle["name"] = cname("handle")
handle["mesh"]["DepotPath"] = respath(HANDLE_MESH)
if "id" in handle:
    handle["id"] = "9999999"
comps.append(handle)

# drop the lid animator: its open-transform was authored for the small
# suitcase and floats our longer lid; the case stays closed instead
comps = [c for c in comps if c.get("$type") != "gameTransformAnimatorComponent"]
default["Data"]["components"] = comps

aroot["appearances"] = [default]
with open(STAGE + r"\cache_case.app.json", "w", encoding="utf-8") as fh:
    json.dump(app, fh, indent=1)
print("APP written, components:", [c.get("name", {}).get("$value") for c in comps])

LOOT_TABLE = "LootTables.DioscuriCacheLoot"

# ---- .ent ------------------------------------------------------------
with open(PROPS + r"\base\gameplay\loot\containers\common_suitcases\common_suitcase_small.ent.json", encoding="utf-8") as fh:
    ent = json.load(fh)
eroot = ent["Data"]["RootChunk"]
entry = eroot["appearances"][0]
entry["appearanceName"] = cname("default")
entry["appearanceResource"]["DepotPath"] = respath(APP_PATH)
entry["name"] = cname("default")
eroot["appearances"] = [entry]
eroot["defaultAppearance"] = cname("default")
# native content: lootTables seeds the container's inventory at spawn
eroot["entity"]["Data"]["lootTables"] = [
    {"$type": "TweakDBID", "$storage": "string", "$value": LOOT_TABLE}]
eroot["entity"]["Data"]["contentAssignment"] = {
    "$type": "TweakDBID", "$storage": "string", "$value": LOOT_TABLE}
eroot["entity"]["Data"]["lootQuality"] = "Legendary"
eroot["entity"]["Data"]["displayName"] = {"unk1": "0", "value": "LocKey#Dioscuri-Cache-Name"}
with open(STAGE + r"\cache_case.ent.json", "w", encoding="utf-8") as fh:
    json.dump(ent, fh, indent=1)
print("ENT written with contentAssignment ->", LOOT_TABLE)
print("ENTITY BUILD DONE")
