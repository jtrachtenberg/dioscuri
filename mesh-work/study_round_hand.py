"""Where does V's hand hold a round, and where does it put it? (2026-10-28)

Study for visible rounds in the two-round reload. Loads what the game plays:
V's arm clips and the bolt clips as decoded from the STAGED .anims
(ashura-reload/work/two_round/decoded/) and Dioscuri's skinned body (the
verify uncook). The gun follows V's hands the way the engine places it: gun
space (`arm_right_ik_weapon`) with the -90 deg X attach correction
(CLAUDE.md, "The weapon attachment is ...").

V's hands are drawn as joint chains, rebuilt every frame from the bone heads
(the shipped FPP arm meshes are skinned to the full body rig and shred on
the animation rig: Meigetsu's add_hand_proxy.py). Fingertips are not joints
on this rig, so each tip is the last joint carried on along its bone.

Prints, per variant and every 6 frames, each hand's pinch point (between the
thumb and index tips) in the WEAPON frame (the frame a weapon component's clip
is authored in) and how far WeaponRight is from gun space. Writes every frame
to preview/round_study/fingers_gun_frame.json.
Renders (ashura-reload/preview/round_study/): the FPP camera view, a close
view from behind-left, and a top view of the breech.

Run: & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python study_round_hand.py [-- --ashura]
--ashura: the vanilla Ashura the same way (its own arm clips; its receiver, bolt
and cartridge, the cartridge in red), to see where CDPR's round goes. Output:
preview/round_study_ashura/.
"""
import bpy, bmesh, os, sys, math, json
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, 'ashura-reload')
TR = os.path.join(R, 'work', 'two_round')
ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ASHURA = '--ashura' in ARGV   # the vanilla Ashura instead: its own arm clips, all three gun parts


def opt(name, default=None):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default


# --rounds X,Y,Z[;X,Y,Z...]: test cartridges fixed in the gun frame (red), to try
# a chamber spot; --frames / --clips limit the renders; --views picks views
ROUNDS = [Vector(map(float, r.split(','))) for r in opt('--rounds', '').split(';') if r]
# --authored: the two rounds as build_rounds.py authored them (work/rounds/rounds.json), per frame
AUTHORED = None
if '--authored' in ARGV:
    AUTHORED = json.load(open(os.path.join(TR, '..', 'rounds', 'rounds.json')))['pose']
    ROUNDS = [Vector((0, 0, 0)), Vector((0, 0, 0))]
U = os.path.join(R, 'uncooked', 'base')
VAN = os.path.join(U, 'animations', 'weapon', 'firearms', 'rifle_sniper')
ASH = os.path.join(U, 'weapons', 'firearms', 'rifle_sniper', 'tsunami_ashura', 'entities', 'meshes')
if ASHURA:
    ARMS = os.path.join(VAN, 'tsunami_ashura', 'pwa_w_rifle_sniper__tsunami_ashura.anims.glb')
    PARTS = [  # (anim set, meshes): as the Ashura's .app has them, all at the weapon origin
        (os.path.join(VAN, 'tsunami_ashura', 'w_rifle_sniper__tsunami_ashura__base1.anims.glb'),
         [os.path.join(ASH, 'w_rifle_sniper__tsunami_ashura__base1_01.glb')]),
        (os.path.join(VAN, 'tsunami_ashura', 'w_rifle_sniper__tsunami_ashura__mag_std.anims.glb'),
         [os.path.join(ASH, 'w_rifle_sniper__tsunami_ashura__mag_std_01.glb')]),
        (os.path.join(VAN, 'w_rifle_sniper__rcv1.anims.glb'),
         [os.path.join(U, 'weapons', 'firearms', 'rifle_sniper', 'tsunami_nekomata', 'entities', 'meshes',
                       'w_rifle_sniper__tsunami_nekomata__rcv1_01.glb')]),
    ]
    OUT = os.path.join(R, 'preview', 'round_study_ashura')
    NF = 126
    FRAMES = [0, 27, 41, 48, 52, 58, 64, 70, 75, 81, 90, 100]
else:
    ARMS = os.path.join(TR, 'decoded', 'pwa_dioscuri.anims.glb')
    PARTS = [(os.path.join(TR, 'decoded', 'dioscuri_base1.anims.glb'),
              [os.path.join(R, 'work', 'verify', 'uncook', 'mod', 'dioscuri', 'meshes', 'dioscuri_body_verify.glb')])]
    OUT = os.path.join(R, 'preview', 'round_study')
