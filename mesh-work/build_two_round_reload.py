"""Author Dioscuri's two-round reload from the Ashura's own clips (2026-10-28).

The maintainer: "the dioscuri fires two - so it needs to put in two rounds",
reload about 3.0 s with the animation a bit quicker (1.3x). Plan and
measurements: HANDOFF.md "Two-round reload".

Each of the Ashura's three empty_reload variants is cut and replayed:
  frames [0..B], then (A..B] again, then (B..125]
  A = handle_pull + 7   (bolt fully back)
  B = handle_release - 4 (round in, hand still at the breech)
read per variant from the clips' own sound events, so the stretch "bolt back
-> fetch a round -> round in" plays twice before the bolt closes. 126 frames
become 126 + (B - A) = 180. The SAME time map goes on V's arms (pwa, pma) and
on the gun's bolt (base1), so they stay in step; the bolt is back for the
whole repeated stretch. At the seam (pose B -> pose A+1) every channel blends
over SEAM frames (smoothstep; quaternions slerp): measured, the gun moves
3-6 cm and 15-25 deg there.

Inputs: the vanilla sets' GLBs (ashura-reload/uncooked/..., WolvenKit uncook)
and their serialized JSON (the event frames). Imported with the CP77 addon
(never the stock importer: it drops the float tracks, CLAUDE.md).
Out: ashura-reload/work/two_round/<set>.glb holding ONLY the three rebuilt
clips (the importer rebuilds what the GLB holds and keeps every other clip of
the existing set verbatim), plus splice.json (A, B per variant) for
finish_two_round_reload.py.

Traps handled (CLAUDE.md / the addon's code):
- numExtraJoints must be the NUMBER 0, rootMotionType 'Unknown';
- LINEAR keys only (a CUBICSPLINE sampler makes the importer throw);
- the addon exporter converts float-track curves to trackKeys only when the
  curve names start with '["T'; V's tracks are named ('["cameraUpOffset"]'),
  so it would export the clip's ORIGINAL 126-frame trackKeys. Converted here
  with the addon's own export_anim_tracks() after the cut;
- scale curves: asserted 1.0 and dropped (the pipeline keys loc+rot only).

Run: & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python build_two_round_reload.py
"""
import bpy, json, math, os, struct, sys
from mathutils import Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, 'ashura-reload')
U = os.path.join(R, 'uncooked', 'base', 'animations', 'weapon', 'firearms', 'rifle_sniper', 'tsunami_ashura')
OUT = os.path.join(R, 'work', 'two_round')
SETS = [  # (name, vanilla set basename)
    ('pwa', 'pwa_w_rifle_sniper__tsunami_ashura'),
    ('pma', 'pma_w_rifle_sniper__tsunami_ashura'),
    ('base1', 'w_rifle_sniper__tsunami_ashura__base1'),
]
CLIPS = ['empty_reload', 'empty_reload_01', 'empty_reload_02']
FRAMES = 126
SEAM = 8

from i_scene_cp77_gltf.animtools.tracks import export_anim_tracks  # noqa: E402  (the addon is enabled)


def event_frames(set_base, clip, needle):
    a = json.load(open(os.path.join(U, set_base + '.anims.json'), encoding='utf-8'))['Data']['RootChunk']
    for e in a['animations']:
        d = e['Data']
        if d['animation']['Data']['name']['$value'] != clip:
            continue
        evs = (d.get('events') or {}).get('Data', {}).get('events', [])
        return [x['Data']['startFrame'] for x in evs if needle in json.dumps(x)]
    raise KeyError(clip)


# A and B from V's female arm clips (the male clips' events are frame-identical,
# checked 2026-10-28); one time map for every set
splice = {}
for clip in CLIPS:
    pull, rel = event_frames('pwa_w_rifle_sniper__tsunami_ashura', clip, 'handle_pull'), event_frames('pwa_w_rifle_sniper__tsunami_ashura', clip, 'handle_release')
    assert len(pull) == 1 and len(rel) == 1, (clip, pull, rel)
    assert (pull, rel) == (event_frames('pma_w_rifle_sniper__tsunami_ashura', clip, 'handle_pull'), event_frames('pma_w_rifle_sniper__tsunami_ashura', clip, 'handle_release')), clip
    A, B = pull[0] + 7, rel[0] - 4
    splice[clip] = {'A': A, 'B': B, 'frames': FRAMES + (B - A)}
