"""Dioscuri kitbash v6 â€” text anchored to measured surfaces, junk quads
removed, red grip boundary widened."""
import bpy
import bmesh
import math
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
SRC = os.path.join(ROOT, "source")
ASHURA = os.path.join(SRC, r"base\weapons\firearms\rifle_sniper\tsunami_ashura\entities\meshes\w_rifle_sniper__tsunami_ashura__base1_01.glb")
MALORIAN = os.path.join(SRC, r"base\weapons\firearms\handgun\malorian_silverhand\entities\meshes\w_handgun__malorian_silverhand__base1_01.glb")

MAL_SCALE = 1.2
MAL_KEEP_Y = 0.16

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

# drop rifle mag + vestigial glow-card quads (tiny submeshes)
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

# --- materials --------------------------------------------------------
for o in ashura:
    if o.type == 'MESH':
        o.data.materials.clear()
        o.data.materials.append(MAT_GUNMETAL)

for o in malorian:
    if o.type != 'MESH':
        continue
    o.data.materials.clear()
    o.data.materials.append(MAT_GUNMETAL)
    o.data.materials.append(MAT_RED_GRIP)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for f in bm.faces:
        c = f.calc_center_median()
        f.material_index = 1 if (c.z < -0.008 and c.y < 0.050) else 0
    bm.to_mesh(o.data)
    bm.free()

# --- probe the rifle body's +X flank at given y/z windows -------------
ash_body = next(o for o in ashura if o.type == 'MESH' and 'submesh_00' in o.name)
dg = bpy.context.evaluated_depsgraph_get()
eo = ash_body.evaluated_get(dg)
mesh = eo.to_mesh()
world_verts = [eo.matrix_world @ v.co for v in mesh.vertices]
eo.to_mesh_clear()

def probe(y_lo, y_hi, z_lo, z_hi):
    """max x and z-extent of geometry inside the window."""
    sel = [w for w in world_verts if y_lo <= w.y <= y_hi and z_lo <= w.z <= z_hi]
    if not sel:
        return None
    mx = max(w.x for w in sel)
    zc = (min(w.z for w in sel) + max(w.z for w in sel)) / 2
    return mx, zc

# receiver flank band (barrel start) and forward housing band (muzzle end)
p_rear = probe(0.36, 0.52, 0.00, 0.06)
p_front = probe(0.56, 0.76, -0.02, 0.06)
print("PROBE rear :", p_rear)
print("PROBE front:", p_front)

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

# lettering: patent lines at barrel start, wordmark + dots near muzzle
rx, rz = p_rear
fx, fz = p_front
add_text("MALORIAN ARMS  NIGHT CITY", 0.0075, rx + 0.0005, 0.375, rz + 0.010, "txt_patent1")
add_text("SILVERHAND CUSTOM [PAT.XIJS/001]", 0.0075, rx + 0.0005, 0.375, rz + 0.000, "txt_patent2")
add_text("MALORIAN", 0.018, fx + 0.0005, 0.635, fz + 0.002, "txt_malorian", spacing=1.15)

for r in range(3):
    for c in range(6):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0018, depth=0.0016,
            location=(fx + 0.0005, 0.585 + c * 0.006, fz + 0.016 - r * 0.006),
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

cy, cz, L = 0.36, 0.02, 0.9
views = {
    "side":    ((L * 1.35, cy, cz), (math.radians(90), 0, math.radians(90))),
    "three_q": ((L * 1.0, cy - L * 0.85, cz + L * 0.33), (math.radians(70), 0, math.radians(50))),
}
outdir = os.path.join(ROOT, "renders")
os.makedirs(outdir, exist_ok=True)
for name, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = rot
    scene.render.filepath = os.path.join(outdir, "v7_" + name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
print("KITBASH V6 DONE")

