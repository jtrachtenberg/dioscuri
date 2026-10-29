"""Visible rounds for the two-round reload (2026-10-28).

The maintainer, after the two-round reload was confirmed: "there are still no
bullet showing in the chamber". Each of Dioscuri's two rounds is the Ashura's
own cartridge (its vanilla mesh and its 3-bone `mag_std` rig) in a component
of its own, playing a clip set of its own (round A: the first round loaded,
round B: the second). This script authors those clips from the clips the game
plays (V's arms and the bolt as DECODED from the staged sets, ashura-reload/
work/two_round/decoded/), and the cartridge mesh moved to the chamber.

Where the rounds go (gun frame: +Y muzzle, +Z up; measured with
study_round_hand.py and a ray test of 200 directions, 2026-10-28):
- CHAMBER (0, 0.165, 0.072): hidden from every direction with the bolt open
  or closed. The mesh rests here, so whenever no clip plays (idle, firing,
  NPC sets) the rounds are out of sight. Both rounds rest at the same spot;
  they cannot be seen there, so the overlap does not show.
- the SLOTS, x -0.0075 (A) and +0.0075 (B), 10 cm behind the chamber (y
  0.065): the open channel on top of the receiver, in front of the open
  bolt's rear block. Seen from V's eye this is where the rounds read as
  loaded. Each slot rides the bolt (its transform relative to the fully open
  bolt), so as the bolt closes it carries both rounds forward into the
  chamber, 10 cm: the bolt's own travel.

Per variant and round, from the frames the game plays:
- the carrying hand: the left in empty_reload, the right in _01/_02 (the
  other hand holds the gun; asserted);
- insert end E: the frame near the round's "load" sound (the second "load"
  for round B) where V's pinch (thumb and index tips) is closest to the
  slot's rear end, the fingers holding the round by its base; insert start
  S = E - INSERT frames;
- the hold: at E the round lies along the gun's axis with its base in the
  pinch, fixed to the hand back to its appearance (CDPR's own cartridge sits
  in the hand only in the last ~8 frames before its insert, measured; it is
  parked far away the rest of the time);
- appearance P: the frame before S where the held round is furthest outside
  V's view (FPP camera, Torso_fppCamera_Aim_JNT, 80 deg horizontal, 16:9),
  so the jump from the hidden chamber to the hand is not seen;
- poses: before P the chamber; P..S the hand; S..E still the hand, plus a
  smoothstep share of what is left between the held round and the slot at E
  (so the round never leaves the fingers early); after E the slot, riding
  the bolt.
first_equip holds the rest pose (the vanilla one moves the cartridge, which
with the moved mesh would fly it around).

Out (ashura-reload/work/rounds/):
- round_a.glb, round_b.glb: the cartridge rig with the four clips, for
  finish_rounds.py's headless import into copies of the vanilla set;
- dioscuri_round.glb: the cartridge mesh, rest in the chamber, skinned to
  mag_std (LOD 1, one UV map, tangents);
- rounds.json: per variant and round the phase frames and the authored pose
  of the round's centre every frame (preview/verify).

Gates: the hidden spots (ray test), the clip's last pose in the chamber, the
evaluated rig against the authored poses, the GLBs (as build_two_round_reload.py).
Reports: the gap the insert closes, how far outside the view each round
appears, and how far male V's hand (pma) is from the round female V's
(pwa) clip carries.

Run: & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python build_rounds.py
"""
import bpy, json, math, os, struct
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, 'ashura-reload')
TR = os.path.join(R, 'work', 'two_round')
OUT = os.path.join(R, 'work', 'rounds')
U = os.path.join(R, 'uncooked', 'base')
VAN = os.path.join(U, 'animations', 'weapon', 'firearms', 'rifle_sniper', 'tsunami_ashura')
MAG_ANIMS = os.path.join(VAN, 'w_rifle_sniper__tsunami_ashura__mag_std.anims.glb')
MAG_MESH = os.path.join(U, 'weapons', 'firearms', 'rifle_sniper', 'tsunami_ashura', 'entities', 'meshes',
                        'w_rifle_sniper__tsunami_ashura__mag_std_01.glb')
