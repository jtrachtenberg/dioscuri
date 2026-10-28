"""Skin Dioscuri's shipped body mesh to the vanilla Ashura's base1 rig, so the
Ashura's own reload clips move its bolt (2026-10-28).

Why: on 2.5 a user reported Dioscuri has "no reload animation". V's hands
reload; the GUN does not move, because dioscuri_body is one static mesh. The
kitbash (kitbash_v22.py) built Dioscuri's receiver from the Ashura's own
w_rifle_sniper__tsunami_ashura__base1_01 geometry, untransformed. So every
moving piece of the Ashura (bolt = cocking_mechanism, hammer, l_grip, r_grip)
is in Dioscuri's mesh at the same place, vertex for vertex. Nothing is cut:
each vertex is skinned to the bone its twin is skinned to on the Ashura, and
everything else to 'barrel' (which the Ashura's clips never move).

How a vertex is classified: the nearest Ashura vertex (KD-tree) within TOL
gives its strongest bone. A connected island moves only if at least
ISLAND_MIN of its vertices land on one moving bone; measured on the 1.1.0 mesh,
111 islands are 100% moving and 9 static islands touch the bolt with 1-2
vertices (1-6%), so the threshold has a wide margin either side.

In:  ashura-reload/dioscuri/mod/dioscuri/meshes/dioscuri_body.glb (uncook of
     the deployed 1.1.0 archive: the geometry exactly as it ships)
     ashura-reload/uncooked/.../w_rifle_sniper__tsunami_ashura__base1_01.glb
     (vanilla, default uncook: its skin carries the real bone names)
Out: ashura-reload/work/dioscuri_body_skinned.glb, the same four submeshes as
     export_game_mesh_v2.py wrote (no materials, tangents, one UV map), plus a
     skin on the Ashura's bones. finish_moving_parts.py takes it from there.

Run: & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python build_moving_parts.py
"""
import bpy, bmesh, os
from mathutils import kdtree
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, 'ashura-reload')
DIO = os.path.join(R, 'dioscuri', 'mod', 'dioscuri', 'meshes', 'dioscuri_body.glb')
ASH = os.path.join(R, 'uncooked', 'base', 'weapons', 'firearms', 'rifle_sniper', 'tsunami_ashura',
                   'entities', 'meshes', 'w_rifle_sniper__tsunami_ashura__base1_01.glb')
OUT = os.path.join(R, 'work', 'dioscuri_body_skinned.glb')
TOL = 0.0003          # 0.3 mm: a twin vertex, not a neighbour
ISLAND_MIN = 0.9      # share of an island's vertices that must be on a moving bone
STATIC = 'barrel'     # never moved by the Ashura's clips (0.0 mm, build_ashura_reload_blend.py)
MOVING = {'cocking_mechanism', 'hammer', 'l_grip', 'r_grip'}


def imp(path):
    assert os.path.exists(path), path
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.name.startswith('Icosphere')]:  # WolvenKit's junk sphere
        new.remove(o)
        bpy.data.objects.remove(o, do_unlink=True)
    return new


bpy.ops.wm.read_homefile(use_empty=True)
ash = imp(ASH)
ash_arm = [o for o in ash if o.type == 'ARMATURE'][0]
ash_arm.name = 'ashura_base1'
bones = {b.name for b in ash_arm.data.bones}
assert MOVING | {STATIC} <= bones, bones

# Ashura twin lookup: LOD_1 vertices and their strongest bone
pts = []
for o in ash:
    if o.type != 'MESH' or 'LOD_1' not in o.name:
        continue
    gname = {g.index: g.name for g in o.vertex_groups}
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight, default=None)
        pts.append((o.matrix_world @ v.co, gname.get(g.group) if g else None))
kd = kdtree.KDTree(len(pts))
for i, (p, _) in enumerate(pts):
    kd.insert(p, i)
kd.balance()
for o in ash:  # done with the Ashura's meshes; they would hold the submesh_0N names
    if o.type == 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)

