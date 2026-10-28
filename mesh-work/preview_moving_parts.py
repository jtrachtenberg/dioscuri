"""Check finish_moving_parts.py's mesh in Blender before any launch (2026-10-28).

Takes the built dioscuri_body.mesh as the game will read it (packed and
uncooked back: ashura-reload/work/verify/), binds it to the Ashura's base1
animation rig, adds the Ashura cartridge on its mag_std rig (as the patched
.app does), and plays the Ashura's empty_reload.
Gates:
- every vertex is where 1.1.0 has it (the shipped GLB), to the format's
  position quantization;
- the skin: vertices per bone as build_moving_parts.py assigned them;
- in the clip, 'barrel' vertices never move and the bolt travels ~10 cm.
Renders (ashura-reload/preview/): dioscuri_bolt_strip.png (close on the bolt
through the clip) and dioscuri_round_rest.png (frame 0, close, the cartridge
in red: is it hidden inside the gun at rest?).

Run: & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python preview_moving_parts.py
"""
import bpy, os, math
from mathutils import Vector, kdtree
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, 'ashura-reload')
VERIFY = os.path.join(R, 'work', 'verify', 'uncook', 'mod', 'dioscuri', 'meshes', 'dioscuri_body_verify.glb')
SHIPPED = os.path.join(R, 'dioscuri', 'mod', 'dioscuri', 'meshes', 'dioscuri_body.glb')
U = os.path.join(R, 'uncooked', 'base')
ANIM = os.path.join(U, 'animations', 'weapon', 'firearms', 'rifle_sniper', 'tsunami_ashura')
BODY_ANIMS = os.path.join(ANIM, 'w_rifle_sniper__tsunami_ashura__base1.anims.glb')
MAG_ANIMS = os.path.join(ANIM, 'w_rifle_sniper__tsunami_ashura__mag_std.anims.glb')
MAG_MESH = os.path.join(U, 'weapons', 'firearms', 'rifle_sniper', 'tsunami_ashura', 'entities', 'meshes',
                        'w_rifle_sniper__tsunami_ashura__mag_std_01.glb')
PREVIEW = os.path.join(R, 'preview')
CLIP = 'empty_reload'
ROUND = False   # keep in step with finish_moving_parts.py
EXPECT = {'barrel': 70298, 'cocking_mechanism': 5534, 'hammer': 1147, 'l_grip': 392, 'r_grip': 396}


def imp(path, addon=False):
    assert os.path.exists(path), path
    before = set(bpy.data.objects)
    acts = set(bpy.data.actions)
    if addon:
        bpy.ops.io_scene_gltf.cp77(filepath=path, scripting=True, hide_armatures=False)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.name.startswith('Icosphere')]:
        new.remove(o)
        bpy.data.objects.remove(o, do_unlink=True)
    return new, [a for a in bpy.data.actions if a not in acts]


def rig_with_clip(path, part):
    new, acts = imp(path, addon=True)   # .anims always through the addon
    rig = [o for o in new if o.type == 'ARMATURE'][0]
    rig.name = 'rig_' + part
    a = [x for x in acts if x.name.split('.')[0] == CLIP][0]  # the 2nd rig's comes in as empty_reload.001
    rig.animation_data_create()
    rig.animation_data.action = a
    if len(a.slots):
        rig.animation_data.action_slot = a.slots[0]
    return rig, a


def bind(meshes, arms, rig):
    for o in meshes:
        for m in [m for m in o.modifiers if m.type == 'ARMATURE']:
            m.object = rig
        mw = o.matrix_world.copy()
        o.parent = rig
        o.matrix_world = mw
    for a in arms:
        bpy.data.objects.remove(a, do_unlink=True)


bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene

# shipped geometry, for the position gate
shp, _ = imp(SHIPPED)
ref = {}
for o in shp:
    if o.type == 'MESH':
        ref[o.name.split('.')[0]] = [o.matrix_world @ v.co for v in o.data.vertices]
for o in shp:
    bpy.data.objects.remove(o, do_unlink=True)