# --final: the rounds as the game gets them: the staged clip sets decoded
# (work/rounds/decoded/) and the built round mesh packed and uncooked back
# (finish_rounds.py), each on its own cartridge rig, as dioscuri_weapon.app has them
FINAL = '--final' in ARGV and not ASHURA
if FINAL:
    RW = os.path.join(R, 'work', 'rounds')
    RMESH = os.path.join(RW, 'verify', 'uncook', 'mod', 'dioscuri', 'meshes', 'dioscuri_round_verify.glb')
    PARTS += [(os.path.join(RW, 'decoded', 'dioscuri_round_%s.anims.glb' % r), [RMESH]) for r in 'ab']
    OUT += '_final'
    NF = 180
    FRAMES = [0, 27, 41, 48, 52, 58, 64, 75, 81, 95, 106, 118, 135, 150]
CLIPS = ['empty_reload', 'empty_reload_01', 'empty_reload_02']
FRAMES = [int(f) for f in opt('--frames', ','.join(map(str, FRAMES))).split(',')]
CLIPS = opt('--clips', ','.join(CLIPS)).split(',')
VIEWS = opt('--views', 'fpp,close,top,eye').split(',')
CARTRIDGE = os.path.join(ASH, 'w_rifle_sniper__tsunami_ashura__mag_std_01.glb')  # 7.5 cm, along +Y from y 0.002
if AUTHORED:
    OUT += '_authored'
elif ROUNDS:
    OUT += '_chamber'
ATTACH = Matrix.Rotation(math.radians(-90), 4, 'X')
DIGITS = {'Thumb': 2, 'Index': 3, 'Middle': 3, 'Ring': 3, 'Pinky': 3}

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene


def imp(path, addon=True, **kw):
    assert os.path.exists(path), path
    before, acts = set(bpy.data.objects), set(bpy.data.actions)
    if addon:
        bpy.ops.io_scene_gltf.cp77(filepath=path, scripting=True, **kw)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.name.startswith('Icosphere')]:
        new.remove(o)
        bpy.data.objects.remove(o, do_unlink=True)
    return new, {a.name.split('.')[0]: a for a in bpy.data.actions if a not in acts}


new, arm_acts = imp(ARMS, import_tracks=True)
arms = [o for o in new if o.type == 'ARMATURE'][0]
arms.name = 'V'

# the gun: each part's rig (with its clips) under an empty that follows gun space
gun = bpy.data.objects.new('GUN', None)
sc.collection.objects.link(gun)
rigs, body = [], []
for anims, meshes in PARTS:
    new, acts = imp(anims)
    rig = [o for o in new if o.type == 'ARMATURE'][0]
    rig.parent = gun
    rigs.append((rig, acts))
    for mp in meshes:
        new, _ = imp(mp, addon=False)   # stock importer: the addon dies on the cartridge's material
        for o in new:
            if o.type != 'MESH':
                continue
            for m in [m for m in o.modifiers if m.type == 'ARMATURE']:
                o.modifiers.remove(m)
            o.modifiers.new('Armature', 'ARMATURE').object = rig
            o.parent = rig
            o.matrix_parent_inverse = Matrix.Identity(4)
            o.hide_render = 'LOD_' in o.name and 'LOD_1' not in o.name
            body.append(o)
        for o in new:
            if o.type != 'MESH':
                bpy.data.objects.remove(o, do_unlink=True)
bolt = rigs[0][0]
test_rounds = []
for k, at in enumerate(ROUNDS):
    new, _ = imp(CARTRIDGE, addon=False)
    for o in new:
        if o.type != 'MESH' or ('LOD_' in o.name and 'LOD_1' not in o.name):
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        o.modifiers.clear()
        o.parent = gun
        # centre the 7.5 cm round on the requested point (its mesh runs y 0.002..0.077)
        o.matrix_parent_inverse = Matrix.Identity(4)
        o.matrix_basis = Matrix.Translation(at - Vector((0, 0.0395, 0)))
        test_rounds.append(o)


def play(rig, action):
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    rig.animation_data_create()
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]


def world(rig, bone):
    return (rig.matrix_world @ rig.pose.bones[bone].matrix).copy()