print('SPLICE', splice)


def smooth(t):
    return t * t * (3 - 2 * t)


def time_map(g, A, B):
    """new frame g -> (source frame, seam weight or None)"""
    L = B - A
    if g <= B:
        return g, None
    if g <= B + L:
        k = g - B
        return A + k, (smooth(k / SEAM) if k < SEAM else None)
    return g - L, None


def fcurves_of(action):
    fcs = []
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                fcs.extend(cb.fcurves)
    return fcs


def rebuild(action, A, B):
    n = FRAMES + (B - A)
    fcs = fcurves_of(action)
    src = {(fc.data_path, fc.array_index): [fc.evaluate(i) for i in range(FRAMES)] for fc in fcs}
    out = {}
    # rotations: per bone, slerp at the seam and keep the sign continuous
    rot_paths = sorted({p for (p, i) in src if p.endswith('rotation_quaternion')})
    for p in rot_paths:
        q_src = [Quaternion([src[(p, i)][f] for i in range(4)]) for f in range(FRAMES)]
        seq = []
        for g in range(n):
            f, w = time_map(g, A, B)
            q = q_src[f].copy()
            if w is not None:
                qb = q_src[B].copy()
                if qb.dot(q) < 0:
                    q.negate()
                q = qb.slerp(q, w)
            if seq and seq[-1].dot(q) < 0:
                q.negate()
            seq.append(q)
        for i in range(4):
            out[(p, i)] = [q[i] for q in seq]
    # everything else (locations, float tracks): lerp at the seam
    for (p, i), vals in src.items():
        if p.endswith('rotation_quaternion') or p.endswith('.scale'):
            continue
        seq = []
        for g in range(n):
            f, w = time_map(g, A, B)
            v = vals[f]
            if w is not None:
                v = vals[B] + (v - vals[B]) * w
            seq.append(v)
        out[(p, i)] = seq
    # scale: must be 1 throughout; dropped
    worst = max((abs(v - 1.0) for (p, i), vals in src.items() if p.endswith('.scale') for v in vals), default=0.0)
    assert worst < 1e-3, '%s: a scale channel is not 1 (%.4f)' % (action.name, worst)
    for fc in list(fcs):
        key = (fc.data_path, fc.array_index)
        if key not in out:
            fc.id_data  # noqa
            for layer in action.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        if fc in list(cb.fcurves):
                            cb.fcurves.remove(fc)
            continue
        vals = out[key]
        kp = fc.keyframe_points
        kp.clear()
        kp.add(n)
        co = [0.0] * (2 * n)
        for g, v in enumerate(vals):
            co[2 * g], co[2 * g + 1] = float(g), v
        kp.foreach_set('co', co)
        for k in kp:
            k.interpolation = 'LINEAR'
        fc.update()
    # the gate: no frame-to-frame jump at the seam bigger than the clip already has
    def max_step(series_by_bone, frames):
        worst = 0.0
        for qs in series_by_bone:
            for g in frames:
                worst = max(worst, math.degrees(qs[g].rotation_difference(qs[g - 1]).angle))
        return worst
    new_q = [[Quaternion([out[(p, i)][g] for i in range(4)]) for g in range(n)] for p in rot_paths]
    old_q = [[Quaternion([src[(p, i)][f] for i in range(4)]) for f in range(FRAMES)] for p in rot_paths]
    seam = max_step(new_q, range(B + 1, B + SEAM + 2))
    clip_max = max_step(old_q, range(1, FRAMES))
    return n, seam, clip_max


