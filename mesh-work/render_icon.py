"""Render the inventory icon: orthographic side view, transparent background."""
import bpy
import math
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "dioscuri_joined.blend"))
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
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.06, 0.06, 0.075, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

# darken the preview materials for the icon pass (game icons are moody)
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        continue
    if "gunmetal" in mat.name:
        bsdf.inputs["Base Color"].default_value = (0.11, 0.11, 0.125, 1.0)
    elif "red_grip" in mat.name:
        bsdf.inputs["Base Color"].default_value = (0.30, 0.015, 0.02, 1.0)

sun_data = bpy.data.lights.new("sun", 'SUN')
sun_data.energy = 1.5
sun = bpy.data.objects.new("sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(115))

cam_data = bpy.data.cameras.new("cam")
cam_data.type = 'ORTHO'
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

# gun spans y -0.24..0.82, z -0.24..0.13. The icon atlas part claims the
# central 46.9% x 28.9% of this square canvas (600x208 effective px on a
# declared HD_1280_720 atlas), so frame the gun into exactly that band.
cy, cz = 0.29, -0.055
cam.location = (1.2, cy, cz)
cam.rotation_euler = (math.radians(90), 0, math.radians(90))
cam_data.ortho_scale = 2.32   # 1.09m gun spans 46.9% of frame width

scene.render.filepath = os.path.join(ROOT, "renders", "dioscuri_icon.png")
bpy.ops.render.render(write_still=True)
print("ICON RENDERED")
