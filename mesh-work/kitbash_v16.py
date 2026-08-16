"""Dioscuri kitbash v14:
- logo cluster eased back from the muzzle dip (-9mm)
- NIGHT CITY onto the upper receiver flat (rearward + up, per red arrow)
- red grip via crease-bounded flood fill (follows geometry edges)"""
import bpy
import bmesh
import math
import os
from collections import deque

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
SRC = os.path.join(ROOT, "source")
ASHURA = os.path.join(SRC, r"base\weapons\firearms\rifle_sniper\tsunami_ashura\entities\meshes\w_rifle_sniper__tsunami_ashura__base1_01.glb")
MALORIAN = os.path.join(SRC, r"base\weapons\firearms\handgun\malorian_silverhand\entities\meshes\w_handgun__malorian_silverhand__base1_01.glb")

MAL_SCALE = 1.2
MAL_KEEP_Y = 0.16
SHARP = math.radians(38)     # crease angle that stops the red flood fill
SEED = (0.0, -0.03, -0.12)   # local-space point deep in the grip

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def make_mat(name, base, metallic, rough, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = 'BLEND'
    return m

MAT_GUNMETAL = make_mat("gunmetal", (0.28, 0.29, 0.31), 1.0, 0.38)
MAT_RED_GRIP = make_mat("red_grip", (0.45, 0.02, 0.03), 0.0, 0.15, alpha=0.92)
MAT_TEXT     = make_mat("text_ink", (0.02, 0.02, 0.02), 0.2, 0.5)

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

def trim(o, predicate):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    doomed = [v for v in bm.verts if predicate(v.co)]
    n = len(doomed)
    if n == len(bm.verts):
        bm.free()
        return -1
    if doomed:
        bmesh.ops.delete(bm, geom=doomed, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    return n

ashura = import_clean(ASHURA, "ash")
malorian = import_clean(MALORIAN, "mal")

for o in list(ashura):
    if o.type == 'MESH' and any(k in o.name for k in ("submesh_01", "submesh_02", "submesh_03", "submesh_04")):
        ashura.remove(o); bpy.data.objects.remove(o, do_unlink=True)

for o in list(malorian):
    if o.type != 'MESH':
        continue
    r = trim(o, lambda co: co.y > MAL_KEEP_Y)
    if r < 0:
        malorian.remove(o); bpy.data.objects.remove(o, do_unlink=True)

anchor = bpy.data.objects.new("Malorian_Anchor", None)
scene.collection.objects.link(anchor)
for o in malorian:
    if o.parent is None:
        o.parent = anchor
anchor.scale = (MAL_SCALE, MAL_SCALE, MAL_SCALE)

for o in ashura:
    if o.type == 'MESH':
        o.data.materials.clear()
        o.data.materials.append(MAT_GUNMETAL)

# --- red grip: the grip skin is its own submesh (submesh_06 per the
# original GLB inspection: 1718 verts, 0.038 x 0.089 x 0.132) -----------
grip_obj = next(o for o in malorian if o.type == "MESH" and "submesh_06" in o.name)
print("GRIP SUBMESH:", grip_obj.name)
for o in malorian:
    if o.type == "MESH":
        o.data.materials.clear()
        o.data.materials.append(MAT_RED_GRIP if o is grip_obj else MAT_GUNMETAL)

# --- lettering --------------------------------------------------------
p_tube = (0.0210, 0.0665)
tx, tz = p_tube

def add_text(body, size, x, y, z, name, spacing=1.0):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = body
    curve.size = size
    curve.extrude = 0.0008
    curve.space_character = spacing
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    obj.rotation_euler = (math.pi / 2, 0, math.pi / 2)
    obj.location = (x, y, z)
    obj.data.materials.append(MAT_TEXT)
    return obj

# upper receiver flat, rear of the barrel start (per red arrow)
add_text("MALORIAN ARMS  NIGHT CITY", 0.0075, 0.0220, 0.165, 0.062, "txt_nightcity")
# wordmark + dots eased back from the muzzle dip
add_text("MALORIAN", 0.012, tx + 0.0004, 0.663, tz - 0.0055, "txt_malorian", spacing=1.15)

DOT_Y0 = 0.737
DOT_STEP = 0.0060
for r in range(2):
    for c in range(4):
        if r == 1 and c == 3:
            continue
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0021, depth=0.0016,
            location=(tx + 0.0006, DOT_Y0 + c * DOT_STEP, (tz + 0.0032) - r * 0.0064),
            rotation=(0, math.pi / 2, 0))
        d = bpy.context.active_object
        d.name = f"dot_{r}_{c}"
        d.data.materials.append(MAT_TEXT)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "dioscuri_kitbash.blend"))

# --- render -----------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.cycles.device = 'CPU'
scene.render.resolution_x = 1400
scene.render.resolution_y = 800

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.35, 0.37, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.2

sun_data = bpy.data.lights.new("sun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(120))

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 50
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

views = {
    "side":     ((0.9 * 1.35, 0.36, 0.02), (math.radians(90), 0, math.radians(90))),
    "detail":   ((0.9 * 0.45, 0.66, 0.055), (math.radians(90), 0, math.radians(90))),
    "receiver": ((0.9 * 0.45, 0.20, 0.045), (math.radians(90), 0, math.radians(90))),
    "grip":     ((-0.42, -0.02, -0.11), (math.radians(90), 0, math.radians(-90))),
    "ref_view": ((-0.9 * 1.35, 0.36, 0.02), (math.radians(90), 0, math.radians(-90))),
}
outdir = os.path.join(ROOT, "renders")
os.makedirs(outdir, exist_ok=True)
for name, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = rot
    scene.render.filepath = os.path.join(outdir, f"v14_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
print("KITBASH V16 DONE")

