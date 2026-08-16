"""Dioscuri kitbash v1 — stage Ashura frame + Malorian 3516 parts and render previews.

Run headless:  blender --background --python kitbash_v1.py
Outputs: dioscuri_kitbash.blend + renders/*.png in mesh-work/
"""
import bpy
import math
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
SRC = os.path.join(ROOT, "source")
ASHURA = os.path.join(SRC, r"base\weapons\firearms\rifle_sniper\tsunami_ashura\entities\meshes\w_rifle_sniper__tsunami_ashura__base1_01.glb")
MALORIAN = os.path.join(SRC, r"base\weapons\firearms\handgun\malorian_silverhand\entities\meshes\w_handgun__malorian_silverhand__base1_01.glb")

# --- clean scene ------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def import_glb(path, collection_name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new_objs = [o for o in bpy.data.objects if o not in before]
    coll = bpy.data.collections.new(collection_name)
    scene.collection.children.link(coll)
    for o in new_objs:
        for c in o.users_collection:
            c.objects.unlink(o)
        coll.objects.link(o)
    return coll, new_objs

def bounds(objs):
    xs, ys, zs = [], [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type != 'MESH':
            continue
        eo = o.evaluated_get(dg)
        for v in eo.to_mesh().vertices:
            w = eo.matrix_world @ v.co
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
        eo.to_mesh_clear()
    if not xs:
        return None
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

ashura_coll, ashura_objs = import_glb(ASHURA, "Ashura_Frame")
malorian_coll, malorian_objs = import_glb(MALORIAN, "Malorian_3516")

ab = bounds(ashura_objs)
mb = bounds(malorian_objs)
print("ASHURA bounds  x=%.3f..%.3f y=%.3f..%.3f z=%.3f..%.3f" % (ab[0][0], ab[0][1], ab[1][0], ab[1][1], ab[2][0], ab[2][1]))
print("MALORIAN bounds x=%.3f..%.3f y=%.3f..%.3f z=%.3f..%.3f" % (mb[0][0], mb[0][1], mb[1][0], mb[1][1], mb[2][0], mb[2][1]))

# --- naive first placement -------------------------------------------
# Weapons export along Y (muzzle direction) in CP77 convention; grip near origin.
# First pass: leave the Ashura where it is, scale the Malorian up ~1.45x and
# sink it into the grip/receiver zone of the rifle for silhouette comparison.
mal_parent = bpy.data.objects.new("Malorian_Anchor", None)
scene.collection.objects.link(mal_parent)
for o in malorian_objs:
    if o.parent is None:
        o.parent = mal_parent
mal_parent.scale = (1.45, 1.45, 1.45)
mal_parent.location = (0.0, -0.05, -0.01)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "dioscuri_kitbash.blend"))

# --- render previews --------------------------------------------------
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'RANDOM'   # color per object: parts distinguishable
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.film_transparent = False

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

cy = (ab[1][0] + ab[1][1]) / 2.0
cz = (ab[2][0] + ab[2][1]) / 2.0
length = ab[1][1] - ab[1][0]

views = {
    "side":     ((length * 1.5, cy, cz),               (math.radians(90), 0, math.radians(90))),
    "three_q":  ((length * 1.1, cy - length * 0.9, cz + length * 0.35), (math.radians(72), 0, math.radians(52))),
    "top":      ((0.0, cy, length * 1.5),              (0, 0, 0)),
}
outdir = os.path.join(ROOT, "renders")
os.makedirs(outdir, exist_ok=True)
for name, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = rot
    scene.render.filepath = os.path.join(outdir, f"v1_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)

print("KITBASH V1 DONE")