ARMS = {'pwa': os.path.join(TR, 'decoded', 'pwa_dioscuri.anims.glb'),
        'pma': os.path.join(TR, 'decoded', 'pma_dioscuri.anims.glb')}
BOLT = os.path.join(TR, 'decoded', 'dioscuri_base1.anims.glb')
BODY = os.path.join(R, 'work', 'verify', 'uncook', 'mod', 'dioscuri', 'meshes', 'dioscuri_body_verify.glb')
EVENTS = os.path.join(TR, 'import', 'pwa_dioscuri', 'pwa_dioscuri.anims.json')   # the patched sound events

CLIPS = ['empty_reload', 'empty_reload_01', 'empty_reload_02']
CARRIER = {'empty_reload': 'Left', 'empty_reload_01': 'Right', 'empty_reload_02': 'Right'}
NF = 180
ATTACH = Matrix.Rotation(math.radians(-90), 4, 'X')   # CLAUDE.md: weapon = gun space @ Rot(-90, X)
CHAMBER = Vector((0.0, 0.165, 0.072))
SLOT_X = {'A': -0.0075, 'B': 0.0075}
SLOT_OPEN_Y = 0.065            # the chamber minus the bolt's 10 cm travel (gated below)
HALF = 0.0375                  # half the 7.5 cm round
VAN_CENTRE = 0.0395            # the vanilla mesh runs y 0.002..0.077 at x = z = 0
INSERT = 6                     # frames from the hand to the slot
FOV_H = math.radians(80)
ASPECT = 16 / 9
DIGITS = {'Thumb': 2, 'Index': 3}

os.makedirs(OUT, exist_ok=True)


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


def play(rig, action):
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    rig.animation_data_create()
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]


def world(rig, bone):
    return (rig.matrix_world @ rig.pose.bones[bone].matrix).copy()


def at(p, q=None):
    m = (q or Quaternion()).to_matrix().to_4x4()
    m.translation = p
    return m


def smooth(t):
    return t * t * (3 - 2 * t)


def blend(m0, m1, w):
    q0, q1 = m0.to_quaternion(), m1.to_quaternion()
    if q0.dot(q1) < 0:
        q1.negate()
    return at(m0.translation.lerp(m1.translation, w), q0.slerp(q1, w))


# ---------------------------------------------------------------- what the game plays
bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
rigs = {}
for k, p in ARMS.items():
    new, acts = imp(p, import_tracks=True)
    rigs[k] = ([o for o in new if o.type == 'ARMATURE'][0], acts)
new, bolt_acts = imp(BOLT)
bolt = [o for o in new if o.type == 'ARMATURE'][0]
new, _ = imp(BODY, addon=False)
body = [o for o in new if o.type == 'MESH']
for o in body:
    for m in [m for m in o.modifiers if m.type == 'ARMATURE']:
        o.modifiers.remove(m)
    o.modifiers.new('Armature', 'ARMATURE').object = bolt
    o.parent = bolt
    o.matrix_parent_inverse = Matrix.Identity(4)
for o in new:
    if o.type != 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)

loads = {}
for e in json.load(open(EVENTS, encoding='utf-8'))['Data']['RootChunk']['animations']:
    d = e['Data']
    name = d['animation']['Data']['name']['$value']
    if name in CLIPS:
        evs = (d.get('events') or {}).get('Data', {}).get('events', [])
        loads[name] = sorted(x['Data']['startFrame'] for x in evs if x['Data']['eventName']['$value'].endswith('_load'))
        assert len(loads[name]) == 2, (name, loads[name])
print('LOAD EVENTS', loads)