dio = imp(DIO)
meshes = sorted([o for o in dio if o.type == 'MESH'], key=lambda o: o.name)
assert len(meshes) == 4, [o.name for o in meshes]
total = Counter()
for o in meshes:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    o.vertex_groups.clear()
    bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects:
        x.select_set(x is o)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.name = o.name.split('.')[0]          # submesh_0N_LOD_1, the name WolvenKit groups by
    o.data.name = o.name
    assert '.' not in o.name, o.name

    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    twin = {}
    for v in bm.verts:
        _, i, d = kd.find(v.co)
        twin[v.index] = pts[i][1] if d <= TOL else None
    seen = set()
    bone_of = {}
    for v in bm.verts:
        if v.index in seen:
            continue
        isl, stack = [], [v]
        seen.add(v.index)
        while stack:
            x = stack.pop()
            isl.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index)
                    stack.append(y)
        c = Counter(twin[i] for i in isl if twin[i] in MOVING)
        top = c.most_common(1)
        moving = top and top[0][1] >= ISLAND_MIN * len(isl)
        for i in isl:
            bone_of[i] = top[0][0] if moving else STATIC
    bm.free()

    groups = {b: o.vertex_groups.new(name=b) for b in sorted(set(bone_of.values()) | {STATIC})}
    by_bone = {}
    for i, b in bone_of.items():
        by_bone.setdefault(b, []).append(i)
    for b, idx in by_bone.items():
        groups[b].add(idx, 1.0, 'REPLACE')
    counts = Counter(bone_of.values())
    total.update(counts)
    print('SKIN %s: %d verts %s' % (o.name, len(o.data.vertices), dict(counts)))

    o.parent = ash_arm
    o.matrix_parent_inverse = ash_arm.matrix_world.inverted()
    mod = o.modifiers.new('Armature', 'ARMATURE')
    mod.object = ash_arm

    # as export_game_mesh_v2.py: one UV map named UVMap
    while len(o.data.uv_layers) > 1:
        o.data.uv_layers.remove(o.data.uv_layers[-1])
    o.data.uv_layers[0].name = 'UVMap'

print('SKIN TOTAL', dict(total))
assert total['cocking_mechanism'] > 5000 and total['hammer'] > 1000, 'the bolt was not found'

for o in [o for o in bpy.data.objects if o.type == 'ARMATURE' and o is not ash_arm]:
    bpy.data.objects.remove(o, do_unlink=True)  # the Malorian-donor armature of the shipped mesh

os.makedirs(os.path.dirname(OUT), exist_ok=True)
for x in bpy.data.objects:
    x.select_set(x in meshes or x is ash_arm)
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format='GLB',
                          export_materials='NONE', export_apply=False, export_skins=True,
                          export_animations=False, export_tangents=True)
assert os.path.exists(OUT), OUT
print('EXPORTED', OUT)

# Gate: the export holds the shipped geometry, vertex for vertex (positions only;
# a re-import of each submesh against the shipped one, both directions)
ref = {o.name: [v.co.copy() for v in o.data.vertices] for o in meshes}
bpy.ops.wm.read_homefile(use_empty=True)
back = [o for o in imp(OUT) if o.type == 'MESH']
for o in sorted(back, key=lambda o: o.name):
    name = o.name.split('.')[0]
    r = ref[name]
    kr = kdtree.KDTree(len(r))
    for i, p in enumerate(r):
        kr.insert(p, i)
    kr.balance()
    worst = max(kr.find(o.matrix_world @ v.co)[2] for v in o.data.vertices)
    kb = kdtree.KDTree(len(o.data.vertices))
    for i, v in enumerate(o.data.vertices):
        kb.insert(o.matrix_world @ v.co, i)
    kb.balance()
    worst = max(worst, max(kb.find(p)[2] for p in r))
    joints = sorted(g.name for g in o.vertex_groups)
    print('ROUNDTRIP %s: %d verts (shipped %d), worst %.7f m, groups %s' % (name, len(o.data.vertices), len(r), worst, joints))
    assert worst < 1e-5, '%s moved %.6f m in the export' % (name, worst)
print('BUILD MOVING PARTS DONE')
