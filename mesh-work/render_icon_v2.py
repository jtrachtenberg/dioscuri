"""Render the inventory icon from the CURRENT model (silencer + black parts),
darker pass: game icons sit moodier than our first render."""
import bpy
import math
import os
import mathutils

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "dioscuri_joined_v2.blend"))
scene = bpy.context.scene

scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.cycles.device = 'CPU'
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.film_transparent = True

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.065, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.06

# icon-pass material darkening (deeper than v1 â€” icons read brighter in the grid)
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
key_data.size = 2.4     # long strip along the gun
key_data.size_y = 0.5
key = bpy.data.objects.new("key", key_data)
scene.collection.objects.link(key)

fill_data = bpy.data.lights.new("fill", 'SUN')
fill_data.energy = 0.12
fill = bpy.data.objects.new("fill", fill_data)
scene.collection.objects.link(fill)
fill.rotation_euler = (0, math.radians(80), 0)  # frontal fill from camera side

cam_data = bpy.data.cameras.new("cam")
cam_data.type = 'ORTHO'
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

# frame the (now longer) gun into the same 46.9% central band the atlas
# part expects: gun bbox measured live
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
cam.location = (1.2, cy, cz)
cam.rotation_euler = (math.radians(90), 0, math.radians(90))
key.location = (0.7, cy, cz + 0.85)
d = mathutils.Vector((0, cy, cz)) - mathutils.Vector(key.location)
key.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
key.rotation_euler.rotate_axis("Z", math.radians(90))   # strip runs along gun length
cam_data.ortho_scale = span_y / 0.469
print("frame: span %.3f center (%.3f, %.3f) ortho %.3f" % (span_y, cy, cz, cam_data.ortho_scale))

scene.render.filepath = os.path.join(ROOT, "renders", "dioscuri_icon_v2.png")
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(os.path.join(ROOT, "renders", "dioscuri_icon_v2.png"))
px = list(img.pixels)
for i in range(0, len(px), 4):
    px[i] = px[i] ** 3.0
    px[i + 1] = px[i + 1] ** 3.0
    px[i + 2] = px[i + 2] ** 3.0
img.pixels = px
img.save()
print("ICON V2 RENDERED + dimmed 15%")












