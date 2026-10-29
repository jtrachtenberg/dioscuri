"""Import build_rounds.py's rounds into game files, gate them, stage them
(2026-10-28).

Run after build_rounds.py:  python mesh-work\\finish_rounds.py

1. The clip sets, one per round (round_a.glb -> dioscuri_round_a.anims,
   round_b.glb -> dioscuri_round_b.anims): the headless import
   (aeroboard tools\\wkit-anims-import, the GUI's importer, "Use existing
   file") into a COPY of the Ashura's cartridge set
   (w_rifle_sniper__tsunami_ashura__mag_std.anims: rig mag_std, 3 joints,
   the three empty_reload clips and first_equip). All four clips are
   rebuilt. Gates, as finish_two_round_reload.py: every clip's bytes
   changed, frames (180, first_equip 142), numExtraJoints 0, same joints,
   a COMPRESSED buffer (the vanilla set is SIMD; a SIMD re-encode hid the
   whole gun in game), fallbackFrameIndices restored to the vanilla clip's
   and in range.
2. The mesh (dioscuri_round.glb -> dioscuri_round.mesh): `import -k` over a
   copy of the Ashura's cartridge mesh, which keeps its materials. Then the
   bone data is put back from the vanilla mesh (one bone, mag_std: its bind
   matrix and bonePosition), and its vertex epsilon raised to EPSILON: a
   skinned mesh is culled from its bone's position plus this margin, and the
   round now sits ~0.2 m from mag_std's position (the mesh rests in the
   chamber, the bone stays at the gun origin). Gates: materials and
   appearances unchanged; then the built mesh is packed and uncooked back
   (as the game reads it) and its bounds checked against build_rounds.py's.
3. Copies to archive-staging\\Dioscuri\\mod\\dioscuri\\anims\\ and \\meshes\\.
"""
import base64, json, os, shutil, struct, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WK_DIR = r'C:\Users\jtrac\dev\tools\WolvenKit.Console'
WK = os.path.join(WK_DIR, 'WolvenKit.CLI.exe')
GAME = r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
IMPORTER = r'C:\Users\jtrac\dev\cp2077-mods\aeroboard\tools\wkit-anims-import\bin\Release\net8.0\wkit-anims-import.dll'
R = os.path.join(HERE, 'ashura-reload')
U = os.path.join(R, 'uncooked', 'base')
VAN_SET = os.path.join(U, 'animations', 'weapon', 'firearms', 'rifle_sniper', 'tsunami_ashura', 'w_rifle_sniper__tsunami_ashura__mag_std.anims')
VAN_MESH = os.path.join(U, 'weapons', 'firearms', 'rifle_sniper', 'tsunami_ashura', 'entities', 'meshes', 'w_rifle_sniper__tsunami_ashura__mag_std_01.mesh')
W = os.path.join(R, 'work', 'rounds')
STAGE = os.path.join(ROOT, 'archive-staging', 'Dioscuri', 'mod', 'dioscuri')
# first_equip: the importer counts int(last key time * 30) + 1, and 4.7 s in
# float32 is 140.99999 frames, so the vanilla 142 comes back 141 (the round
# holds still through it, so one frame shorter changes nothing)
FRAMES = {'empty_reload': (180,), 'empty_reload_01': (180,), 'empty_reload_02': (180,), 'first_equip': (141, 142)}
EPSILON = 0.3
MATERIAL_KEYS = ('appearances', 'materialEntries', 'preloadLocalMaterialInstances', 'preloadExternalMaterials',
                 'externalMaterials', 'localMaterialBuffer', 'localMaterialInstances', 'objectType')


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


def clips(root):
    return {e['Data']['animation']['Data']['name']['$value']: e for e in root['animations']}


def clip_bytes(root, entry):
    buf = entry['Data']['animation']['Data']['animBuffer']['Data']
    a = buf['dataAddress']
    if a['unkIndex'] == 4294967295:
        return base64.b64decode(buf['inplaceCompressedBuffer']['Bytes'])
    chunk = base64.b64decode(root['animationDataChunks'][a['unkIndex']]['buffer']['Bytes'])
    return chunk[a['fsetInBytes']:a['fsetInBytes'] + a['zeInBytes']]


os.makedirs(os.path.join(STAGE, 'anims'), exist_ok=True)
os.makedirs(os.path.join(STAGE, 'meshes'), exist_ok=True)
vroot = json.load(open(VAN_SET + '.json', encoding='utf-8'))['Data']['RootChunk']
vc = clips(vroot)

