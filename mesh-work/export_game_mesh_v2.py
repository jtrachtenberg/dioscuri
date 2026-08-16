"""Join the user-edited kitbash (dioscuri_kitbash_edit.blend) into 4
game-structured submeshes and export GLB.
submesh_00 = gunmetal body, submesh_01 = red grip, submesh_02 = ink lettering,
submesh_03 = black parts (user-painted 'blackmetal' + 'blackmetal.001').
Grouping is by MATERIAL (not object name) so face-level edits carry over."""
import bpy
import os

ROOT = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "dioscuri_kitbash_edit.blend"))
scene = bpy.context.scene

def deselect_all():
    for o in bpy.data.objects:
        o.select_set(False)

# 0. drop armatures (bones came along with the source GLBs; meshes keep
# their world transform via parent_clear below)
for o in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    for child in o.children:
        deselect_all()
        child.hide_set(False)
        child.select_set(True)
        bpy.context.view_layer.objects.active = child
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.data.objects.remove(o, do_unlink=True)

# unhide everything else so ops can touch it
for o in bpy.data.objects:
    o.hide_set(False)

# 0b. drop WolvenKit junk Icospheres (ride along in every exported GLB)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and 'Icosphere' in o.name]:
    bpy.data.objects.remove(o, do_unlink=True)

# 0c. free up the final submesh names: imported donor parts (e.g. the
# silencer arrived named submesh_00_LOD_1) would otherwise collide with
# the joined outputs and leave them named submesh_00_LOD_1.002
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('submesh_'):
        o.name = "part_" + o.name

# 1. convert text curves to mesh
for o in list(bpy.data.objects):
    if o.type == 'FONT':
        deselect_all()
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.convert(target='MESH')

# 2. separate multi-material objects so each object is single-material
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    used = {p.material_index for p in o.data.polygons}
    if len(used) > 1:
        deselect_all()
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.separate(type='MATERIAL')
        bpy.ops.object.mode_set(mode='OBJECT')

# 3. classify every mesh object by the material its faces actually use
groups = {"gunmetal": [], "red_grip": [], "text_ink": [], "black": []}
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.data.polygons:
        continue
    mat = o.data.materials[o.data.polygons[0].material_index] if o.data.materials else None
    name = mat.name if mat else "Default"
    # glTF placeholder "Default" (e.g. the imported silencer body) counts as black
    if name.startswith("blackmetal") or name == "Default":
        groups["black"].append(o)
    elif name in groups:
        groups[name].append(o)
    else:
        raise RuntimeError(f"unclassified material {name!r} on {o.name}")
for k, v in groups.items():
    print(f"CLASSIFY {k} = {len(v)} objects")

# 4. apply transforms, clear parents (WolvenKit ignores node transforms)
for group in groups.values():
    for o in group:
        deselect_all()
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 4b. normalize UVs: exactly one layer named UVMap
for group in groups.values():
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

# 5. join groups in fixed submesh order (00..02 keep their old indices,
# black appends as 03 so existing chunkMaterials stay valid)
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

order = [("gunmetal", "submesh_00_LOD_1"), ("red_grip", "submesh_01_LOD_1"),
         ("text_ink", "submesh_02_LOD_1"), ("black", "submesh_03_LOD_1")]
joined = []
for key, name in order:
    m = join(groups[key], name)
    joined.append(m)
    print(f"JOINED {name}: {len(m.data.vertices)} verts")

# 5b. triangulate (importer requirement)
for m in joined:
    deselect_all()
    m.select_set(True)
    bpy.context.view_layer.objects.active = m
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.object.mode_set(mode='OBJECT')

# 5c. double-side the black submesh (rides our one-sided custom material;
# shell parts like the scope knob would show see-through holes otherwise).
# gunmetal CANNOT be doubled wholesale: 2x 47k verts exceeds the engine's
# 65535-per-submesh limit — inward-facing gunmetal faces get fixed at the
# source in Blender instead (flip normals / fill the missing wall)
ds = joined[3]
deselect_all()
ds.select_set(True)
bpy.context.view_layer.objects.active = ds
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.duplicate()
bpy.ops.mesh.flip_normals()
bpy.ops.object.mode_set(mode='OBJECT')
print(f"DOUBLED {ds.name}: now {len(ds.data.vertices)} verts")

# 6. export just the four, with tangents
deselect_all()
for m in joined:
    m.select_set(True)
out = os.path.join(ROOT, "dioscuri_body.glb")
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB',
                          export_materials='NONE', export_apply=True,
                          export_tangents=True)
print("EXPORTED", out)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "dioscuri_joined_v2.blend"))
print("EXPORT V2 DONE")