def head(bone):
    return world(arms, bone).translation


def chains(side):
    """The hand's joint chains, wrist first, each ending in its estimated tip."""
    out = [[head(side + 'ForeArm'), head(side + 'Hand')]]
    for d, n in DIGITS.items():
        pts = [head(side + 'Hand')] + [head('%sHand%s%d' % (side, d, k)) for k in range(1, n + 1)]
        pts.append(pts[-1] + (pts[-1] - pts[-2]) * (0.9 if d == 'Thumb' else 0.75))
        out.append(pts)
    return out


def tips(side):
    c = {d: ch for d, ch in zip(['Arm'] + list(DIGITS), chains(side))}
    return c['Thumb'][-1], c['Index'][-1]


def goto(f):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    g = world(arms, 'arm_right_ik_weapon') @ ATTACH
    gun.matrix_world = g
    if AUTHORED:
        for rnd, o in zip('AB', test_rounds):
            # a round's pose is its centre and axis (+Y); the vanilla mesh runs y 0.002..0.077
            o.matrix_basis = Matrix(AUTHORED[CLIP][rnd][f]) @ Matrix.Translation((0, -0.0395, 0))
    bpy.context.view_layer.update()
    return g


# --- numbers --------------------------------------------------------------
report = {}
for clip in ([] if ROUNDS else CLIPS):   # a chamber test only renders
    CLIP = clip
    play(arms, arm_acts[clip])
    for rig, acts in rigs:
        if clip in acts:   # the Ashura's receiver set has no clips: it never moves
            play(rig, acts[clip])
    rows, worst = [], 0.0
    for f in range(0, NF):
        g = goto(f)
        w = world(arms, 'WeaponRight') @ ATTACH
        worst = max(worst, (g.translation - w.translation).length)
        gi = g.inverted()
        row = {'f': f, 'bolt': list(gi @ world(bolt, 'cocking_mechanism').translation)}
        if ASHURA:
            row['mag_std'] = list(gi @ world(rigs[1][0], 'mag_std').translation)
        for side in ('Left', 'Right'):
            t, i = tips(side)
            row[side] = {'thumb': list(gi @ t), 'index': list(gi @ i), 'hand': list(gi @ head(side + 'Hand'))}
        rows.append(row)
    report[clip] = rows
    print('%s: WeaponRight vs gun space, worst %.1f mm' % (clip, worst * 1000))
    for r in rows[::6]:
        s = '  f%03d' % r['f']
        for side in ('Left', 'Right'):
            t, i = Vector(r[side]['thumb']), Vector(r[side]['index'])
            p = (t + i) / 2
            s += '  %s pinch %+.3f %+.3f %+.3f (gap %.1f cm)' % (side[0], p.x, p.y, p.z, (t - i).length * 100)
        print(s + '  bolt y %+.3f' % r['bolt'][1] + ('  round %+.3f %+.3f %+.3f' % tuple(r['mag_std']) if ASHURA else ''))
os.makedirs(OUT, exist_ok=True)
if report:
    json.dump(report, open(os.path.join(OUT, 'fingers_gun_frame.json'), 'w'))

# --- the hands as geometry, rebuilt per frame ------------------------------
hands_me = bpy.data.meshes.new('HANDS')
hands = bpy.data.objects.new('HANDS', hands_me)
sc.collection.objects.link(hands)


def build_hands():
    bm = bmesh.new()
    for side in ('Left', 'Right'):
        for k, ch in enumerate(chains(side)):
            for a, b in zip(ch, ch[1:]):
                d = b - a
                if d.length < 1e-5:
                    continue
                r = 0.022 if k == 0 else 0.0065
                m = Matrix.Translation((a + b) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
                bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r * 0.9,
                                      depth=d.length, matrix=m)
            for p in ch[1:]:
                bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=0.008,
                                          matrix=Matrix.Translation(p))
    bm.to_mesh(hands_me)
    bm.free()
    hands_me.update()


# --- renders --------------------------------------------------------------
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'OBJECT'
sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 800, 450
for o in body:
    o.color = (0.55, 0.55, 0.6, 1)
if ASHURA:
    for o in rigs[1][0].children:
        o.color = (0.95, 0.2, 0.1, 1)   # the cartridge
for o in test_rounds:
    o.color = (0.95, 0.2, 0.1, 1)
