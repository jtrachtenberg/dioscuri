"""Gate the two-round reload as the game will decode it (2026-10-28).

Compares, per clip and per joint, the motion in the GLB we authored
(ashura-reload/work/two_round/<set>.glb) with the GLB WolvenKit exports from
the STAGED .anims (ashura-reload/work/two_round/decoded/, `export -gp`).
A CLAUDE.md lesson: the anims encoder kept positions exact but bent rotations
1.3-3.3 deg on some bones, and only a decoded-vs-authored compare sees that.
Reports the worst rotation (deg) and translation (mm) difference per clip and
the bone it is on; fails above ROT_TOL / POS_TOL.

Run (after the decoded GLBs exist):  python mesh-work\\verify_two_round_reload.py
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# mesh-work holds a Blender script called inspect.py, which shadows the
# standard library's inspect (numpy imports it): drop this folder from the path
sys.path = [p for p in sys.path if os.path.abspath(p or '.') != HERE]
import numpy as np  # noqa: E402
TR = os.path.join(HERE, 'ashura-reload', 'work', 'two_round')
PAIRS = [('pwa.glb', 'decoded/pwa_dioscuri.anims.glb'), ('pma.glb', 'decoded/pma_dioscuri.anims.glb'),
         ('base1.glb', 'decoded/dioscuri_base1.anims.glb')]
CLIPS = ['empty_reload', 'empty_reload_01', 'empty_reload_02']
ROT_TOL, POS_TOL = 0.5, 0.001   # deg, m
CT = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5122: np.int16, 5120: np.int8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def load(path):
    b = open(path, 'rb').read()
    n = struct.unpack_from('<I', b, 12)[0]
    j = json.loads(b[20:20 + n])
    off = 20 + n
    bn = struct.unpack_from('<I', b, off)[0]
    bin_ = b[off + 8:off + 8 + bn]

    def acc(i):
        a = j['accessors'][i]
        bv = j['bufferViews'][a['bufferView']]
        start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        dt = np.dtype(CT[a['componentType']])
        cnt = a['count'] * NC[a['type']]
        arr = np.frombuffer(bin_, dtype=dt, count=cnt, offset=start).astype(np.float64)
        if a.get('normalized'):
            arr /= np.iinfo(dt).max
        return arr.reshape(a['count'], NC[a['type']])

    out = {}
    for an in j.get('animations', []):
        ch = {}
        for c in an['channels']:
            s = an['samplers'][c['sampler']]
            name = j['nodes'][c['target']['node']].get('name')
            ch[(name, c['target']['path'])] = (acc(s['input'])[:, 0], acc(s['output']))
        out[an['name']] = ch
    return out


def sample(times, vals, t):
    return np.array([np.interp(t, times, vals[:, k]) for k in range(vals.shape[1])]).T


bad = []
# 1. The decoded clips against the VANILLA clips, time-mapped (the frames the
#    cut takes them from), outside the seam blend. This is the check that
#    matters (2026-10-28: comparing only with our own export missed nothing
#    there, but it could not have caught a clip that is wrong from the start).
U = os.path.join(HERE, 'ashura-reload', 'uncooked', 'base', 'animations', 'weapon', 'firearms', 'rifle_sniper', 'tsunami_ashura')
VANILLA = {'pwa.glb': 'pwa_w_rifle_sniper__tsunami_ashura.anims.glb', 'pma.glb': 'pma_w_rifle_sniper__tsunami_ashura.anims.glb',
           'base1.glb': 'w_rifle_sniper__tsunami_ashura__base1.anims.glb'}
splice = json.load(open(os.path.join(TR, 'splice.json')))
for authored, decoded in PAIRS:
    V, D = load(os.path.join(U, VANILLA[authored])), load(os.path.join(TR, decoded))
    for clip in CLIPS:
        A, B = splice[clip]['A'], splice[clip]['B']
        L = B - A
        g = np.array([x for x in range(180) if not (B < x < B + 10)])
        f = np.where(g <= B, g, np.where(g <= B + L, A + (g - B), g - L))
        worst_r, worst_p = (0.0, ''), (0.0, '')
        for key, (tv, vv) in V[clip].items():
            if key[1] not in ('rotation', 'translation') or key not in D[clip]:
                continue
            td, vd = D[clip][key]
            x, y = sample(tv, vv, f / 30.0), sample(td, vd, g / 30.0)
            if key[1] == 'rotation':
                x /= np.linalg.norm(x, axis=1, keepdims=True)
                y /= np.linalg.norm(y, axis=1, keepdims=True)
                e = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(x * y, axis=1)), 0, 1))).max()
                if e > worst_r[0]:
                    worst_r = (e, key[0])
            else:
                e = np.linalg.norm(x - y, axis=1).max()
                if e > worst_p[0]:
                    worst_p = (e, key[0])
        print('vs vanilla %-6s %-16s worst rotation %.3f deg (%s), worst position %.2f mm (%s)' % (
            authored[:-4], clip, worst_r[0], worst_r[1], worst_p[0] * 1000, worst_p[1]))
        if worst_r[0] > ROT_TOL or worst_p[0] > POS_TOL:
            bad.append(('vanilla', authored, clip))
# 2. The decoded clips against our own export (the encoder's error alone).
for authored, decoded in PAIRS:
    A, D = load(os.path.join(TR, authored)), load(os.path.join(TR, decoded))
    for clip in CLIPS:
        a, d = A[clip], D[clip]
        t = np.arange(0, 180) / 30.0
        worst_r, worst_p = (0.0, ''), (0.0, '')
        for key, (ta, va) in a.items():
            if key not in d:
                continue
            td, vd = d[key]
            x, y = sample(ta, va, t), sample(td, vd, t)
            if key[1] == 'rotation':
                x /= np.linalg.norm(x, axis=1, keepdims=True)
                y /= np.linalg.norm(y, axis=1, keepdims=True)
                ang = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(x * y, axis=1)), 0, 1))).max()
                if ang > worst_r[0]:
                    worst_r = (ang, key[0])
            elif key[1] == 'translation':
                dist = np.linalg.norm(x - y, axis=1).max()
                if dist > worst_p[0]:
                    worst_p = (dist, key[0])
        missing = [k for k in a if k[1] in ('rotation', 'translation') and k not in d]
        print('%-6s %-16s worst rotation %.3f deg (%s), worst position %.2f mm (%s), decoded ends %.3f s%s' % (
            authored[:-4], clip, worst_r[0], worst_r[1], worst_p[0] * 1000, worst_p[1],
            max(td.max() for td, _ in d.values()), ', MISSING %d channels' % len(missing) if missing else ''))
        if worst_r[0] > ROT_TOL or worst_p[0] > POS_TOL or missing:
            bad.append((authored, clip))
if bad:
    sys.exit('DECODE GATE FAILED: %s' % bad)
print('DECODE GATE OK')
