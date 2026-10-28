"""Build mesh-work\\ashura-reload\\ashura_reload_vs_dioscuri.blend (2026-10-28).

Why: a user reported Dioscuri has "no reload animation" on 2.5. V's hands do
reload (filmed, HANDOFF.md "Game 2.5"); what does not move is the GUN: the
vanilla Ashura's barrel, cocking mechanism, hammer, cables and magazine move
during its reload, Dioscuri's body is one static mesh. The maintainer wants the
Ashura's own gun animation next to Dioscuri in Blender to design moving parts.

What it builds:
- collection "Ashura (vanilla, animated)": the Ashura's three animated parts
  from its .app (w_rifle_sniper__tsunami_ashura.app, game 2.5), each mesh bound
  to its own rig and playing the gun's own clips:
    body      rig base1   (barrel, cocking_mechanism, hammer, cables, grips)
    magazine  rig mag_std (magazine, mag_std, mag_plug)
    receiver  rig rcv1    (the Nekomata receiver; its anim set has no clips)
  In the .app all three components sit at the same origin (Barrel and Magazine
  bind to their parent component with no slot), so they need no offsets here.
- collection "Dioscuri (shipped mesh)": dioscuri_body from the deployed
  Dioscuri.archive (1.1.0), at its in-game origin, i.e. where the Ashura's
  parts are drawn.
- text blocks README and set_clip.py (switches every part to one clip).

Inputs (gitignored, vanilla assets): mesh-work\\ashura-reload\\uncooked\\ from
WolvenKit CLI uncook (default mesh export: the GLBs carry skins with the real
bone names) and ashura-reload\\dioscuri\\ (uncook of the deployed archive).

Run:  & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python build_ashura_reload_blend.py
"""
import bpy, os, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, 'ashura-reload')
U = os.path.join(R, 'uncooked', 'base')
ANIM = os.path.join(U, 'animations', 'weapon', 'firearms', 'rifle_sniper')
MESH = os.path.join(U, 'weapons', 'firearms', 'rifle_sniper')
ASH = os.path.join(MESH, 'tsunami_ashura', 'entities', 'meshes')

PARTS = [
    ('body', os.path.join(ANIM, 'tsunami_ashura', 'w_rifle_sniper__tsunami_ashura__base1.anims.glb'),
     [os.path.join(ASH, 'w_rifle_sniper__tsunami_ashura__base1_01.glb'),
      os.path.join(ASH, 'w_rifle_sniper__tsunami_ashura__base1_02_diode_bottom.glb'),
      os.path.join(ASH, 'w_rifle_sniper__tsunami_ashura__base1_02_diode_top.glb')]),
    ('magazine', os.path.join(ANIM, 'tsunami_ashura', 'w_rifle_sniper__tsunami_ashura__mag_std.anims.glb'),
     [os.path.join(ASH, 'w_rifle_sniper__tsunami_ashura__mag_std_01.glb')]),
    ('receiver', os.path.join(ANIM, 'w_rifle_sniper__rcv1.anims.glb'),
     [os.path.join(MESH, 'tsunami_nekomata', 'entities', 'meshes', 'w_rifle_sniper__tsunami_nekomata__rcv1_01.glb')]),
]
DIOSCURI = os.path.join(R, 'dioscuri', 'mod', 'dioscuri', 'meshes', 'dioscuri_body.glb')
OUT = os.path.join(R, 'ashura_reload_vs_dioscuri.blend')
PREVIEW = os.path.join(R, 'preview')
CLIP = 'empty_reload'  # the Ashura reloads from empty (Dioscuri's burst empties it too)


PLAIN = []  # meshes that came in with plain materials


