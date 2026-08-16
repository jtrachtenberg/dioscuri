"""Join the locked v19 kitbash into 3 game-structured submeshes and export GLB.
submesh_00 = gunmetal body, submesh_01 = red grip, submesh_02 = ink lettering."""
import bpy
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "dioscuri_kitbash.blend"))
scene = bpy.context.scene

def deselect_all():
    for o in bpy.data.objects:
        o.select_set(False)

# 1. convert text curves to mesh
for o in list(bpy.data.objects):
    if o.type == 'FONT':
        deselect_all()
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.convert(target='MESH')

# 2. classify
gunmetal, red, ink = [], [], []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    if o.name.startswith('txt_') or o.name.startswith('dot_'):
        ink.append(o)
    elif 'submesh_06' in o.name and o.name.startswith('mal_'):
        red.append(o)
    elif o.name.startswith(('ash_', 'mal_')):
        gunmetal.append(o)
print(f"CLASSIFY gunmetal={len(gunmetal)} red={len(red)} ink={len(ink)}")

# 3. apply all transforms (incl. the 1.2x malorian anchor scale), clear parents
for group in (gunmetal, red, ink):
    for o in group:
        deselect_all()
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        # location MUST be applied too: the WolvenKit GLB importer reads raw
        # vertex buffers and ignores node transforms entirely
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 3b. normalize UVs: every mesh needs exactly one layer named UVMap
for group in (gunmetal, red, ink):
    for o in group:
        deselect_all()
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        uvs = o.data.uv_layers
        if len(uvs) == 0:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
            bpy.ops.object.mode_set(mode='OBJECT')
        while len(o.data.uv_layers) > 1:
            o.data.uv_layers.remove(o.data.uv_layers[-1])
        o.data.uv_layers[0].name = "UVMap"

# 4. join each group
def join(objs, name):
    deselect_all()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = name
    joined.data.name = name
    return joined

m0 = join(gunmetal, "submesh_00_LOD_1")
m1 = join(red, "submesh_01_LOD_1")
m2 = join(ink, "submesh_02_LOD_1")

for m in (m0, m1, m2):
    print(f"JOINED {m.name}: {len(m.data.vertices)} verts")

# 4b. triangulate everything (importer requirement)
for m in (m0, m1, m2):
    deselect_all()
    m.select_set(True)
    bpy.context.view_layer.objects.active = m
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.object.mode_set(mode='OBJECT')

# 5. export just the three, with tangents
deselect_all()
for m in (m0, m1, m2):
    m.select_set(True)
out = os.path.join(ROOT, "dioscuri_body.glb")
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB',
                          export_materials='NONE', export_apply=True,
                          export_tangents=True)
print("EXPORTED", out)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "dioscuri_joined.blend"))
print("EXPORT DONE")
