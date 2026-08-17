"""Nexus header: 1300x372, gun with the inventory-icon lighting on a
near-black backdrop, Malorian seven-dot logo top-left."""
import bpy
import math
import os
import mathutils

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "dioscuri_joined_v2.blend"))
scene = bpy.context.scene

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.cycles.device = 'CPU'
scene.render.resolution_x = 1300
scene.render.resolution_y = 372
scene.render.film_transparent = False   # opaque near-black backdrop

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.065, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.06

# pin icon-pass materials
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        continue
    if "gunmetal" in mat.name:
        bsdf.inputs["Base Color"].default_value = (0.11, 0.11, 0.125, 1.0)
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.30
    elif "red_grip" in mat.name:
        bsdf.inputs["Base Color"].default_value = (0.30, 0.015, 0.02, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.15
    elif "blackmetal" in mat.name:
        bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.9

key_data = bpy.data.lights.new("key", 'AREA')
key_data.energy = 85
key_data.shape = 'RECTANGLE'
key_data.size = 2.4
key_data.size_y = 0.5
key = bpy.data.objects.new("key", key_data)
scene.collection.objects.link(key)

fill_data = bpy.data.lights.new("fill", 'SUN')
fill_data.energy = 0.12
fill = bpy.data.objects.new("fill", fill_data)
scene.collection.objects.link(fill)
fill.rotation_euler = (0, math.radians(80), 0)

# frame the gun across the banner
ys, zs = [], []
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    for c in ob.bound_box:
        w = ob.matrix_world @ mathutils.Vector(c)
        ys.append(w.y)
        zs.append(w.z)
span_y = max(ys) - min(ys)
cy = (min(ys) + max(ys)) / 2
cz = (min(zs) + max(zs)) / 2

cam_data = bpy.data.cameras.new("cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = span_y / 0.90    # gun fills 90% of the width
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (1.2, cy, cz - 0.006)
cam.rotation_euler = (math.radians(90), 0, math.radians(90))

key.location = (0.7, cy, cz + 0.85)
d = mathutils.Vector((0, cy, cz)) - mathutils.Vector(key.location)
key.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
key.rotation_euler.rotate_axis('Z', math.radians(90))

# Malorian seven-dot logo, top-left of frame (view right = +y)
dot_mat = bpy.data.materials.new("logo_dot")
dot_mat.use_nodes = True
nt = dot_mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (0.75, 0.78, 0.82, 1.0)
em.inputs["Strength"].default_value = 1.0
nt.links.new(em.outputs[0], out.inputs[0])

view_w = cam_data.ortho_scale
view_h = view_w * 372.0 / 1300.0
y_left = cy - view_w / 2.0
z_top = cz + view_h / 2.0
DOT_R = 0.011
STEP = 0.032
oy = y_left + 0.10          # inset from left edge
oz = z_top - 0.055          # inset from top edge
for r in range(2):
    for c in range(4):
        if r == 1 and c == 3:
            continue
        bpy.ops.mesh.primitive_circle_add(vertices=48, radius=DOT_R, fill_type='NGON',
            location=(0.5, oy + c * STEP, oz - r * STEP))
        dot = bpy.context.active_object
        dot.rotation_euler = (0, math.radians(90), 0)
        dot.data.materials.append(dot_mat)

scene.render.filepath = os.path.join(ROOT, "renders", "nexus_header.png")
bpy.ops.render.render(write_still=True)
print("HEADER RENDERED 1300x372")