os.makedirs(OUT, exist_ok=True)
json.dump(splice, open(os.path.join(OUT, 'splice.json'), 'w'), indent=1)
for name, base in SETS:
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.io_scene_gltf.cp77(filepath=os.path.join(U, base + '.anims.glb'), scripting=True, import_tracks=True)
    arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    for a in list(bpy.data.actions):
        if a.name not in CLIPS:
            bpy.data.actions.remove(a)
    for clip in CLIPS:
        a = bpy.data.actions[clip]
        n, seam, clip_max = rebuild(a, splice[clip]['A'], splice[clip]['B'])
        print('REBUILT %-5s %-16s %d frames; biggest bone step at the seam %.1f deg/frame (the clip itself has up to %.1f)' % (name, clip, n, seam, clip_max))
        assert seam <= max(clip_max, 6.0) * 1.05, 'the seam jumps more than the clip ever moves'
        a['numExtraJoints'] = 0          # a NUMBER (a "0" string throws in WolvenKit's PutAnimations)
        a['rootMotionType'] = 'Unknown'
        if name == 'base1':
            # 2026-10-28, in game: re-encoded as the vanilla clips are (SIMD,
            # 16-bit quantized, 14 joints) the bolt clips hid the WHOLE gun
            # during the reload (every vertex hangs off base1), while V's arm
            # clips (SIMD, unquantized, 152 joints) played fine; the vanilla
            # bolt clips with the new arms kept the gun (A/B). WolvenKit's
            # decoder reads its own SIMD encode back fine, the game does not.
            # So the bolt goes in a Compressed buffer: the importer follows
            # this hint. Its rotation noise only touches channels that change,
            # and every base1 rotation is constant here (the bolt slides).
            hints = dict(a.get('optimizationHints', {}))
            hints['preferSIMD'] = False
            a['optimizationHints'] = hints
        a.use_fake_user = True
        arm.animation_data_create()
        arm.animation_data.action = a
        if len(a.slots):
            arm.animation_data.action_slot = a.slots[0]
        if name in ('pwa', 'pma'):
            export_anim_tracks(a, arm)   # the retimed float-track curves -> trackKeys
            tk = a.get('trackKeys', [])
            tmax = max((k['time'] for k in tk), default=0.0)
            print('        tracks: %d keyed, %d constant, last key %.3f s' % (len(tk), len(a.get('constTrackKeys', [])), tmax))
            assert not tk or abs(tmax - (n - 1) / 30.0) < 1e-3, 'track keys not retimed'
    for o in list(bpy.data.objects):
        if o is not arm:
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    out_glb = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.cp77_glb(filepath=out_glb, export_poses=True, export_tracks=False)

    # gate the written GLB (aeroboard export_stance.py's checks)
    b = open(out_glb, 'rb').read()
    j = json.loads(b[20:20 + struct.unpack_from('<I', b, 12)[0]])
    nodes = j['nodes']
    joints = set()
    for s in j.get('skins', []):
        joints.update(s['joints'])
    if not joints:
        joints = {i for i, nd in enumerate(nodes) if 'mesh' not in nd}
    problems = []
    anims = j.get('animations', [])
    if sorted(a['name'] for a in anims) != sorted(CLIPS):
        problems.append('animations %s' % sorted(a['name'] for a in anims))
    for a in anims:
        ex = a.get('extras', {})
        if ex.get('numExtraJoints') != 0 or ex.get('rootMotionType') != 'Unknown':
            problems.append('%s extras %s' % (a['name'], {k: ex.get(k) for k in ('numExtraJoints', 'rootMotionType')}))
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
        want = (splice[a['name']]['frames'] - 1) / 30.0
        if abs(tmax - want) > 1e-3:
            problems.append('%s: ends at %.3f s, want %.3f' % (a['name'], tmax, want))
        print('  GLB %-5s %-16s channels %4d  joints keyed %d/%d  ends %.3f s' % (name, a['name'], len(a['channels']), len(keyed), len(joints), tmax))
    if problems:
        raise SystemExit('GLB GATE FAILED (%s):\n  ' % name + '\n  '.join(problems))
    print('EXPORTED', out_glb, len(b) // 1024, 'KB')
print('BUILD TWO ROUND RELOAD DONE')
