"""Put the two rounds' motion on the bolt's own rig (2026-10-30).

Why: the first visible-rounds build gave each round an animated component of
its own (the Ashura's 3-bone cartridge rig, its own clip set). In game
(2026-10-30 probe run, HANDOFF.md "Visible rounds") the bolt played our clip
exactly, but the round components did not: round A and round B read the same
pose every frame, matching none of our clips, and the rounds never showed.
The bolt's rig is the one path proven to play our data, and it has three cable
bones Dioscuri's body does not use and that every clip, vanilla and ours,
holds still at their bind pose:
  l_cable_front_01  -> round A (the first round loaded)
  l_cable_middle_01 -> round B
So each round mesh is skinned to its cable bone (finish_rounds.py) and this
script keys the rounds' authored poses (build_rounds.py, rounds.json) onto
those bones in the bolt's three empty_reload clips.

The math. A round mesh rests in the chamber when its bone is at its bind pose
C_rest (the mesh's vertices sit there in the gun frame). For the round to sit
at its authored pose M(t) (centre, axis +Y; M_rest = the chamber), the bone
must carry the same rigid motion:  C(t) = M(t) @ M_rest^-1 @ C_rest.
The bolt rig's armature sits at the gun origin (build_rounds.py reads the bolt
there), so the gun frame is Blender's world frame here.

In:  ashura-reload/work/two_round/base1.glb (build_two_round_reload.py: the
     bolt's three rebuilt clips), ashura-reload/work/rounds/rounds.json.
Out: ashura-reload/work/two_round/base1_rounds.glb, the same three clips with
     the two cable bones keyed every frame; finish_two_round_reload.py imports
     it into dioscuri_base1.anims.

Gates: every other channel unchanged; the rig as Blender evaluates it puts
each cable bone exactly at C(t); the written GLB as build_two_round_reload.py
gates it (extras, LINEAR, rot+trans on every joint, no scale, 180 frames).
The CLAUDE.md rules for per-frame authoring: every frame is computed from the
pristine action before anything is keyed, quaternion signs kept continuous.

Run: & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python key_round_bones.py
"""
import bpy, json, math, os, struct
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, 'ashura-reload')
TR = os.path.join(R, 'work', 'two_round')
IN_GLB = os.path.join(TR, 'base1.glb')
OUT_GLB = os.path.join(TR, 'base1_rounds.glb')
ROUNDS = os.path.join(R, 'work', 'rounds', 'rounds.json')
CLIPS = ['empty_reload', 'empty_reload_01', 'empty_reload_02']
BONE = {'A': 'l_cable_front_01', 'B': 'l_cable_middle_01'}
NF = 180

rj = json.load(open(ROUNDS))
CHAMBER = Vector(rj['chamber'])
M_REST_INV = Matrix.Translation(CHAMBER).inverted()


def mat(rows):
    return Matrix([list(r) for r in rows])


def fcurves_of(action):
    return [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]


def play(rig, action):
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    rig.animation_data_create()
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]


bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
# the importer turns GLB seconds into frames at the scene rate: at Blender's
# default 24 fps the 180-frame clips came in 144 frames long (caught by the
# per-sampler end-time gate below, 2026-10-30)
sc.render.fps, sc.render.fps_base = 30, 1.0
before = set(bpy.data.objects)
bpy.ops.io_scene_gltf.cp77(filepath=IN_GLB, scripting=True)
arm = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
for o in [o for o in bpy.data.objects if o is not arm]:
    bpy.data.objects.remove(o, do_unlink=True)
W = arm.matrix_world.copy()
assert (W.translation.length < 1e-9), W
for b in BONE.values():
    assert arm.pose.bones[b].parent.name == 'barrel', b

