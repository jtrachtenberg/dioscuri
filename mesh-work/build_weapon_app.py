"""Build dioscuri_weapon.app: clone of the Dian WEAPON-level app, default
appearance only, all Dian meshes removed, our body mesh added. Also rebuild
the factory csv with both rows."""
import json
import copy

SRC = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work\source"
STAGE = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\archive-staging\Dioscuri\mod\dioscuri"
APP_TMPL = SRC + r"\base\weapons\firearms\special\kangtao_dian\w_special__kangtao_dian.app.json"
CSV_TMPL = SRC + r"\base\gameplay\factories\items\weapons\parts_appearances.csv.json"

MESH_PATH = "mod\\dioscuri\\meshes\\dioscuri_body.mesh"

with open(APP_TMPL, "r", encoding="utf-8") as fh:
    doc = json.load(fh)
root = doc["Data"]["RootChunk"]

default = next(a for a in root["appearances"]
               if a["Data"]["name"].get("$value") == "default")
comps = default["Data"]["components"]

DROP_TYPES = {"entSkinnedMeshComponent", "entMeshComponent"}
kept = [c for c in comps if c.get("$type") not in DROP_TYPES]
print("kept component types:", sorted({c.get("$type") for c in kept}))

shadow = next(c for c in comps if c.get("$type") == "entMeshComponent")
body = copy.deepcopy(shadow)
body["name"] = {"$type": "CName", "$storage": "string", "$value": "dioscuri_body_mesh"}
body["mesh"]["DepotPath"] = {"$type": "ResourcePath", "$storage": "string", "$value": MESH_PATH}
body["meshAppearance"] = {"$type": "CName", "$storage": "string", "$value": "default"}
kept.append(body)

default["Data"]["components"] = kept
root["appearances"] = [default]

with open(STAGE + r"\dioscuri_weapon.app.json", "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1)
print("WEAPON APP written with", len(kept), "components")

# factory: both the part row (kept for compat) and the weapon row
with open(CSV_TMPL, "r", encoding="utf-8") as fh:
    cdoc = json.load(fh)
croot = cdoc["Data"]["RootChunk"]
rows = [
    ["dioscuri_body", "mod\\dioscuri\\dioscuri_body.app", "false"],
    ["Dioscuri_Weapon", "mod\\dioscuri\\dioscuri_weapon.app", "false"],
]
croot["data"] = rows
if isinstance(croot.get("compiledData"), list):
    croot["compiledData"] = rows
with open(STAGE + r"\factory_parts.csv.json", "w", encoding="utf-8") as fh:
    json.dump(cdoc, fh, indent=1)
print("FACTORY rebuilt with 2 rows")
print("BUILD DONE")
