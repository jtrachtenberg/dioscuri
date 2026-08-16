"""Render the gun case top with textures to locate the Constitutional Arms logo."""
import bpy
import math
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
GLB = os.path.join(ROOT, "source", r"base\items\quest\q000__hym_gun_suitcase\q000__gun_suitcase_top.glb")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=GLB)

for o in list(bpy.data.objects):
    if o.type == 'MESH' and 'Icosphere' in o.name:
        bpy.data.objects.remove(o, do_unlink=True)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
xs, ys, zs = [], [], []
dg = bpy.context.evaluated_depsgraph_get()
for o in meshes:
    eo = o.evaluated_get(dg)
    m = eo.to_mesh()
    for v in m.vertices:
        w = eo.matrix_world @ v.co
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
    eo.to_mesh_clear()
print("TOP bounds x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.device = 'CPU'
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.film_transparent = True

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.2

cx = (min(xs) + max(xs)) / 2
cy = (min(ys) + max(ys)) / 2
cz = (min(zs) + max(zs)) / 2
span = max(max(xs) - min(xs), max(ys) - min(ys))

cam_data = bpy.data.cameras.new("cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = span * 1.2
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (cx, cy, cz + 2.0)
cam.rotation_euler = (0, 0, 0)

outdir = os.path.join(ROOT, "renders")
scene.render.filepath = os.path.join(outdir, "case_top_topview.png")
bpy.ops.render.render(write_still=True)
print("CASE TOP RENDERED")
