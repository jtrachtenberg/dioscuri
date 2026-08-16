"""Dioscuri kitbash v4 — full Ashura rifle frame; Malorian contributes only
its grip/trigger/rear-slide section (trimmed), grafted at the rifle grip."""
import bpy
import bmesh
import math
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
SRC = os.path.join(ROOT, "source")
ASHURA = os.path.join(SRC, r"base\weapons\firearms\rifle_sniper\tsunami_ashura\entities\meshes\w_rifle_sniper__tsunami_ashura__base1_01.glb")
MALORIAN = os.path.join(SRC, r"base\weapons\firearms\handgun\malorian_silverhand\entities\meshes\w_handgun__malorian_silverhand__base1_01.glb")

MAL_SCALE = 1.2
MAL_KEEP_Y = 0.16   # keep malorian geometry behind this (local, pre-scale): grip/trigger/rear slide

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def import_clean(path, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    keep = []
    for o in new:
        if o.type == 'MESH' and 'Icosphere' in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
        else:
            o.name = f"{tag}_{o.name}"
            keep.append(o)
    return keep

ashura = import_clean(ASHURA, "ash")
malorian = import_clean(MALORIAN, "mal")

# floating mag off the rifle
for o in list(ashura):
    if o.type == 'MESH' and 'submesh_03' in o.name:
        ashura.remove(o)
        bpy.data.objects.remove(o, do_unlink=True)

# --- malorian: keep only the rear section ----------------------------
for o in list(malorian):
    if o.type != 'MESH':
        continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    doomed = [v for v in bm.verts if v.co.y > MAL_KEEP_Y]
    if len(doomed) == len(bm.verts):
        # entirely forward of the cut: drop the whole part
        bm.free()
        malorian.remove(o)
        bpy.data.objects.remove(o, do_unlink=True)
        continue
    if doomed:
        bmesh.ops.delete(bm, geom=doomed, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()

anchor = bpy.data.objects.new("Malorian_Anchor", None)
scene.collection.objects.link(anchor)
for o in malorian:
    if o.parent is None:
        o.parent = anchor
anchor.scale = (MAL_SCALE, MAL_SCALE, MAL_SCALE)
anchor.location = (0.0, 0.0, 0.0)

# --- colors -----------------------------------------------------------
for o in ashura:
    if o.type == 'MESH':
        o.color = (0.35, 0.45, 0.60, 1.0)
for o in malorian:
    if o.type == 'MESH':
        o.color = (0.65, 0.15, 0.15, 1.0)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "dioscuri_kitbash.blend"))

# --- render -----------------------------------------------------------
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'OBJECT'
scene.render.resolution_x = 1600
scene.render.resolution_y = 900

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 50
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

def all_bounds():
    dg = bpy.context.evaluated_depsgraph_get()
    ys, zs = [], []
    for o in ashura + malorian:
        if o.type != 'MESH':
            continue
        eo = o.evaluated_get(dg)
        m = eo.to_mesh()
        for v in m.vertices:
            w = eo.matrix_world @ v.co
            ys.append(w.y); zs.append(w.z)
        eo.to_mesh_clear()
    return ys, zs

ys, zs = all_bounds()
cy = (min(ys) + max(ys)) / 2
cz = (min(zs) + max(zs)) / 2
L = max(ys) - min(ys)
print(f"COMPOSITE length {L:.3f} m")

views = {
    "side":    ((L * 1.4, cy, cz), (math.radians(90), 0, math.radians(90))),
    "three_q": ((L * 1.05, cy - L * 0.9, cz + L * 0.35), (math.radians(70), 0, math.radians(50))),
    "top":     ((0.0, cy, L * 1.4), (0, 0, 0)),
}
outdir = os.path.join(ROOT, "renders")
os.makedirs(outdir, exist_ok=True)
for name, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = rot
    scene.render.filepath = os.path.join(outdir, f"v4_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
print("KITBASH V4 DONE")
