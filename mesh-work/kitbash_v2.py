"""Dioscuri kitbash v2 — drop icosphere junk, stage parts at real scale, render."""
import bpy
import math
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
SRC = os.path.join(ROOT, "source")
ASHURA = os.path.join(SRC, r"base\weapons\firearms\rifle_sniper\tsunami_ashura\entities\meshes\w_rifle_sniper__tsunami_ashura__base1_01.glb")
MALORIAN = os.path.join(SRC, r"base\weapons\firearms\handgun\malorian_silverhand\entities\meshes\w_handgun__malorian_silverhand__base1_01.glb")

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

def mesh_bounds(objs):
    xs, ys, zs = [], [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type != 'MESH':
            continue
        eo = o.evaluated_get(dg)
        m = eo.to_mesh()
        for v in m.vertices:
            w = eo.matrix_world @ v.co
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
        eo.to_mesh_clear()
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

ashura = import_clean(ASHURA, "ash")
malorian = import_clean(MALORIAN, "mal")

ab = mesh_bounds(ashura)
print("ASHURA  x=%.3f..%.3f  y=%.3f..%.3f  z=%.3f..%.3f" % (*ab[0], *ab[1], *ab[2]))
mb = mesh_bounds(malorian)
print("MALORIAN x=%.3f..%.3f  y=%.3f..%.3f  z=%.3f..%.3f" % (*mb[0], *mb[1], *mb[2]))

# --- stage: malorian scaled into the rifle's grip/receiver zone -------
anchor = bpy.data.objects.new("Malorian_Anchor", None)
scene.collection.objects.link(anchor)
for o in malorian:
    if o.parent is None:
        o.parent = anchor
anchor.scale = (1.5, 1.5, 1.5)
anchor.location = (0.0, 0.0, 0.0)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "dioscuri_kitbash.blend"))

# --- render -----------------------------------------------------------
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'RANDOM'
scene.render.resolution_x = 1600
scene.render.resolution_y = 900

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 50
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

allb = mesh_bounds(ashura + malorian)
cy = (allb[1][0] + allb[1][1]) / 2
cz = (allb[2][0] + allb[2][1]) / 2
L = allb[1][1] - allb[1][0]

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
    scene.render.filepath = os.path.join(outdir, f"v2_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
print("KITBASH V2 DONE")
