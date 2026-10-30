"""Build the two round meshes, gate them, stage them (2026-10-28; on the
bolt's cable bones since 2026-10-30).

Run after build_rounds.py (and key_round_bones.py for the motion):
    python mesh-work\\finish_rounds.py

2026-10-30: the rounds no longer have animated components or clip sets of
their own. In game the bolt played our clip exactly, while the round
components (the Ashura's cartridge rig, their own sets) did something none of
our clips do and never showed (HANDOFF.md "Visible rounds"). So each round
mesh is now skinned to a cable bone of the BOLT's rig, which Dioscuri's body
does not use and every clip holds still:
    dioscuri_round_a.mesh -> l_cable_front_01
    dioscuri_round_b.mesh -> l_cable_middle_01
and key_round_bones.py keys the rounds' motion on those bones in the bolt's
own clip set (dioscuri_base1.anims).

1. The geometry (dioscuri_round.glb, build_rounds.py: the Ashura's cartridge
   moved into the chamber, in the gun frame): `import -k` over a copy of the
   Ashura's cartridge mesh, which keeps its materials. Gate: materials and
   appearances unchanged.
2. Per round, the bone data replaced (the vertices stay where they are, in
   the gun frame, all on bone index 0): boneNames = the cable bone,
   boneRigMatrices and bonePositions = the Ashura base1 mesh's own for that
   bone (the game's bind for it; the Ashura skins its real cables there),
   boneVertexEpsilons = EPSILON. A skinned mesh is culled from its bone's
   position plus this margin, and the round rests ~0.2 m from its cable bone.
   With the bone at its bind pose the mesh is exactly in the chamber.
3. Gate, as the game reads it: each mesh packed under a unique name and
   uncooked back; its bounds are build_rounds.py's rest bounds and its one
   skin joint is the cable bone.
4. Copies to archive-staging\\Dioscuri\\mod\\dioscuri\\meshes\\, and removes
   the first build's files from staging (dioscuri_round.mesh and the two
   dioscuri_round_*.anims): a staging tree keeps outputs nothing builds any
   more (CLAUDE.md).
"""
import copy, json, os, shutil, struct, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WK = r'C:\Users\jtrac\dev\tools\WolvenKit.Console\WolvenKit.CLI.exe'
GAME = r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
R = os.path.join(HERE, 'ashura-reload')
U = os.path.join(R, 'uncooked', 'base')
VAN_MESH = os.path.join(U, 'weapons', 'firearms', 'rifle_sniper', 'tsunami_ashura', 'entities', 'meshes', 'w_rifle_sniper__tsunami_ashura__mag_std_01.mesh')
ASH_BASE1 = os.path.join(U, 'weapons', 'firearms', 'rifle_sniper', 'tsunami_ashura', 'entities', 'meshes', 'w_rifle_sniper__tsunami_ashura__base1_01.mesh')
W = os.path.join(R, 'work', 'rounds')
STAGE = os.path.join(ROOT, 'archive-staging', 'Dioscuri', 'mod', 'dioscuri')
BONE = {'a': 'l_cable_front_01', 'b': 'l_cable_middle_01'}
EPSILON = 0.3
MATERIAL_KEYS = ('appearances', 'materialEntries', 'preloadLocalMaterialInstances', 'preloadExternalMaterials',
                 'externalMaterials', 'localMaterialBuffer', 'localMaterialInstances', 'objectType')
STALE = [os.path.join('meshes', 'dioscuri_round.mesh'),
         os.path.join('anims', 'dioscuri_round_a.anims'), os.path.join('anims', 'dioscuri_round_b.anims')]


def wk(*args, allow=()):
    r = subprocess.run([WK, *args], capture_output=True, text=True)
    out = '\n'.join(l for l in r.stdout.splitlines() if not any(a in l for a in allow))
    if r.returncode != 0 or 'rror' in out.replace('0 errors', ''):
        print(r.stdout[-2000:], r.stderr[-1000:])
        raise SystemExit('WolvenKit %s failed' % args[0])


def fresh(*parts):
    p = os.path.join(W, *parts)
    if os.path.exists(p):
        shutil.rmtree(p)
    os.makedirs(p)
    return p


def serialize(path):
    wk('convert', 'serialize', path, '-o', os.path.dirname(path))
    return path + '.json'


def cname(s):
    return {'$type': 'CName', '$storage': 'string', '$value': s}


os.makedirs(os.path.join(STAGE, 'meshes'), exist_ok=True)

