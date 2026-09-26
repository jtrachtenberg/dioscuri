"""Join the user-edited kitbash (dioscuri_kitbash_edit.blend) into 4
game-structured submeshes and export GLB.
submesh_00 = gunmetal body, submesh_01 = red grip, submesh_02 = ink lettering,
submesh_03 = black parts (user-painted 'blackmetal' + 'blackmetal.001').
Grouping is by MATERIAL (not object name) so face-level edits carry over.

Usage (both forms work):
  blender --background --python export_game_mesh_v2.py
  blender <file.blend> --background --python export_game_mesh_v2.py -- <out.glb>
With no .blend on the command line the script opens dioscuri_kitbash_edit.blend
next to itself; with no "-- <out.glb>" it writes dioscuri_body.glb next to itself.
Any failure exits Blender with status 1 (Blender itself exits 0 when a --python
script raises), so build.ps1 / ModWright stop instead of shipping a stale GLB."""
import bpy
import os
import re
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BLEND = os.path.join(HERE, "dioscuri_kitbash_edit.blend")
DEFAULT_OUT = os.path.join(HERE, "dioscuri_body.glb")
MAX_SUBMESH_VERTS = 65535   # engine cap per submesh (see HANDOFF)


def deselect_all():
    for o in bpy.data.objects:
        o.select_set(False)


def unhide_everything():
    """Make every object selectable/editable: view-layer hide, viewport hide,
    select lock, and hidden/excluded collections all block the edit-mode ops."""
    def walk(lc):
        lc.exclude = False
        lc.hide_viewport = False
        for child in lc.children:
            walk(child)
    for lc in bpy.context.view_layer.layer_collection.children:
        walk(lc)   # the scene's root collection itself can't be excluded
    for c in bpy.data.collections:
        c.hide_viewport = False
        c.hide_select = False
    bpy.context.view_layer.update()
    for o in bpy.data.objects:
        o.hide_viewport = False
        o.hide_select = False
        if o.name in bpy.context.view_layer.objects:
            o.hide_set(False)


def base_material_name(name):
    """Blender auto-renames appended/duplicated materials to 'name.001'."""
    return re.sub(r"\.\d{3}$", "", name)


# 5. join groups in fixed submesh order (00..02 keep their old indices,
# black appends as 03 so existing chunkMaterials stay valid)
def join(objs, name):
    if not objs:
        # skipping would shift every later submesh index and break the
        # mesh's chunkMaterials, so refuse instead
        raise RuntimeError(f"no objects for {name}: its material group is empty")
    deselect_all()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = name
    joined.data.name = name
    return joined


def main(out):
    if not bpy.data.filepath:
        bpy.ops.wm.open_mainfile(filepath=DEFAULT_BLEND)
    print("SOURCE", bpy.data.filepath)
    # never leave a previous export behind for a later step to pick up
    if os.path.exists(out):
        os.remove(out)

    # 0. drop armatures (bones came along with the source GLBs; meshes keep
    # their world transform via parent_clear below)
    unhide_everything()
    for o in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        for child in o.children:
            deselect_all()
            child.hide_set(False)
            child.select_set(True)
            bpy.context.view_layer.objects.active = child
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        bpy.data.objects.remove(o, do_unlink=True)

    # unhide everything else so ops can touch it
    unhide_everything()

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
        slots = o.data.materials
        idx = o.data.polygons[0].material_index
        if slots and idx >= len(slots):
            raise RuntimeError(f"{o.name}: faces use material slot {idx} but the "
                               f"object has only {len(slots)} slot(s)")
        mat = slots[idx] if slots else None
        name = base_material_name(mat.name) if mat else "Default"
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

    # 5d. engine cap. Blender's count is a lower bound: the GLB splits
    # vertices further along UV seams and hard edges.
    for m in joined:
        if len(m.data.vertices) > MAX_SUBMESH_VERTS:
            raise RuntimeError(f"{m.name} has {len(m.data.vertices)} verts, over the "
                               f"{MAX_SUBMESH_VERTS}-per-submesh engine limit")

    # 6. export just the four, with tangents
    deselect_all()
    for m in joined:
        m.select_set(True)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB',
                              export_materials='NONE', export_apply=True,
                              export_tangents=True)
    if not os.path.isfile(out):
        raise RuntimeError(f"glTF exporter wrote nothing to {out}")
    print("EXPORTED", out)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "dioscuri_joined_v2.blend"))
    print("EXPORT V2 DONE")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    try:
        main(os.path.abspath(argv[0]) if argv else DEFAULT_OUT)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