def sample(clip):
    """Every frame in the GUN frame: both hands, the pinches, the camera, the bolt."""
    rows = {k: [] for k in rigs}
    for k, (arm, acts) in rigs.items():
        play(arm, acts[clip])
    play(bolt, bolt_acts[clip])
    for f in range(NF):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        for k, (arm, _) in rigs.items():
            gi = (world(arm, 'arm_right_ik_weapon') @ ATTACH).inverted()
            row = {'cam': gi @ world(arm, 'Torso_fppCamera_Aim_JNT')}
            for side in ('Left', 'Right'):
                row[side] = gi @ world(arm, side + 'Hand')
                tips = []
                for d, n in DIGITS.items():
                    a = (gi @ world(arm, '%sHand%s%d' % (side, d, n - 1))).translation
                    b = (gi @ world(arm, '%sHand%s%d' % (side, d, n))).translation
                    tips.append(b + (b - a) * (0.9 if d == 'Thumb' else 0.75))   # tips are not joints: carry on the last bone
                row[side + 'Pinch'] = (tips[0] + tips[1]) / 2
            if k == 'pwa':
                row['bolt'] = world(bolt, 'cocking_mechanism')   # the bolt rig sits at the gun origin
            rows[k].append(row)
    return rows


def outside(cam, p):
    """How far p is outside V's view: > 0 outside (1 = one screen-half beyond the edge), inf behind."""
    c = cam.inverted() @ p
    if c.z >= -0.01:
        return float('inf')
    x = (c.x / -c.z) / math.tan(FOV_H / 2)
    y = (c.y / -c.z) / (math.tan(FOV_H / 2) / ASPECT)
    return max(abs(x), abs(y)) - 1


plan, poses = {}, {}
for clip in CLIPS:
    S_ = sample(clip)
    rows, male = S_['pwa'], S_['pma']
    side = CARRIER[clip]
    other = 'Right' if side == 'Left' else 'Left'
    by = [r['bolt'].translation.y for r in rows]
    open_ref = min(range(NF), key=lambda f: by[f])
    travel = max(by) - min(by)
    assert abs(travel - (CHAMBER.y - SLOT_OPEN_Y)) < 0.002, 'bolt travel %.4f' % travel
    bolt_open = rows[open_ref]['bolt'].inverted()
    plan[clip], poses[clip] = {}, {}
    for k, rnd in enumerate('AB'):
        load = loads[clip][k]
        slot_open = at(Vector((SLOT_X[rnd], SLOT_OPEN_Y, CHAMBER.z)))
        slot = [rows[f]['bolt'] @ bolt_open @ slot_open for f in range(NF)]
        rear = lambda f: slot[f].translation - Vector((0, HALF, 0))
        E = min(range(load - 6, load + 13), key=lambda f: (rows[f][side + 'Pinch'] - rear(f)).length)
        S = E - INSERT
        # the hold: at E the round lies along the gun's axis with its base in the
        # pinch; the insert then only adds what is left (FIX, in the round's own
        # frame), so the round travels WITH the hand and closes the last gap
        hold = rows[E][side].inverted() @ at(rows[E][side + 'Pinch'] + Vector((0, HALF, 0)))
        held = lambda f, r=rows: r[f][side] @ hold
        fix = held(E).inverted() @ slot[E]
        P = max(range(load - 34, S - 1), key=lambda f: outside(rows[f]['cam'], held(f).translation))
        out_by = outside(rows[P]['cam'], held(P).translation)
        # the other hand holds the gun meanwhile
        drift = max((rows[f][other].translation - rows[P][other].translation).length for f in range(P, E + 1))
        assert drift < 0.02, '%s %s: the %s hand moves %.3f m while the %s loads' % (clip, rnd, other, drift, side)
        seq = []
        for f in range(NF):
            if f < P:
                m = at(CHAMBER)
            elif f < S:
                m = held(f)
            elif f <= E:
                m = held(f) @ blend(Matrix.Identity(4), fix, smooth((f - S) / (E - S)))
            else:
                m = slot[f]
            seq.append(m)
        end = seq[-1].translation
        assert (end - Vector((SLOT_X[rnd], CHAMBER.y, CHAMBER.z))).length < 0.001, '%s %s ends at %s' % (clip, rnd, end)
        steps = [(seq[f].translation - seq[f - 1].translation).length for f in range(1, NF) if f != P]
        male_off = max(((male[f][side] @ hold).translation - held(f).translation).length for f in range(P, S + 1))
        plan[clip][rnd] = {'hand': side, 'load': load, 'appear': P, 'insert': [S, E], 'open_ref': open_ref,
                           'insert_gap_m': round(fix.translation.length, 4),
                           'appear_outside_view': round(out_by, 2), 'max_step_m': round(max(steps), 4),
                           'male_hand_off_m': round(male_off, 4)}
        poses[clip][rnd] = seq
        print('ROUND %-16s %s: %s hand, appears f%d (%.2f outside the view), carried to f%d, in the slot f%d (load f%d); '
              'the insert moves it %.1f cm; biggest step %.1f cm/frame; male V\'s hand up to %.1f cm off' % (
                  clip, rnd, side, P, out_by, S, E, load, plan[clip][rnd]['insert_gap_m'] * 100,
                  max(steps) * 100, male_off * 100))
        if out_by < 0.1:
            print('  WARNING: round %s of %s appears near or inside the view' % (rnd, clip))