# ---------------------------------------------------------------- 1. the geometry
mw = fresh('mesh')
shutil.copy(VAN_MESH, os.path.join(mw, 'dioscuri_round.mesh'))
van = json.load(open(serialize(os.path.join(mw, 'dioscuri_round.mesh')), encoding='utf-8'))['Data']['RootChunk']
shutil.copy(os.path.join(W, 'dioscuri_round.glb'), os.path.join(mw, 'dioscuri_round.glb'))
wk('import', os.path.join(mw, 'dioscuri_round.glb'), '-o', mw, '-k')
mj_path = serialize(os.path.join(mw, 'dioscuri_round.mesh'))
mj = json.load(open(mj_path, encoding='utf-8'))
mr = mj['Data']['RootChunk']
assert [b['$value'] for b in mr['boneNames']] == ['mag_std'], mr['boneNames']
for k in MATERIAL_KEYS:
    assert json.dumps(mr.get(k), sort_keys=True) == json.dumps(van.get(k), sort_keys=True), 'import changed %s' % k
print('mesh boundingBox', {k: [round(mr['boundingBox'][k][a], 4) for a in 'XYZ'] for k in ('Min', 'Max')})

# the game's bind for the cable bones: the Ashura base1 mesh's own
aw = fresh('ashura_base1')
shutil.copy(ASH_BASE1, os.path.join(aw, 'base1_01.mesh'))
ar = json.load(open(serialize(os.path.join(aw, 'base1_01.mesh')), encoding='utf-8'))['Data']['RootChunk']
anames = [b['$value'] for b in ar['boneNames']]

# ---------------------------------------------------------------- 2.-3. one mesh per round
for rnd, bone in BONE.items():
    name = 'dioscuri_round_%s' % rnd
    i = anames.index(bone)
    doc = copy.deepcopy(mj)
    r = doc['Data']['RootChunk']
    r['boneNames'] = [cname(bone)]
    r['boneRigMatrices'] = [copy.deepcopy(ar['boneRigMatrices'][i])]
    r['renderResourceBlob']['Data']['header']['bonePositions'] = [copy.deepcopy(ar['renderResourceBlob']['Data']['header']['bonePositions'][i])]
    r['boneVertexEpsilons'] = [EPSILON]
    assert len(r.get('lodBoneMask') or [3]) == 1, r.get('lodBoneMask')
    jw = fresh('mesh_' + rnd)
    jp = os.path.join(jw, name + '.mesh.json')
    json.dump(doc, open(jp, 'w', encoding='utf-8'), indent=1)
    out = fresh('mesh_out_' + rnd)
    wk('convert', 'deserialize', jp, '-o', out)
    built = os.path.join(out, name + '.mesh')
    assert os.path.exists(built), built

    # gate: as the game reads it (packed under a unique name, uncooked back)
    ver = fresh('verify_' + rnd)
    vname = 'DioscuriRoundVerify' + rnd.upper()
    vm = os.path.join(ver, vname, 'mod', 'dioscuri', 'meshes')
    os.makedirs(vm)
    shutil.copy(built, os.path.join(vm, '%s_verify.mesh' % name))
    wk('pack', os.path.join(ver, vname), '-o', ver)
    wk('uncook', os.path.join(ver, vname + '.archive'), '-o', os.path.join(ver, 'uncook'), '-gp', GAME,
       '-w', '*%s_verify.mesh' % name, '--uext', 'png', allow=('Failed to export materials',))
    vg = [os.path.join(d, f) for d, _, fs in os.walk(os.path.join(ver, 'uncook')) for f in fs if f.endswith('.glb')]
    assert len(vg) == 1, vg
    b = open(vg[0], 'rb').read()
    j = json.loads(b[20:20 + struct.unpack_from('<I', b, 12)[0]])
    acc = j['accessors'][j['meshes'][0]['primitives'][0]['attributes']['POSITION']]
    lo, hi = acc['min'], acc['max']
    # glTF is Y up: game (x, y, z) = glTF (x, -z, y)
    game_lo, game_hi = (lo[0], -hi[2], lo[1]), (hi[0], -lo[2], hi[1])
    want_lo, want_hi = (-0.0071, 0.1277, 0.0645), (0.0071, 0.2024, 0.0788)   # build_rounds.py's rest bounds
    err = max(max(abs(a - c) for a, c in zip(game_lo, want_lo)), max(abs(a - c) for a, c in zip(game_hi, want_hi)))
    joints = [j['nodes'][k]['name'] for s in j.get('skins', []) for k in s['joints']]
    print('VERIFY %s: %d vertices, bounds %s .. %s (off by %.4f m), skin joints %s' % (
        name, acc['count'], tuple(round(x, 4) for x in game_lo), tuple(round(x, 4) for x in game_hi), err, joints))
    assert err < 0.0015, 'the round mesh is not where build_rounds.py put it'
    assert joints == [bone], joints
    shutil.copy(built, os.path.join(STAGE, 'meshes', name + '.mesh'))
    print('STAGED', os.path.join(STAGE, 'meshes', name + '.mesh'))

for p in STALE:
    full = os.path.join(STAGE, p)
    if os.path.exists(full):
        os.remove(full)
        print('REMOVED stale', full)
print('FINISH ROUNDS DONE')
