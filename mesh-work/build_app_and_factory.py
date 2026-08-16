"""Build dioscuri_body.app.json (single default appearance -> our mesh as a
static entMeshComponent) and a one-row parts factory csv json."""
import json
import copy

SRC = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work\source"
STAGE = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\archive-staging\Dioscuri\mod\dioscuri"
APP_TMPL = SRC + r"\base\weapons\firearms\special\kangtao_dian\appearances\w_smg__kang_tao_dian__rcv1.app.json"
CSV_TMPL = SRC + r"\base\gameplay\factories\items\weapons\parts_appearances.csv.json"

MESH_PATH = "mod\\dioscuri\\meshes\\dioscuri_body.mesh"
APP_PATH = "mod\\dioscuri\\dioscuri_body.app"

# ---- .app -----------------------------------------------------------
with open(APP_TMPL, "r", encoding="utf-8") as f:
    doc = json.load(f)
root = doc["Data"]["RootChunk"]

default = next(a for a in root["appearances"]
               if a["Data"]["name"].get("$value") == "default")
comps = default["Data"]["components"]

KEEP_TYPES = {"entAnimatedComponent", "entAnimationControllerComponent",
              "gameStatsComponent", "gameScanningComponent", "WorkspotMapperComponent"}
kept = [c for c in comps if c.get("$type") in KEEP_TYPES]

shadow = next(c for c in comps if c.get("$type") == "entMeshComponent")
body = copy.deepcopy(shadow)
body["name"] = {"$type": "CName", "$storage": "string", "$value": "dioscuri_body_mesh"}
body["mesh"]["DepotPath"] = {"$type": "ResourcePath", "$storage": "string", "$value": MESH_PATH}
body["meshAppearance"] = {"$type": "CName", "$storage": "string", "$value": "default"}
# leave castShadows ("Always") and chunkMask as the template has them

kept.append(body)
default["Data"]["components"] = kept
root["appearances"] = [default]

with open(STAGE + r"\dioscuri_body.app.json", "w", encoding="utf-8") as f:
    json.dump(doc, f, indent=1)
print("APP written: components kept =", [c.get("$type") for c in kept])

# ---- factory csv ----------------------------------------------------
with open(CSV_TMPL, "r", encoding="utf-8") as f:
    cdoc = json.load(f)
croot = cdoc["Data"]["RootChunk"]
print("csv keys:", [k for k in croot.keys()])
rows = croot.get("compiledData") or croot.get("data")
if rows is not None:
    print("row sample:", json.dumps(rows[0] if isinstance(rows, list) and rows else rows, default=str)[:300])
# C2dArray: headers + data
if "headers" in croot:
    print("headers:", croot["headers"])
data = croot.get("data")
if isinstance(data, list) and data:
    sample = data[0]
    print("data[0]:", json.dumps(sample)[:300])
    croot["data"] = [["dioscuri_body", APP_PATH, "false"]] if isinstance(sample, list) else data[:1]
    if not isinstance(sample, list):
        print("UNEXPECTED row shape; left first row for manual fix")
with open(STAGE + r"\factory_parts.csv.json", "w", encoding="utf-8") as f:
    json.dump(cdoc, f, indent=1)
print("FACTORY draft written")
print("BUILD DONE")