# ---------------------------------------------------------------- gate: the hidden spots
SAMP = [Vector((0.0068 * math.cos(2 * math.pi * a / 8), -HALF + 2 * HALF * k / 8, 0.0068 * math.sin(2 * math.pi * a / 8)))
        for k in range(9) for a in range(8)]
DIRS = []
for i in range(200):
    z = 1 - 2 * (i + 0.5) / 200
    r = math.sqrt(1 - z * z)
    t = math.pi * (3 - math.sqrt(5)) * i
    DIRS.append(Vector((r * math.cos(t), r * math.sin(t), z)))


def seen_from(frame, m):
    sc.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in body:
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        base = len(verts)
        verts += [e.matrix_world @ v.co for v in me.vertices]
        polys += [[base + i for i in p.vertices] for p in me.polygons]
        e.to_mesh_clear()
    tr = BVHTree.FromPolygons(verts, polys)
    return sum(any(tr.ray_cast(m @ p + d, -d, 0.999)[0] is None for p in SAMP) for d in DIRS)


play(bolt, bolt_acts['empty_reload'])
open_f = plan['empty_reload']['A']['open_ref']
for label, m in (('rest', at(CHAMBER)), ('chamber A', at(Vector((SLOT_X['A'], CHAMBER.y, CHAMBER.z)))),
                 ('chamber B', at(Vector((SLOT_X['B'], CHAMBER.y, CHAMBER.z))))):
    for f in (0, open_f):
        n = seen_from(f, m)
        print('HIDDEN %-10s frame %3d (%s): seen from %d of 200 directions' % (label, f, 'closed' if f == 0 else 'open', n))
        assert n == 0, '%s is visible' % label
json.dump({'plan': plan, 'chamber': list(CHAMBER), 'slot_x': SLOT_X, 'slot_open_y': SLOT_OPEN_Y,
           'centre': {c: {r: [list(m.translation) for m in poses[c][r]] for r in 'AB'} for c in CLIPS},
           'pose': {c: {r: [[list(row) for row in m] for m in poses[c][r]] for r in 'AB'} for c in CLIPS}},
          open(os.path.join(OUT, 'rounds.json'), 'w'), indent=0)

# ---------------------------------------------------------------- the clips
# the mesh rests at Q_REST (the vanilla geometry moved to the chamber); a round
# at canonical pose M (centre, axis +Y) needs the vanilla geometry at
# Q = M @ T(0, -VAN_CENTRE, 0), so mag_std's armature-space pose is
# Q @ Q_REST^-1 @ rest, and with its parents at rest its basis is rest^-1 @ that.
Q_REST = at(CHAMBER - Vector((0, VAN_CENTRE, 0)))
TO_VAN = at(Vector((0, -VAN_CENTRE, 0)))


def fcurves_of(action):
    return [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]