new, _ = imp(VERIFY)
dio = sorted([o for o in new if o.type == 'MESH'], key=lambda o: o.name)
counts = Counter()
for o in dio:
    names = {g.index: g.name for g in o.vertex_groups}
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        counts[names[g.group]] += 1
    r = ref[o.name.split('.')[0]]
    kd = kdtree.KDTree(len(r))
    for i, p in enumerate(r):
        kd.insert(p, i)
    kd.balance()
    worst = max(kd.find(o.matrix_world @ v.co)[2] for v in o.data.vertices)
    print('GEOMETRY %s: %d verts, farthest from 1.1.0 %.6f m' % (o.name, len(o.data.vertices), worst))
    assert worst < 1e-4, '%s moved %.6f m' % (o.name, worst)
print('SKIN', dict(counts))
for b, n in EXPECT.items():
    assert abs(counts[b] - n) <= max(100, n * 0.01), 'skin %s: %d, expected ~%d' % (b, counts[b], n)

body_rig, act = rig_with_clip(BODY_ANIMS, 'body')
bind(dio, [o for o in new if o.type == 'ARMATURE'], body_rig)

rnd = []
if ROUND:
    mnew, _ = imp(MAG_MESH)   # the vanilla cartridge (stock importer: the addon dies on its material)
    rnd = [o for o in mnew if o.type == 'MESH']
    mag_rig, _ = rig_with_clip(MAG_ANIMS, 'mag')
    bind(rnd, [o for o in mnew if o.type == 'ARMATURE'], mag_rig)
    for o in rnd:
        if 'LOD_' in o.name and 'LOD_1' not in o.name:
            o.hide_render = True

f0, f1 = (int(round(x)) for x in act.frame_range)
scene.frame_start, scene.frame_end = f0, f1


def evaluated(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for o in objs:
        e = o.evaluated_get(dg)
        m = e.to_mesh()
        out[o.name] = [e.matrix_world @ v.co for v in m.vertices]
        e.to_mesh_clear()
    return out


scene.frame_set(f0)
rest = evaluated(dio)
moved = Counter()
for f in range(f0, f1 + 1, 3):
    scene.frame_set(f)
    cur = evaluated(dio)
    for o in dio:
        names = {g.index: g.name for g in o.vertex_groups}
        for v, a, b in zip(o.data.vertices, rest[o.name], cur[o.name]):
            g = names[max(v.groups, key=lambda g: g.weight).group]
            moved[g] = max(moved[g], (a - b).length)
print('MOVES in %s:' % CLIP, {k: '%.1f mm' % (v * 1000) for k, v in moved.items()})
assert moved['barrel'] < 1e-5, 'static geometry moved %.4f m' % moved['barrel']
assert 0.08 < moved['cocking_mechanism'] < 0.12, 'bolt travel %.4f m' % moved['cocking_mechanism']

# renders
os.makedirs(PREVIEW, exist_ok=True)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'OBJECT'
scene.render.resolution_x, scene.render.resolution_y = 960, 540
for o in dio:
    o.color = (0.6, 0.6, 0.65, 1)
for o in rnd:
    o.color = (0.95, 0.15, 0.1, 1)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.rotation_euler = (math.pi / 2, 0, math.pi / 2)   # the gun's right side
scene.camera = cam
scene.frame_set(f0)
c0 = (body_rig.matrix_world @ body_rig.pose.bones['cocking_mechanism'].matrix).translation
cam.data.ortho_scale = 0.45
cam.location = Vector((3.0, c0.y - 0.04, c0.z - 0.03))
frames = [f0 + round(i * (f1 - f0) / 7) for i in range(8)]
paths = []
for f in frames:
    scene.frame_set(f)
    scene.render.filepath = os.path.join(PREVIEW, 'dioscuri_bolt_%03d.png' % f)
    bpy.ops.render.render(write_still=True)
    assert os.path.exists(scene.render.filepath)
    paths.append(scene.render.filepath)
scene.frame_set(f0)
scene.render.filepath = os.path.join(PREVIEW, 'dioscuri_round_rest.png')
bpy.ops.render.render(write_still=True)
# and from below, where a magazine well would show it
cam.rotation_euler = (0, 0, 0)
cam.location = Vector((0, c0.y - 0.04, -3.0))
cam.rotation_euler = (math.pi, 0, 0)
scene.render.filepath = os.path.join(PREVIEW, 'dioscuri_round_rest_below.png')
bpy.ops.render.render(write_still=True)
print('PREVIEW', frames)
print('PREVIEW MOVING PARTS DONE')
