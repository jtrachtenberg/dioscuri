"""Closed-case lid: gun-case top FLIPPED shut onto the bottom, with the
embossed MALORIAN plaque on the upward face. Exports cache_case_top.glb."""
import bpy
import math
import os
from mathutils import Matrix

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
SRC = os.path.join(ROOT, "source", r"base\items\quest\q000__hym_gun_suitcase")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def deselect_all():
    for o in bpy.data.objects:
        o.select_set(False)

def imp(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in list(new):
        if o.type == 'MESH' and ('Icosphere' in o.name or len(o.data.vertices) < 100):
            bpy.data.objects.remove(o, do_unlink=True)
            new.remove(o)
    return [o for o in new if o.type == 'MESH']

def bbox(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    xs, ys, zs = [], [], []
    for o in objs:
        eo = o.evaluated_get(dg)
        m = eo.to_mesh()
        for v in m.vertices:
            w = eo.matrix_world @ v.co
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
        eo.to_mesh_clear()
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

lid_parts = imp(os.path.join(SRC, "q000__gun_suitcase_top.glb"))
bottom_parts = imp(os.path.join(ROOT, "cache_case_bottom.glb"))

# join lid geometry first
for o in lid_parts:
    deselect_all(); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
deselect_all()
for o in lid_parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = lid_parts[0]
bpy.ops.object.join()
lid = bpy.context.view_layer.objects.active

lb = bbox([lid]); bb = bbox(bottom_parts)
print("lid bbox   x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (*lb[0], *lb[1], *lb[2]))
print("bottom bbox x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (*bb[0], *bb[1], *bb[2]))

# close the lid EXTERIOR-UP: the open pose already has the exterior facing
# up, so no fold is needed — spin 180 about Z (hinge-to-hinge alignment)
# and translate onto the bottom
lc_x = (lb[0][0] + lb[0][1]) / 2
lc_y = (lb[1][0] + lb[1][1]) / 2
lc_z = (lb[2][0] + lb[2][1]) / 2
piv = Matrix.Translation((lc_x, lc_y, lc_z))
rot = piv @ Matrix.Rotation(math.pi, 4, 'Z') @ piv.inverted()
lid.matrix_world = rot @ lid.matrix_world
deselect_all(); lid.select_set(True); bpy.context.view_layer.objects.active = lid
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

lb2 = bbox([lid])
dy = ((bb[1][0] + bb[1][1]) / 2) - ((lb2[1][0] + lb2[1][1]) / 2)
dz = (bb[2][1] - 0.005) - lb2[2][0]
lid.location = (0, dy, dz)
deselect_all(); lid.select_set(True); bpy.context.view_layer.objects.active = lid
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
lb3 = bbox([lid])
print("closed lid  x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (*lb3[0], *lb3[1], *lb3[2]))

# --- plaque on the upward face ---------------------------------------
# raycast straight down at the case center: exact top-face height,
# immune to sparse vertices on big flat faces
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
hit, loc, normal, _, hit_obj, _ = scene.ray_cast(dg, Vector((0.0, 0.0, 1.0)), Vector((0.0, 0.0, -1.0)))
if not hit:
    raise RuntimeError("raycast missed the case top")
px, py, pz = 0.0, 0.0, loc.z
print("raycast hit %s at z %.3f" % (hit_obj.name, pz))
print("plaque anchor (%.3f, %.3f) z %.3f" % (px, py, pz))

bpy.ops.mesh.primitive_cube_add(location=(px, py, pz + 0.002))
plate = bpy.context.active_object
plate.scale = (0.115, 0.0375, 0.002)
deselect_all(); plate.select_set(True); bpy.context.view_layer.objects.active = plate
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

curve = bpy.data.curves.new("plaque_text", 'FONT')
curve.body = "MALORIAN"
curve.size = 0.034
curve.extrude = 0.0025
curve.space_character = 1.1
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
txt = bpy.data.objects.new("plaque_text", curve)
scene.collection.objects.link(txt)
txt.location = (px - 0.018, py, pz + 0.004)
deselect_all(); txt.select_set(True); bpy.context.view_layer.objects.active = txt
bpy.ops.object.convert(target='MESH')
txt = bpy.context.active_object
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

dots = []
DX, DY0, STEP = px + 0.096, py + 0.009, 0.0115
for r in range(2):
    for c in range(4):
        if r == 1 and c == 3:
            continue
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0045, segments=16, ring_count=8,
            location=(DX + c * STEP, DY0 - r * 0.018, pz + 0.0045))
        d = bpy.context.active_object
        deselect_all(); d.select_set(True); bpy.context.view_layer.objects.active = d
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        dots.append(d)

# --- UVs, join, tris, export -----------------------------------------
allobjs = [lid, plate, txt] + dots
for o in allobjs:
    deselect_all(); o.select_set(True); bpy.context.view_layer.objects.active = o
    if len(o.data.uv_layers) == 0:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
        bpy.ops.object.mode_set(mode='OBJECT')
    while len(o.data.uv_layers) > 1:
        o.data.uv_layers.remove(o.data.uv_layers[-1])
    o.data.uv_layers[0].name = "UVMap"

deselect_all()
for o in allobjs:
    o.select_set(True)
bpy.context.view_layer.objects.active = allobjs[0]
bpy.ops.object.join()
final = bpy.context.view_layer.objects.active
final.name = "submesh_00_LOD_1"
final.data.name = "submesh_00_LOD_1"
deselect_all(); final.select_set(True); bpy.context.view_layer.objects.active = final
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
print("JOINED closed lid:", len(final.data.vertices), "verts")

out = os.path.join(ROOT, "cache_case_top.glb")
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB',
                          export_materials='NONE', export_apply=True,
                          export_tangents=True)
print("EXPORTED", out)
print("LID BUILD DONE")
