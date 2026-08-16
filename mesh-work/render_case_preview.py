"""Preview render of the assembled custom cache case (lid + bottom + handle)."""
import bpy
import math
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
SRC = os.path.join(ROOT, "source", r"base\items\quest\q000__hym_gun_suitcase")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def imp(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in list(new):
        if o.type == 'MESH' and 'Icosphere' in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
            new.remove(o)
    return new

imp(os.path.join(ROOT, "cache_case_top.glb"))          # custom lid w/ plaque
imp(os.path.join(ROOT, "cache_case_bottom.glb"))        # custom bottom, empty foam
imp(os.path.join(SRC, "q000__gun_suitcase_handle.glb"))

mat = bpy.data.materials.new("case_metal")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.16, 0.16, 0.18, 1)
b.inputs["Metallic"].default_value = 0.9
b.inputs["Roughness"].default_value = 0.45

for o in bpy.data.objects:
    if o.type == 'MESH':
        o.data.materials.clear()
        o.data.materials.append(mat)

scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.cycles.device = 'CPU'
scene.render.resolution_x = 1400
scene.render.resolution_y = 900

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.35, 0.38, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9

sun_data = bpy.data.lights.new("sun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(35), math.radians(20), math.radians(140))

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 50
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

# lid plateau center ~ (0, 0.21); case ~0.76 x 0.45
views = {
    "top":     ((0.0, 0.0, 1.2), (0, 0, 0)),
    "three_q": ((0.6, -0.75, 0.65), (math.radians(55), 0, math.radians(35))),
    "plaque":  ((0.0, 0.0, 0.6), (0, 0, 0)),
}
outdir = os.path.join(ROOT, "renders")
for name, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = rot
    scene.render.filepath = os.path.join(outdir, f"case_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
print("CASE PREVIEW DONE")


