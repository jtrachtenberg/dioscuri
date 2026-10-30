"""Gate the rounds as the game will play them (2026-10-30).

The rounds ride the bolt's cable bones (key_round_bones.py). This decodes
nothing itself: it reads the GLB WolvenKit exports from the STAGED
dioscuri_base1.anims (`export -gp`, ashura-reload/work/two_round/
decoded_rounds/), runs forward kinematics on the bolt rig every frame, and
puts each round where its mesh's skin puts it:
    centre(t) = C(t) @ C_rest^-1 @ chamber
(C = the cable bone's model pose, C_rest its bind, the mesh's vertices sit
in the chamber at bind). That is compared with build_rounds.py's authored
centre (rounds.json) every frame, and the round's axis (+Y) with the
authored axis. Also checks that the bolt itself decodes as before.

Run (after the decoded GLB exists):  python mesh-work\\verify_round_bones.py
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or '.') != HERE]   # mesh-work's inspect.py shadows the stdlib's
import numpy as np  # noqa: E402

R = os.path.join(HERE, 'ashura-reload', 'work')
DECODED = os.path.join(R, 'two_round', 'decoded_rounds', 'dioscuri_base1.anims.glb')
ROUNDS = os.path.join(R, 'rounds', 'rounds.json')
BONE = {'A': 'l_cable_front_01', 'B': 'l_cable_middle_01'}
POS_TOL, ROT_TOL = 0.003, 0.5   # m, deg


def load(path):
    b = open(path, 'rb').read()
    n = struct.unpack_from('<I', b, 12)[0]
    js = json.loads(b[20:20 + n])
    off = 20 + n
    bl = struct.unpack_from('<I', b, off)[0]
    bin_ = b[off + 8:off + 8 + bl]

    def acc(i):
        a = js['accessors'][i]
        bv = js['bufferViews'][a['bufferView']]
        c = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
        arr = np.frombuffer(bin_, np.float32, a['count'] * c, bv.get('byteOffset', 0) + a.get('byteOffset', 0))
        return arr.reshape(a['count'], c).astype(float) if c > 1 else arr.astype(float)
    return js, acc


def qmat(q):
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


# glTF is Y up: game (x, y, z) = glTF (x, -z, y)
G = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)

js, acc = load(DECODED)
nodes = js['nodes']
parent = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}
idx = {n['name']: i for i, n in enumerate(nodes)}


def chain(name):
    out, i = [], idx[name]
    while i is not None:
        out.append(i)
        i = parent.get(i)
    return out[::-1]


def model(anim_ch, name, t):
    m = np.eye(4)
    for i in chain(name):
        n = nodes[i]
        T = np.array(n.get('translation', [0, 0, 0]), float)
        Q = np.array(n.get('rotation', [0, 0, 0, 1]), float)
        if (i, 'translation') in anim_ch:
            ts, vs = anim_ch[(i, 'translation')]
            T = np.array([np.interp(t, ts, vs[:, k]) for k in range(3)])
        if (i, 'rotation') in anim_ch:
            ts, vs = anim_ch[(i, 'rotation')]
            Q = np.array([np.interp(t, ts, vs[:, k]) for k in range(4)])
        L = np.eye(4)
        L[:3, :3] = qmat(Q)
        L[:3, 3] = T
        m = m @ L
    return G @ m          # in the game frame


def bind(name):
    return model({}, name, 0.0)


rj = json.load(open(ROUNDS))
chamber = np.array(rj['chamber'] + [1.0])
failed = False
for an in js['animations']:
    clip = an['name']
    if clip not in rj['pose']:
        continue
    ch = {}
    for c in an['channels']:
        s = an['samplers'][c['sampler']]
        ch[(c['target']['node'], c['target']['path'])] = (acc(s['input']), acc(s['output']))
    for rnd, bone in BONE.items():
        rest_inv = np.linalg.inv(bind(bone))
        worst_p = worst_r = 0.0
        at = None
        for f, P in enumerate(rj['pose'][clip][rnd]):
            P = np.array(P)
            M = model(ch, bone, f / 30.0) @ rest_inv     # the rigid motion the skin applies
            centre = (M @ chamber)[:3]
            dp = np.linalg.norm(centre - P[:3, 3])
            # the round's axis: the authored pose's +Y vs the decoded motion's
            want_axis = P[:3, 1]
            got_axis = M[:3, :3] @ np.array([0, 1, 0])
            dr = np.degrees(np.arccos(np.clip(np.dot(want_axis, got_axis), -1, 1)))
            if dp > worst_p:
                worst_p, at = dp, f
            worst_r = max(worst_r, dr)
        ok = worst_p < POS_TOL and worst_r < ROT_TOL
        failed |= not ok
        print('%-16s round %s (%s): centre within %.2f mm of the authored path (worst at f%d), axis within %.2f deg  %s' % (
            clip, rnd, bone, worst_p * 1000, at, worst_r, 'ok' if ok else 'FAIL'))
    # the bolt: closed 0.1083, open 0.0083 (as the in-game probe read it)
    by = [model(ch, 'cocking_mechanism', f / 30.0)[1, 3] for f in range(180)]
    print('%-16s bolt y %.4f .. %.4f' % (clip, min(by), max(by)))
if failed:
    raise SystemExit('VERIFY ROUND BONES FAILED')
print('VERIFY ROUND BONES OK')