def cp77_import(path, mesh=False):
    """Import one GLB with the Cyberpunk addon (never the stock importer for
    .anims: it drops their extras, CLAUDE.md). For a MESH the stock importer is
    an acceptable fallback: the addon dies on a material whose .mlsetup the
    uncook did not export (the Ashura magazine), and geometry + skin are what
    this study needs."""
    assert os.path.exists(path), path
    before = set(bpy.data.objects)
    acts = set(bpy.data.actions)
    try:
        bpy.ops.io_scene_gltf.cp77(filepath=path, scripting=True, hide_armatures=False)
    except RuntimeError as e:
        if not mesh:
            raise
        for o in [o for o in bpy.data.objects if o not in before]:
            bpy.data.objects.remove(o, do_unlink=True)
        print('  (addon import failed: %s; stock glTF importer, plain materials)' % str(e).splitlines()[-1][:120])
        bpy.ops.import_scene.gltf(filepath=path)
        PLAIN.append(os.path.basename(path))
    new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.name.startswith('Icosphere')]:  # WolvenKit's junk sphere
        bpy.data.objects.remove(o, do_unlink=True)
        new.remove(o)
    return new, [a for a in bpy.data.actions if a not in acts]


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def move_to(objs, coll):
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)


def set_action(rig, action):
    rig.animation_data_create()
    rig.animation_data.action = action
    if action is not None and len(action.slots):
        rig.animation_data.action_slot = action.slots[0]


bpy.ops.wm.read_homefile(use_empty=True)  # not read_factory_settings: it unloads the addon
scene = bpy.context.scene
ash = collection('Ashura (vanilla, animated)')
dio = collection('Dioscuri (shipped mesh)')
rigs = {}

for part, anims, meshes in PARTS:
    new, acts = cp77_import(anims)
    rig = [o for o in new if o.type == 'ARMATURE'][0]
    rig.name = 'ASHURA_%s_rig' % part
    rig['ashura_part'] = part
    for a in acts:
        a.name = '%s.%s' % (part, a.name)
        a.use_fake_user = True
    move_to(new, ash)
    rigs[part] = rig
    print('PART %s: rig %s, %d bones, clips %s' % (part, rig.name, len(rig.data.bones), sorted(a.name for a in acts)))

    for mp in meshes:
        new, _ = cp77_import(mp, mesh=True)
        marm = [o for o in new if o.type == 'ARMATURE']
        mobs = [o for o in new if o.type == 'MESH']
        # Gate: the mesh's bind pose must be the anim rig's rest pose, bone by bone,
        # or rebinding moves the mesh (it would sit wrong before any clip plays).
        worst = 0.0
        for a in marm:
            for b in a.data.bones:
                rb = rig.data.bones.get(b.name)
                assert rb is not None, 'mesh bone %s missing from rig %s' % (b.name, rig.name)
                d = ((a.matrix_world @ b.matrix_local).translation - (rig.matrix_world @ rb.matrix_local).translation).length
                worst = max(worst, d)
        assert worst < 1e-4, '%s: bind pose differs from the rig rest by %.6f m' % (os.path.basename(mp), worst)
        for o in mobs:
            mods = [m for m in o.modifiers if m.type == 'ARMATURE']
            for m in mods:
                m.object = rig
            mw = o.matrix_world.copy()
            o.parent = rig
            o.matrix_world = mw
            o['ashura_part'] = part
            # LOD_1 is the in-game model; the lower LODs overlap it, keep them hidden
            if 'LOD_' in o.name and 'LOD_1' not in o.name:
                o.hide_viewport = True
                o.hide_render = True
        for a in marm:
            bpy.data.objects.remove(a, do_unlink=True)
        move_to(mobs, ash)
        print('  mesh %s: %d objects bound, bind pose matches rig to %.6f m' % (os.path.basename(mp), len(mobs), worst))

# Dioscuri as it ships
new, _ = cp77_import(DIOSCURI, mesh=True)
arms = [o for o in new if o.type == 'ARMATURE']
new = [o for o in new if o.type != 'ARMATURE']
for o in new:
    for m in [m for m in o.modifiers if m.type == 'ARMATURE']:
        o.modifiers.remove(m)  # Dioscuri is static: drop the skin's leftover modifier
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
for a in arms:
    bpy.data.objects.remove(a, do_unlink=True)
for o in new:
    o['dioscuri'] = True
    if 'LOD_' in o.name and 'LOD_1' not in o.name:
        o.hide_viewport = True
        o.hide_render = True
move_to(new, dio)
print('DIOSCURI: %d objects' % len(new))