# ---------------------------------------------------------------- 1. the clip sets
for rnd in 'ab':
    out = 'dioscuri_round_%s' % rnd
    work = fresh('import', out)
    imported = os.path.join(work, out + '.anims')
    r = subprocess.run(['dotnet', 'exec', '--runtimeconfig', os.path.join(WK_DIR, 'WolvenKit.CLI.runtimeconfig.json'),
                        '--depsfile', os.path.join(WK_DIR, 'WolvenKit.CLI.deps.json'), IMPORTER,
                        WK_DIR, os.path.join(W, 'round_%s.glb' % rnd), VAN_SET, imported],
                       cwd=WK_DIR, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(imported):
        print(r.stdout[-3000:], r.stderr[-2000:])
        raise SystemExit('import failed: %s' % out)
    doc = json.load(open(serialize(imported), encoding='utf-8'))
    root = doc['Data']['RootChunk']
    nc = clips(root)
    assert set(nc) == set(vc) == set(FRAMES), 'clip list: %s' % sorted(nc)
    nfb = len(root['fallbackAnimDescIndexes'])
    for name in sorted(nc):
        nb, vb = clip_bytes(root, nc[name]), clip_bytes(vroot, vc[name])
        assert nb != vb, '%s %s: NOT rebuilt (the import left the old clip)' % (out, name)
        buf = nc[name]['Data']['animation']['Data']['animBuffer']['Data']
        vbuf = vc[name]['Data']['animation']['Data']['animBuffer']['Data']
        assert buf['numFrames'] in FRAMES[name], (out, name, buf['numFrames'])
        assert buf['$type'] == 'animAnimationBufferCompressed', (out, name, buf['$type'])
        assert buf['numExtraJoints'] == 0 and buf['numJoints'] == vbuf['numJoints'] and buf['numTracks'] == vbuf['numTracks'], (out, name)
        if buf['fallbackFrameIndices'] != vbuf['fallbackFrameIndices']:
            print('  %s %s: fallbackFrameIndices %s -> restored %s' % (out, name, buf['fallbackFrameIndices'], vbuf['fallbackFrameIndices']))
            buf['fallbackFrameIndices'] = list(vbuf['fallbackFrameIndices'])
        assert all(0 <= i < nfb for i in buf['fallbackFrameIndices']), (out, name)
        print('  %-18s %-16s %s %d frames %.3f s, %d B (vanilla %d B)' % (
            out, name, buf['$type'][4:], buf['numFrames'], nc[name]['Data']['animation']['Data']['duration'], len(nb), len(vb)))
    json.dump(doc, open(imported + '.json', 'w', encoding='utf-8'), indent=1)
    final = os.path.join(work, 'final')
    os.makedirs(final)
    wk('convert', 'deserialize', imported + '.json', '-o', final)
    built = os.path.join(final, out + '.anims')
    assert os.path.exists(built), built
    shutil.copy(built, os.path.join(STAGE, 'anims', out + '.anims'))
    print('STAGED', os.path.join(STAGE, 'anims', out + '.anims'))

# ---------------------------------------------------------------- 2. the mesh
mw = fresh('mesh')
shutil.copy(VAN_MESH, os.path.join(mw, 'dioscuri_round.mesh'))
van = json.load(open(serialize(os.path.join(mw, 'dioscuri_round.mesh')), encoding='utf-8'))['Data']['RootChunk']
shutil.copy(os.path.join(W, 'dioscuri_round.glb'), os.path.join(mw, 'dioscuri_round.glb'))
wk('import', os.path.join(mw, 'dioscuri_round.glb'), '-o', mw, '-k')
mj_path = serialize(os.path.join(mw, 'dioscuri_round.mesh'))
mj = json.load(open(mj_path, encoding='utf-8'))
mr = mj['Data']['RootChunk']
assert [b['$value'] for b in mr['boneNames']] == ['mag_std'], mr['boneNames']
print('after import -k: bind matrix %s, epsilon %s' % (
    'unchanged' if json.dumps(mr['boneRigMatrices'], sort_keys=True) == json.dumps(van['boneRigMatrices'], sort_keys=True) else 'CHANGED (restored)',
    mr['boneVertexEpsilons']))
mr['boneRigMatrices'] = van['boneRigMatrices']
mr['renderResourceBlob']['Data']['header']['bonePositions'] = van['renderResourceBlob']['Data']['header']['bonePositions']
mr['boneVertexEpsilons'] = [EPSILON]
for k in MATERIAL_KEYS:
    assert json.dumps(mr.get(k), sort_keys=True) == json.dumps(van.get(k), sort_keys=True), 'import changed %s' % k
print('mesh boundingBox', {k: [round(mr['boundingBox'][k][a], 4) for a in 'XYZ'] for k in ('Min', 'Max')})
json.dump(mj, open(mj_path, 'w', encoding='utf-8'), indent=1)
mout = fresh('mesh_out')
wk('convert', 'deserialize', mj_path, '-o', mout)
built_mesh = os.path.join(mout, 'dioscuri_round.mesh')
assert os.path.exists(built_mesh), built_mesh

# gate: the mesh as the game reads it (packed under a unique name, uncooked back)
ver = fresh('verify')
vm = os.path.join(ver, 'DioscuriRoundVerify', 'mod', 'dioscuri', 'meshes')
os.makedirs(vm)
shutil.copy(built_mesh, os.path.join(vm, 'dioscuri_round_verify.mesh'))
wk('pack', os.path.join(ver, 'DioscuriRoundVerify'), '-o', ver)
wk('uncook', os.path.join(ver, 'DioscuriRoundVerify.archive'), '-o', os.path.join(ver, 'uncook'), '-gp', GAME,
   '-w', '*dioscuri_round_verify.mesh', '--uext', 'png', allow=('Failed to export materials',))
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
print('VERIFY uncooked round mesh: %d vertices, bounds %s .. %s (off by %.4f m)' % (
    acc['count'], tuple(round(x, 4) for x in game_lo), tuple(round(x, 4) for x in game_hi), err))
assert err < 0.0015, 'the round mesh is not where build_rounds.py put it'
shutil.copy(built_mesh, os.path.join(STAGE, 'meshes', 'dioscuri_round.mesh'))
print('STAGED', os.path.join(STAGE, 'meshes', 'dioscuri_round.mesh'))
print('FINISH ROUNDS DONE')
