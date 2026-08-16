"""Dioscuri kitbash v3 — drop floating mag, trim rifle barrel behind the
Malorian muzzle, fixed team colors (ash=steel blue, mal=crimson)."""
import bpy
import bmesh
import math
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
SRC = os.path.join(ROOT, "source")
ASHURA = os.path.join(SRC, r"base\weapons\firearms\rifle_sniper\tsunami_ashura\entities\meshes\w_rifle_sniper__tsunami_ashura__base1_01.glb")
MALORIAN = os.path.join(SRC, r"base\weapons\firearms\handgun\malorian_silverhand\entities\meshes\w_handgun__malorian_silverhand__base1_01.glb")

MAL_SCALE = 1.5

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

def world_y_range(o):
    dg = bpy.context.evaluated_depsgraph_get()
    eo = o.evaluated_get(dg)
    m = eo.to_mesh()
    ys = [(eo.matrix_world @ v.co).y for v in m.vertices]
    eo.to_mesh_clear()
    return (min(ys), max(ys)) if ys else (0, 0)

ashura = import_clean(ASHURA, "ash")
malorian = import_clean(MALORIAN, "mal")

# --- delete the floating magazine (ash submesh_03) --------------------
for o in list(ashura):
    if o.type == 'MESH' and 'submesh_03' in o.name:
        print("DELETING floating mag:", o.name)
        ashura.remove(o)
        bpy.data.objects.remove(o, do_unlink=True)

# --- scale malorian around the grip ----------------------------------
anchor = bpy.data.objects.new("Malorian_Anchor", None)
scene.collection.objects.link(anchor)
for o in malorian:
    if o.parent is None:
        o.parent = anchor
anchor.scale = (MAL_SCALE, MAL_SCALE, MAL_SCALE)
bpy.context.view_layer.update()

# --- report extents ---------------------------------------------------
mal_muzzle = -999.0
for o in ashura + malorian:
    if o.type == 'MESH':
        lo, hi = world_y_range(o)
        print(f"EXTENT {o.name:35s} y {lo:6.3f} .. {hi:6.3f}")
        if o.name.startswith("mal_") and hi > mal_muzzle:
            mal_muzzle = hi
print(f"MAL MUZZLE at y={mal_muzzle:.3f}")

# --- trim ashura main body just behind the malorian muzzle ------------
cutoff = mal_muzzle - 0.02
for o in ashura:
    if o.type == 'MESH' and 'submesh_00' in o.name:
        inv = o.matrix_world.inverted()
        bm = bmesh.new()
        bm.from_mesh(o.data)
        doomed = [v for v in bm.verts if (o.matrix_world @ v.co).y > cutoff]
        print(f"TRIM {o.name}: removing {len(doomed)} verts past y={cutoff:.3f}")
        bmesh.ops.delete(bm, geom=doomed, context='VERTS')
        bm.to_mesh(o.data)
        bm.free()

# --- team colors (workbench OBJECT color mode) ------------------------
for o in ashura:
    if o.type == 'MESH':
        o.color = (0.35, 0.45, 0.60, 1.0)   # steel blue
for o in malorian:
    if o.type == 'MESH':
        o.color = (0.65, 0.15, 0.15, 1.0)   # crimson

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

ys, zs = [], []
for o in ashura + malorian:
    if o.type == 'MESH':
        lo, hi = world_y_range(o)
        ys += [lo, hi]
dg = bpy.context.evaluated_depsgraph_get()
for o in ashura + malorian:
    if o.type == 'MESH':
        eo = o.evaluated_get(dg)
        m = eo.to_mesh()
        zs += [(eo.matrix_world @ v.co).z for v in m.vertices]
        eo.to_mesh_clear()

cy = (min(ys) + max(ys)) / 2
cz = (min(zs) + max(zs)) / 2
L = max(ys) - min(ys)

views = {
    "side":    ((L * 1.6, cy, cz), (math.radians(90), 0, math.radians(90))),
    "three_q": ((L * 1.2, cy - L, cz + L * 0.4), (math.radians(70), 0, math.radians(50))),
    "top":     ((0.0, cy, L * 1.6), (0, 0, 0)),
}
outdir = os.path.join(ROOT, "renders")
os.makedirs(outdir, exist_ok=True)
for name, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = rot
    scene.render.filepath = os.path.join(outdir, f"v3_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
print("KITBASH V3 DONE")