# Every part plays the same clip, as the weapon.animgraph does
for part, rig in rigs.items():
    set_action(rig, bpy.data.actions.get('%s.%s' % (part, CLIP)))
act = bpy.data.actions['body.%s' % CLIP]
f0, f1 = (int(round(x)) for x in act.frame_range)
scene.frame_start, scene.frame_end = f0, f1
print('CLIP %s: frames %d-%d at %s fps (%.2f s)' % (CLIP, f0, f1, scene.render.fps, (f1 - f0) / scene.render.fps))

# Gate (CLAUDE.md, donor imports): every bone keeps unit scale, and the clip MOVES
moved = {}
for part, rig in rigs.items():
    if rig.animation_data.action is None:
        continue
    rest = {}
    for f in range(f0, f1 + 1, 2):
        scene.frame_set(f)
        for pb in rig.pose.bones:
            s = pb.matrix_basis.to_scale()
            assert max(abs(s.x - 1), abs(s.y - 1), abs(s.z - 1)) < 1e-3, '%s %s scale %s at %d' % (rig.name, pb.name, tuple(s), f)
            p = (rig.matrix_world @ pb.matrix).translation.copy()
            if pb.name not in rest:
                rest[pb.name] = p
            moved[(part, pb.name)] = max(moved.get((part, pb.name), 0.0), (p - rest[pb.name]).length)
for (part, bone), m in sorted(moved.items(), key=lambda kv: -kv[1])[:10]:
    print('  moves: %-9s %-20s %.1f mm' % (part, bone, m * 1000))
assert max(moved.values()) > 0.01, 'the clip does not move any bone by 1 cm'


def world_bounds(objs):
    lo = Vector((1e9, 1e9, 1e9)); hi = -lo
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type != 'MESH' or o.hide_render:
            continue
        e = o.evaluated_get(dg)
        for c in e.bound_box:
            w = e.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi


scene.frame_set(f0)
alo, ahi = world_bounds(ash.objects)
dlo, dhi = world_bounds(dio.objects)
print('BOUNDS ashura   min %s max %s' % (tuple(round(v, 3) for v in alo), tuple(round(v, 3) for v in ahi)))
print('BOUNDS dioscuri min %s max %s' % (tuple(round(v, 3) for v in dlo), tuple(round(v, 3) for v in dhi)))

# Text blocks for the maintainer
t = bpy.data.texts.new('README')
t.write(
    'Ashura reload vs Dioscuri (built by mesh-work\\build_ashura_reload_blend.py, 2026-10-28)\n\n'
    'Ashura (vanilla, animated): the gun\'s three animated parts, each a mesh on its own rig,\n'
    'as the game assembles them. Press Space (or scrub the timeline) to play the clip.\n'
    '  ASHURA_body_rig      barrel, cocking_mechanism, hammer, cables, grips\n'
    '  ASHURA_magazine_rig  magazine, mag_std, mag_plug\n'
    '  ASHURA_receiver_rig  no clips (the receiver never moves)\n'
    'Clips (actions, named <part>.<clip>): empty_reload, empty_reload_01, empty_reload_02, first_equip.\n'
    'empty_reload (126 frames, 30 fps): the magazine leaves the receiver by ~f9 (to ~0.6 m behind\n'
    'the gun, where V\'s hand holds it) and is back in by ~f81; the bolt (cocking_mechanism, with\n'
    'hammer and grips) slides 10 cm back between ~f18 and f27 and forward between ~f90 and f99.\n'
    'To switch every part at once: open set_clip.py in the Text Editor, edit CLIP, Run Script.\n\n'
    'Plain materials (the addon could not build theirs): %s\n\n'
    'Dioscuri (shipped mesh): dioscuri_body exactly as the 1.1.0 archive ships it, at the same\n'
    'origin the game draws the Ashura parts at. Hide either collection to compare.\n\n'
    'How a moving part would reach the game: Dioscuri\'s .app would need animated components\n'
    'like the Ashura\'s (a rig + weapon.animgraph + these .anims), and the moving pieces of\n'
    'Dioscuri\'s mesh skinned to the Ashura\'s bone names. Then the Ashura\'s own clips drive\n'
    'them, in step with V\'s hands, with no new animation authored.\n' % (', '.join(PLAIN) or 'none'))