def write(action, arm, bases, n):
    """Key every bone's location + rotation_quaternion on every frame, LINEAR; drop anything else."""
    cb = action.layers[0].strips[0].channelbag(action.slots[0], ensure=True)
    for fc in list(fcurves_of(action)):
        for layer in action.layers:
            for strip in layer.strips:
                for c in strip.channelbags:
                    if fc in list(c.fcurves):
                        c.fcurves.remove(fc)
    for b in arm.pose.bones:
        series = bases[b.name]
        qs = []
        for m in series:
            q = m.to_quaternion()
            if qs and qs[-1].dot(q) < 0:
                q.negate()
            qs.append(q)
        chans = [('location', i, [m.translation[i] for m in series]) for i in range(3)] + \
                [('rotation_quaternion', i, [q[i] for q in qs]) for i in range(4)]
        for prop, i, vals in chans:
            fc = cb.fcurves.new('pose.bones["%s"].%s' % (b.name, prop), index=i, group_name=b.name)
            kp = fc.keyframe_points
            kp.add(n)
            co = [0.0] * (2 * n)
            for g, v in enumerate(vals):
                co[2 * g], co[2 * g + 1] = float(g), v
            kp.foreach_set('co', co)
            for k in kp:
                k.interpolation = 'LINEAR'
            fc.update()


def gate_glb(path, want_frames):
    b = open(path, 'rb').read()
    j = json.loads(b[20:20 + struct.unpack_from('<I', b, 12)[0]])
    joints = set()
    for s in j.get('skins', []):
        joints.update(s['joints'])
    if not joints:
        joints = {i for i, nd in enumerate(j['nodes']) if 'mesh' not in nd and nd.get('name') != 'Armature'}
    problems = []
    anims = j.get('animations', [])
    if sorted(a['name'] for a in anims) != sorted(want_frames):
        problems.append('animations %s' % sorted(a['name'] for a in anims))
    for a in anims:
        ex = a.get('extras', {})
        if ex.get('numExtraJoints') != 0 or ex.get('rootMotionType') != 'Unknown' or (ex.get('optimizationHints') or {}).get('preferSIMD') is not False:
            problems.append('%s extras %s' % (a['name'], {k: ex.get(k) for k in ('numExtraJoints', 'rootMotionType', 'optimizationHints')}))
        tg = {}
        for ch in a['channels']:
            tg.setdefault(ch['target'].get('node'), set()).add(ch['target']['path'])
        keyed = {nd for nd, p in tg.items() if 'rotation' in p and 'translation' in p}
        if joints - keyed:
            problems.append('%s: %d joints without rot+trans' % (a['name'], len(joints - keyed)))
        if any('scale' in p for p in tg.values()):
            problems.append('%s: scale channels' % a['name'])
        interp = {s.get('interpolation') for s in a['samplers']} - {'LINEAR', 'STEP', None}
        if interp:
            problems.append('%s: interpolation %s' % (a['name'], sorted(interp)))
        tmax = max(j['accessors'][s['input']]['max'][0] for s in a['samplers'])
        if abs(tmax - (want_frames[a['name']] - 1) / 30.0) > 1e-3:
            problems.append('%s: ends at %.3f s' % (a['name'], tmax))
        print('  GLB %-16s channels %d  joints keyed %d/%d  ends %.3f s' % (a['name'], len(a['channels']), len(keyed), len(joints), tmax))
    if problems:
        raise SystemExit('GLB GATE FAILED (%s):\n  ' % path + '\n  '.join(problems))