if FINAL:
    for rig, _ in rigs[1:]:
        for o in rig.children:
            o.color = (0.95, 0.2, 0.1, 1)
    # gate: each decoded round against build_rounds.py's authored pose, every frame.
    # A round's pose M (centre, axis +Y) puts the vanilla geometry at M @ T(0,-0.0395,0);
    # the mesh rests at Q_REST, so M = mag_std(t) @ mag_std(rest)^-1 @ Q_REST @ T(0,0.0395,0)
    want = json.load(open(os.path.join(RW, 'rounds.json')))
    q_rest = Matrix.Translation(Vector(want['chamber']) - Vector((0, 0.0395, 0)))
    worst = {}
    gun.matrix_world = Matrix.Identity(4)   # measure in the gun frame itself
    bpy.context.view_layer.update()
    for clip in CLIPS:
        for (rig, acts), rnd in zip(rigs[1:], 'AB'):
            play(rig, acts[clip])
            rest = rig.matrix_world @ rig.data.bones['mag_std'].matrix_local
            for f in range(NF):
                sc.frame_set(f)
                bpy.context.view_layer.update()
                m = world(rig, 'mag_std') @ rest.inverted() @ q_rest @ Matrix.Translation((0, 0.0395, 0))
                a = Matrix(want['pose'][clip][rnd][f])
                dp = (m.translation - a.translation).length
                da = math.degrees(m.to_quaternion().rotation_difference(a.to_quaternion()).angle)
                k = (clip, rnd)
                worst[k] = (max(worst.get(k, (0, 0))[0], dp), max(worst.get(k, (0, 0))[1], da))
    for (clip, rnd), (dp, da) in sorted(worst.items()):
        print('DECODED round %s %-16s vs authored: worst %.2f mm, %.3f deg' % (rnd, clip, dp * 1000, da))
    assert all(dp < 0.001 and da < 0.5 for dp, da in worst.values()), 'DECODE GATE FAILED'
    print('DECODE GATE OK')
hands.color = (0.85, 0.55, 0.4, 1)


def camera(name, **kw):
    cd = bpy.data.cameras.new(name)
    cd.clip_start = 0.01
    for k, v in kw.items():
        setattr(cd, k, v)
    ob = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(ob)
    return ob


fpp = camera('FPP', sensor_fit='HORIZONTAL', angle=math.radians(80))
close = camera('CLOSE', lens=35)


def look(cam, eye, tgt):
    cam.matrix_world = Matrix.Translation(eye) @ (tgt - eye).to_track_quat('-Z', 'Y').to_matrix().to_4x4()


for clip in CLIPS:
    CLIP = clip
    play(arms, arm_acts[clip])
    for rig, acts in rigs:
        if clip in acts:   # the Ashura's receiver set has no clips: it never moves
            play(rig, acts[clip])
    for f in FRAMES:
        g = goto(f)
        build_hands()
        views = {
            'fpp': lambda: fpp.__setattr__('matrix_world', world(arms, 'Torso_fppCamera_Aim_JNT')),
            # gun frame: +Y muzzle, +Z up (the bolt slides along -Y)
            'close': lambda: look(close, g @ Vector((-0.45, -0.45, 0.30)), g @ Vector((0, -0.05, 0.03))),
            # straight down on the breech, muzzle up the image
            'top': lambda: close.__setattr__('matrix_world', g @ Matrix.Translation((0, 0.02, 0.55))),
            # V's eye on the breech: the FPP camera's position, aimed at the bolt, zoomed in
            'eye': lambda: look(close, world(arms, 'Torso_fppCamera_Aim_JNT').translation, g @ Vector((0, 0.08, 0.06))),
            # the gun's left side, level, on the breech
            'side': lambda: look(close, g @ Vector((-0.6, 0.08, 0.06)), g @ Vector((0, 0.08, 0.06))),
        }
        for v, setup in [(v, views[v]) for v in VIEWS]:
            setup()
            sc.camera = fpp if v == 'fpp' else close
            close.data.lens = {'eye': 70, 'side': 85}.get(v, 35)
            sc.render.filepath = os.path.join(OUT, '%s_%s_%03d.png' % (clip, v, f))
            bpy.ops.render.render(write_still=True)
            assert os.path.exists(sc.render.filepath)
print('STUDY DONE', OUT)