t = bpy.data.texts.new('set_clip.py')
t.write(
    'import bpy\n'
    "CLIP = 'empty_reload'  # empty_reload, empty_reload_01, empty_reload_02, first_equip\n"
    'for ob in bpy.data.objects:\n'
    "    part = ob.get('ashura_part')\n"
    "    if ob.type == 'ARMATURE' and part:\n"
    "        a = bpy.data.actions.get(part + '.' + CLIP)\n"
    '        ob.animation_data_create()\n'
    '        ob.animation_data.action = a\n'
    '        if a is not None and len(a.slots):\n'
    '            ob.animation_data.action_slot = a.slots[0]\n'
    "a = bpy.data.actions.get('body.' + CLIP)\n"
    'if a is not None:\n'
    '    bpy.context.scene.frame_start, bpy.context.scene.frame_end = (int(round(x)) for x in a.frame_range)\n')

bpy.ops.wm.save_as_mainfile(filepath=OUT)
assert os.path.exists(OUT), OUT
print('SAVED', OUT)

# Preview strip: side view of the Ashura alone, then one frame with Dioscuri over it
os.makedirs(PREVIEW, exist_ok=True)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'OBJECT'
scene.render.resolution_x, scene.render.resolution_y = 960, 540
for o in ash.objects:
    o.color = {'body': (0.55, 0.55, 0.6, 1), 'magazine': (0.95, 0.55, 0.1, 1), 'receiver': (0.25, 0.45, 0.85, 1)}.get(o.get('ashura_part'), (1, 1, 1, 1))
for o in dio.objects:
    o.color = (0.85, 0.15, 0.15, 1)
# frame the whole clip: the magazine leaves the gun (into V's hand, ~0.6 m back)
lo = Vector(map(min, alo, dlo)); hi = Vector(map(max, ahi, dhi))
for f in range(f0, f1 + 1, 5):
    scene.frame_set(f)
    flo, fhi = world_bounds(ash.objects)
    lo = Vector(map(min, lo, flo)); hi = Vector(map(max, hi, fhi))
ctr = (lo + hi) / 2
size = hi - lo
cam_data = bpy.data.cameras.new('preview_cam')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = max(size.y, size.z * 16 / 9) * 1.25
cam = bpy.data.objects.new('preview_cam', cam_data)
scene.collection.objects.link(cam)
cam.location = ctr + Vector((3.0, 0, 0))
cam.rotation_euler = (math.pi / 2, 0, math.pi / 2)  # from +X, looking down -X: the gun's side
scene.camera = cam
dio.hide_render = True
frames = [f0 + round(i * (f1 - f0) / 7) for i in range(8)]
for f in frames:
    scene.frame_set(f)
    scene.render.filepath = os.path.join(PREVIEW, 'ashura_%s_%03d.png' % (CLIP, f))
    bpy.ops.render.render(write_still=True)
    assert os.path.exists(scene.render.filepath), scene.render.filepath
# close-up on the bolt (cocking_mechanism slides 10 cm back and forward)
body = rigs['body']
scene.frame_set(f0)
c0 = (body.matrix_world @ body.pose.bones['cocking_mechanism'].matrix).translation
cam_ortho, cam_loc = cam_data.ortho_scale, cam.location.copy()
cam_data.ortho_scale = 0.6
cam.location = Vector((3.0, c0.y - 0.05, c0.z))
for f in frames:
    scene.frame_set(f)
    scene.render.filepath = os.path.join(PREVIEW, 'bolt_%s_%03d.png' % (CLIP, f))
    bpy.ops.render.render(write_still=True)
    assert os.path.exists(scene.render.filepath), scene.render.filepath
cam_data.ortho_scale, cam.location = cam_ortho, cam_loc
dio.hide_render = False
scene.frame_set(f0)
scene.render.filepath = os.path.join(PREVIEW, 'overlay_dioscuri_red.png')
bpy.ops.render.render(write_still=True)
assert os.path.exists(scene.render.filepath)
print('PREVIEW frames', frames)