for clip in CLIPS:
    a = bpy.data.actions[clip]
    play(arm, a)
    # pristine snapshot of every OTHER channel, for the unchanged gate
    others = {(fc.data_path, fc.array_index): [fc.evaluate(f) for f in range(NF)]
              for fc in fcurves_of(a) if not any('"%s"' % b in fc.data_path for b in BONE.values())}
    # 1. every frame from the pristine clip. C_rest: the pose the clip holds
    # each cable at (its bind pose: what the round mesh's inverse bind
    # assumes), checked against Blender's rest and held on every frame
    sc.frame_set(0)
    bpy.context.view_layer.update()
    rest = {}
    for rnd, b in BONE.items():
        rest[rnd] = (W @ arm.pose.bones[b].matrix).copy()
        bind = W @ arm.data.bones[b].matrix_local
        off = (rest[rnd].translation - bind.translation).length
        print('REST %-16s %-18s clip vs bind %.7f m' % (clip, b, off))
        assert off < 1e-4, (clip, b, off)
    bases, targets = {r: [] for r in BONE}, {r: [] for r in BONE}
    for f in range(NF):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        for rnd, b in BONE.items():
            pb = arm.pose.bones[b]
            assert ((W @ pb.matrix).translation - rest[rnd].translation).length < 1e-4, '%s f%d: %s moves' % (clip, f, b)
            want = mat(rj['pose'][clip][rnd][f]) @ M_REST_INV @ rest[rnd]
            targets[rnd].append(want)
            bases[rnd].append(arm.convert_space(pose_bone=pb, matrix=W.inverted() @ want,
                                                from_space='POSE', to_space='LOCAL').copy())
    # 2. key them (replace the cable channels' keys)
    for rnd, b in BONE.items():
        qs = []
        for m in bases[rnd]:
            q = m.to_quaternion()
            if qs and qs[-1].dot(q) < 0:
                q.negate()
            qs.append(q)
        vals = {('location', i): [m.translation[i] for m in bases[rnd]] for i in range(3)}
        vals.update({('rotation_quaternion', i): [q[i] for q in qs] for i in range(4)})
        done = set()
        for fc in fcurves_of(a):
            for (prop, i), series in vals.items():
                if fc.data_path == 'pose.bones["%s"].%s' % (b, prop) and fc.array_index == i:
                    kp = fc.keyframe_points
                    kp.clear()
                    kp.add(NF)
                    co = [0.0] * (2 * NF)
                    for g, v in enumerate(series):
                        co[2 * g], co[2 * g + 1] = float(g), v
                    kp.foreach_set('co', co)
                    for k in kp:
                        k.interpolation = 'LINEAR'
                    fc.update()
                    done.add((prop, i))
        assert done == set(vals), '%s %s: channels missing %s' % (clip, b, set(vals) - done)
    # 3. gates: the rig reproduces the targets; nothing else moved
    play(arm, a)
    worst_p, worst_r = 0.0, 0.0
    for f in range(NF):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        for rnd, b in BONE.items():
            got = W @ arm.pose.bones[b].matrix
            want = targets[rnd][f]
            worst_p = max(worst_p, (got.translation - want.translation).length)
            worst_r = max(worst_r, math.degrees(got.to_quaternion().rotation_difference(want.to_quaternion()).angle))
    assert worst_p < 1e-5 and worst_r < 0.05, '%s: evaluated cable pose off by %.6f m / %.3f deg' % (clip, worst_p, worst_r)
    after = {(fc.data_path, fc.array_index): [fc.evaluate(f) for f in range(NF)]
             for fc in fcurves_of(a) if not any('"%s"' % b in fc.data_path for b in BONE.values())}
    assert after.keys() == others.keys() and all(
        max(abs(x - y) for x, y in zip(after[k], others[k])) < 1e-9 for k in others), '%s: another channel changed' % clip
    # the same extras build_two_round_reload.py sets (the importer reads them)
    a['numExtraJoints'] = 0
    a['rootMotionType'] = 'Unknown'
    hints = dict(a.get('optimizationHints', {}))
    hints['preferSIMD'] = False
    a['optimizationHints'] = hints
    a.use_fake_user = True
    centre_rest = {rnd: (targets[rnd][0] @ rest[rnd].inverted() @ Matrix.Translation(CHAMBER)).translation for rnd in BONE}
    print('KEYED %-16s cables match the authored poses to %.7f m / %.4f deg; frame 0 round centres %s' % (
        clip, worst_p, worst_r, {r: tuple(round(x, 4) for x in v) for r, v in centre_rest.items()}))

play(arm, bpy.data.actions['empty_reload'])
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.cp77_glb(filepath=OUT_GLB, export_poses=True, export_tracks=False)

# gate the written GLB (build_two_round_reload.py's checks)
b_ = open(OUT_GLB, 'rb').read()
j = json.loads(b_[20:20 + struct.unpack_from('<I', b_, 12)[0]])
nodes = j['nodes']
joints = set()
for s in j.get('skins', []):
    joints.update(s['joints'])
if not joints:
    joints = {i for i, nd in enumerate(nodes) if 'mesh' not in nd}
problems = []
anims = j.get('animations', [])
if sorted(x['name'] for x in anims) != sorted(CLIPS):
    problems.append('animations %s' % sorted(x['name'] for x in anims))
for x in anims:
    ex = x.get('extras', {})
    if ex.get('numExtraJoints') != 0 or ex.get('rootMotionType') != 'Unknown' or (ex.get('optimizationHints') or {}).get('preferSIMD') is not False:
        problems.append('%s extras %s' % (x['name'], {k: ex.get(k) for k in ('numExtraJoints', 'rootMotionType', 'optimizationHints')}))
    tg = {}
    for ch in x['channels']:
        tg.setdefault(ch['target'].get('node'), set()).add(ch['target']['path'])
    keyed = {nd for nd, p in tg.items() if 'rotation' in p and 'translation' in p}
    if joints - keyed:
        problems.append('%s: %d joints without rot+trans' % (x['name'], len(joints - keyed)))
    if any('scale' in p for p in tg.values()):
        problems.append('%s: scale channels' % x['name'])
    interp = {s.get('interpolation') for s in x['samplers']} - {'LINEAR', 'STEP', None}
    if interp:
        problems.append('%s: interpolation %s' % (x['name'], sorted(interp)))
    ends = [j['accessors'][s['input']]['max'][0] for s in x['samplers']]
    tmax = max(ends)
    # EVERY sampler, not the longest: a 24 fps import shortened only the
    # channels this script did not rewrite
    if max(abs(t - (NF - 1) / 30.0) for t in ends) > 1e-3:
        problems.append('%s: samplers end at %.3f..%.3f s' % (x['name'], min(ends), tmax))
    print('  GLB %-16s channels %4d  joints keyed %d/%d  ends %.3f s' % (x['name'], len(x['channels']), len(keyed), len(joints), tmax))
if problems:
    raise SystemExit('GLB GATE FAILED:\n  ' + '\n  '.join(problems))
print('EXPORTED', OUT_GLB, len(b_) // 1024, 'KB')
print('KEY ROUND BONES DONE')