for rnd in 'AB':
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    new, acts = imp(MAG_ANIMS, import_tracks=True)
    arm = [o for o in new if o.type == 'ARMATURE'][0]
    for o in new:
        if o is not arm:
            bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions):
        if a.name not in CLIPS + ['first_equip']:
            bpy.data.actions.remove(a)
    W_ = arm.matrix_world.copy()
    rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
    lengths = {'first_equip': int(round(bpy.data.actions['first_equip'].frame_range[1])) + 1}
    lengths.update({c: NF for c in CLIPS})
    for clip, n in lengths.items():
        target = [poses[clip][rnd][f] for f in range(n)] if clip in CLIPS else [at(CHAMBER)] * n
        mag = [W_.inverted() @ (M @ TO_VAN) @ Q_REST.inverted() @ W_ @ rest['mag_std'] for M in target]
        bases = {b: [Matrix.Identity(4)] * n for b in rest}
        bases['mag_std'] = [rest['mag_std'].inverted() @ m for m in mag]
        assert all(b.parent is None or b.parent.name in ('mag_plug', 'magazine') for b in arm.data.bones)
        a = bpy.data.actions[clip]
        write(a, arm, bases, n)
        a['numExtraJoints'] = 0          # a NUMBER (a "0" string throws in WolvenKit's PutAnimations)
        a['rootMotionType'] = 'Unknown'
        hints = dict(a.get('optimizationHints', {}))
        hints['preferSIMD'] = False      # Compressed, as the bolt (a SIMD re-encode hid the gun in game)
        a['optimizationHints'] = hints
        a.use_fake_user = True
        # gate: the rig as Blender evaluates it reproduces the authored poses
        play(arm, a)
        worst = 0.0
        for f in range(0, n, 3):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            got = W_ @ arm.pose.bones['mag_std'].matrix
            want = (target[f] @ TO_VAN) @ Q_REST.inverted() @ W_ @ rest['mag_std']
            worst = max(worst, (got.translation - want.translation).length)
            assert got.to_quaternion().rotation_difference(want.to_quaternion()).angle < math.radians(0.05), (clip, f)
        assert worst < 1e-5, '%s %s: evaluated pose off by %.6f m' % (rnd, clip, worst)
        print('KEYED round %s %-16s %d frames (evaluated vs authored %.6f m)' % (rnd, clip, n, worst))
    play(arm, bpy.data.actions['empty_reload'])
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    out_glb = os.path.join(OUT, 'round_%s.glb' % rnd.lower())
    bpy.ops.export_scene.cp77_glb(filepath=out_glb, export_poses=True, export_tracks=False)
    gate_glb(out_glb, lengths)
    print('EXPORTED', out_glb)

# ---------------------------------------------------------------- the mesh
bpy.ops.wm.read_homefile(use_empty=True)
new, _ = imp(MAG_MESH, addon=False)
meshes = [o for o in new if o.type == 'MESH']
assert len(meshes) == 1, [o.name for o in meshes]
mo = meshes[0]
assert mo.matrix_world == Matrix.Identity(4) or (mo.matrix_world.translation.length < 1e-9), mo.matrix_world
lo = Vector(map(min, *[v.co for v in mo.data.vertices]))
hi = Vector(map(max, *[v.co for v in mo.data.vertices]))
assert abs(lo.y - 0.0022) < 0.0005 and abs(hi.y - 0.0769) < 0.0005 and abs(lo.x + hi.x) < 0.0005, (lo, hi)
mo.data.transform(Q_REST)          # vertices in the gun frame: to the chamber
mo.name = mo.data.name = 'submesh_00_LOD_1'
while len(mo.data.uv_layers) > 1:
    mo.data.uv_layers.remove(mo.data.uv_layers[-1])
mo.data.uv_layers[0].name = 'UVMap'
groups = [g.name for g in mo.vertex_groups]
assert groups == ['mag_std'], groups
bpy.ops.object.select_all(action='DESELECT')
for o in new:
    o.select_set(True)
bpy.context.view_layer.objects.active = mo
out_mesh = os.path.join(OUT, 'dioscuri_round.glb')
bpy.ops.export_scene.gltf(filepath=out_mesh, use_selection=True, export_format='GLB',
                          export_materials='NONE', export_apply=False, export_skins=True,
                          export_animations=False, export_tangents=True)
lo2 = Vector(map(min, *[v.co for v in mo.data.vertices]))
print('MESH', out_mesh, 'rest bounds', tuple(round(x, 4) for x in lo2), '..',
      tuple(round(x, 4) for x in Vector(map(max, *[v.co for v in mo.data.vertices]))))
print('BUILD ROUNDS DONE')
