"""Custom case bottom: drop the pistol/contents submesh -> empty foam."""
import bpy
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
GLB = os.path.join(ROOT, "source", r"base\items\quest\q000__hym_gun_suitcase\q000__gun_suitcase_bottom.glb")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

keep = []
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        continue
    if 'Icosphere' in o.name:
        bpy.data.objects.remove(o, do_unlink=True)
    elif 'submesh_02' in o.name:
        print("dropping contents submesh:", o.name, len(o.data.vertices), "verts")
        bpy.data.objects.remove(o, do_unlink=True)
    else:
        keep.append(o)

def deselect_all():
    for o in bpy.data.objects:
        o.select_set(False)

for o in keep:
    deselect_all(); o.select_set(True); bpy.context.view_layer.objects.active = o
    if len(o.data.uv_layers) == 0:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
        bpy.ops.object.mode_set(mode='OBJECT')
    while len(o.data.uv_layers) > 1:
        o.data.uv_layers.remove(o.data.uv_layers[-1])
    o.data.uv_layers[0].name = "UVMap"
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

deselect_all()
for o in keep:
    o.select_set(True)
bpy.context.view_layer.objects.active = keep[0]
bpy.ops.object.join()
bottom = bpy.context.view_layer.objects.active
bottom.name = "submesh_00_LOD_1"
bottom.data.name = "submesh_00_LOD_1"

deselect_all(); bottom.select_set(True); bpy.context.view_layer.objects.active = bottom
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
print("JOINED bottom:", len(bottom.data.vertices), "verts")

out = os.path.join(ROOT, "cache_case_bottom.glb")
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB',
                          export_materials='NONE', export_apply=True,
                          export_tangents=True)
print("EXPORTED", out)
print("BOTTOM BUILD DONE")
