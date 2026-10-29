"""Turn build_moving_parts.py's skinned GLB into the shipped .mesh, and give
dioscuri_weapon.app the Ashura's animated parts (2026-10-28).

Run after build_moving_parts.py:  python mesh-work\\finish_moving_parts.py
Writes archive-staging\\Dioscuri\\mod\\dioscuri\\meshes\\dioscuri_body.mesh and
archive-staging\\Dioscuri\\mod\\dioscuri\\dioscuri_weapon.app. Both are rebuilt
from the 1.1.0 files in git (commit SHIPPED), so a rerun gives the same result.

The mesh. `WolvenKit.CLI import -k` keeps the existing .mesh's metadata (its
materials) and replaces the geometry buffer. It MERGES bones by name: the
donor's boneNames stay in place and any GLB joint they lack is appended, and
the vertex joint indices it writes point into that merged list (seen
2026-10-28: 1.1.0's mesh carries the Malorian donor's nine bones, and the
import appended the Ashura's after them). So the donor is given exactly the
GLB's joints first, in the GLB's order; the import then appends nothing and
the list stays clean. The bone data, per bone in that order:
- boneNames: the GLB skin's joints, which are the Ashura base1 rig's bone
  names, so the game's rig drives them;
- boneRigMatrices: copied by name from the Ashura's base1_01.mesh (the game's
  own bind matrices for those bones, not Blender's re-export of them);
- boneVertexEpsilons: the Ashura's per bone, but 'barrel' BARREL_EPSILON. A
  skinned weapon mesh is culled from its bone positions plus these margins;
  at 0 it blinks out at some angles (CLAUDE.md, the Meigetsu lesson).
  Dioscuri reaches 1.13 m from 'barrel'; the Ashura's 0.80 covers its own 0.79.
Gate: the materials and appearances are unchanged from 1.1.0's mesh.

The app. As the Ashura's .app does, an animated component on the base1 rig
(weapon.animgraph + the Ashura's base1 anim sets) hangs off Dioscuri's
Receiver, and the body becomes a skinned mesh bound to it. The two ROUNDS
each get the Ashura's cartridge rig (mag_std, weapon.animgraph) in an animated
component of their own, playing Dioscuri's own clip set for that round, and a
skinned mesh component with Dioscuri's round mesh (build_rounds.py and
finish_rounds.py make both: the mesh rests hidden in the chamber, the clips
carry each round from V's hand into its slot and forward with the bolt).
Each new component goes into
BOTH `components` and `compiledData` (the cooked copy the game reads), sharing
their binding handles as vanilla's do, and compiledData's CruidDict (chunk
index -> component id) is rebuilt.

Verify (verify_moving_parts.py) by uncooking the result and reading each
vertex's bone, and in Blender (preview_moving_parts.py) before any launch.
"""
import copy, json, os, shutil, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import wkhandles  # noqa: E402

WK = r'C:\Users\jtrac\dev\tools\WolvenKit.Console\WolvenKit.CLI.exe'
GAME = r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
SHIPPED = 'fdac8c3'  # "Version 1.1.0: the game 2.5 build"
R = os.path.join(HERE, 'ashura-reload')
W = os.path.join(R, 'work')
GLB = os.path.join(W, 'dioscuri_body_skinned.glb')
ASH_MESH = os.path.join(R, 'uncooked', 'base', 'weapons', 'firearms', 'rifle_sniper', 'tsunami_ashura',
                        'entities', 'meshes', 'w_rifle_sniper__tsunami_ashura__base1_01.mesh')
STAGE = os.path.join(ROOT, 'archive-staging', 'Dioscuri', 'mod', 'dioscuri')
BARREL_EPSILON = 1.2
# The rounds (2026-10-28). The first try put the Ashura's cartridge in with its
# own vanilla clip: in game it floated just below the gun, since that clip
# keeps the round 36-78 cm from V's hand while it is out of the gun (CDPR
# parks it out of view), and at rest it sat in Dioscuri's trigger guard (the
# Ashura's receiver hides it there; Dioscuri has none). Now each round has its
# own clips, authored from V's hands (build_rounds.py), and a mesh that rests
# in the chamber, so nothing depends on the component's localTransform
# (unproven in game). `--no-rounds` leaves them out.
ROUNDS = '--no-rounds' not in sys.argv
ROUND_SETS = {'A': 'mod\\dioscuri\\anims\\dioscuri_round_a.anims', 'B': 'mod\\dioscuri\\anims\\dioscuri_round_b.anims'}
ROUND_MESH = 'mod\\dioscuri\\meshes\\dioscuri_round.mesh'
MATERIAL_KEYS = ('appearances', 'materialEntries', 'preloadLocalMaterialInstances', 'preloadExternalMaterials',
                 'externalMaterials', 'localMaterialBuffer', 'localMaterialInstances', 'objectType')


def wk(*args, allow=()):
    r = subprocess.run([WK, *args], capture_output=True, text=True)
    out = '\n'.join(l for l in r.stdout.splitlines() if not any(a in l for a in allow))
    if r.returncode != 0 or 'rror' in out.replace('0 errors', ''):
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit('WolvenKit %s failed' % args[0])


def fresh(*parts):
    p = os.path.join(W, *parts)
    if os.path.exists(p):
        shutil.rmtree(p)
    os.makedirs(p)
    return p


def git_show(path, out):
    data = subprocess.check_output(['git', '-C', ROOT, 'show', '%s:%s' % (SHIPPED, path)])
    with open(out, 'wb') as f:
        f.write(data)


def serialize(path):
    wk('convert', 'serialize', path, '-o', os.path.dirname(path))
    return path + '.json'


def cname(s):
    return {'$type': 'CName', '$storage': 'string', '$value': s}


def glb_json(path):
    b = open(path, 'rb').read()
    n = struct.unpack_from('<I', b, 12)[0]
    return json.loads(b[20:20 + n])


def fnv64(s):
    h = 0xcbf29ce484222325
    for c in s.encode():
        h = ((h ^ c) * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


# ---------------------------------------------------------------- the mesh
g = glb_json(GLB)
joints = [g['nodes'][i]['name'] for i in g['skins'][0]['joints']]
print('GLB joints:', joints)

ash_dir = fresh('ashura')
shutil.copy(ASH_MESH, os.path.join(ash_dir, 'base1_01.mesh'))
ar = json.load(open(serialize(os.path.join(ash_dir, 'base1_01.mesh')), encoding='utf-8'))['Data']['RootChunk']
anames = [b['$value'] for b in ar['boneNames']]
arig = dict(zip(anames, ar['boneRigMatrices']))
aeps = dict(zip(anames, ar['boneVertexEpsilons']))
apos = dict(zip(anames, ar['renderResourceBlob']['Data']['header']['bonePositions']))
missing = [j for j in joints if j not in arig]
assert not missing, 'joints not in the Ashura mesh: %s' % missing


def set_bones(root):
    root['boneNames'] = [cname(j) for j in joints]
    root['boneRigMatrices'] = [copy.deepcopy(arig[j]) for j in joints]
    root['boneVertexEpsilons'] = [BARREL_EPSILON if j == 'barrel' else aeps[j] for j in joints]
    root['lodBoneMask'] = [3] * len(joints)
    # one per bone, beside them in the render blob header; `import -k` keeps the
    # donor's (1.1.0: nine, the Malorian's), and a count that differs from
    # boneNames fails WolvenKit's own export ("Index was outside the bounds")
    root['renderResourceBlob']['Data']['header']['bonePositions'] = [copy.deepcopy(apos[j]) for j in joints]


shipped_dir = fresh('shipped')
git_show('archive-staging/Dioscuri/mod/dioscuri/meshes/dioscuri_body.mesh', os.path.join(shipped_dir, 'dioscuri_body.mesh'))
sj_path = serialize(os.path.join(shipped_dir, 'dioscuri_body.mesh'))
shipped = json.load(open(sj_path, encoding='utf-8'))['Data']['RootChunk']

# the donor: 1.1.0's mesh with the Ashura bones in the GLB's order (see the docstring)
donor = json.load(open(sj_path, encoding='utf-8'))
set_bones(donor['Data']['RootChunk'])
imp = fresh('import')
dj = os.path.join(imp, 'donor', 'dioscuri_body.mesh.json')
os.makedirs(os.path.dirname(dj))
json.dump(donor, open(dj, 'w', encoding='utf-8'), indent=1)
wk('convert', 'deserialize', dj, '-o', imp)
assert os.path.exists(os.path.join(imp, 'dioscuri_body.mesh'))
shutil.copy(GLB, os.path.join(imp, 'dioscuri_body.glb'))
wk('import', os.path.join(imp, 'dioscuri_body.glb'), '-o', imp, '-k')
mj_path = serialize(os.path.join(imp, 'dioscuri_body.mesh'))
mj = json.load(open(mj_path, encoding='utf-8'))
mr = mj['Data']['RootChunk']
after = [b['$value'] for b in mr['boneNames']]
print('after import -k: boneNames', after)
assert after == joints, 'the import changed the bone list: vertex indices would not match'
same_rig = [j for j, m in zip(joints, mr['boneRigMatrices']) if json.dumps(m, sort_keys=True) == json.dumps(arig[j], sort_keys=True)]
print('bind matrices still the Ashura\'s after import: %d of %d; epsilons %s' % (len(same_rig), len(joints), mr['boneVertexEpsilons']))
set_bones(mr)  # put back what the import rewrote (it zeroes the epsilons, CLAUDE.md)
for k in MATERIAL_KEYS:
    assert json.dumps(mr.get(k), sort_keys=True) == json.dumps(shipped.get(k), sort_keys=True), 'import changed %s' % k
changed = sorted(k for k in set(mr) | set(shipped) if json.dumps(mr.get(k), sort_keys=True) != json.dumps(shipped.get(k), sort_keys=True))
print('mesh keys that differ from 1.1.0:', changed)
json.dump(mj, open(mj_path, 'w', encoding='utf-8'), indent=1)
out = fresh('out')
wk('convert', 'deserialize', mj_path, '-o', out)
built_mesh = os.path.join(out, 'dioscuri_body.mesh')
assert os.path.exists(built_mesh), built_mesh

# ---------------------------------------------------------------- the app
app_dir = fresh('app')
git_show('archive-staging/Dioscuri/mod/dioscuri/dioscuri_weapon.app', os.path.join(app_dir, 'dioscuri_weapon.app'))
dio_json = serialize(os.path.join(app_dir, 'dioscuri_weapon.app'))
van = fresh('app', 'vanilla')
wk('extract', os.path.join(GAME, 'archive', 'pc', 'content'), '-w', '*w_rifle_sniper__tsunami_ashura.app', '-o', van)
ash_app = [os.path.join(d, f) for d, _, fs in os.walk(van) for f in fs if f.endswith('tsunami_ashura.app')]
assert len(ash_app) == 1, ash_app
ash_json = serialize(ash_app[0])

doc = wkhandles.load(dio_json)
ash = wkhandles.load(ash_json)


def default_app(d):
    for h in d['Data']['RootChunk']['appearances']:
        a = h.data if isinstance(h, wkhandles.Handle) else h['Data']
        if a['name']['$value'] == 'default':
            return a
    raise KeyError('default')


A = default_app(doc)
S = default_app(ash)


def named(lst, name):
    return [c for c in lst if c.get('name', {}).get('$value') == name][0]


def dup(o, memo):
    """Deep copy that keeps handles shared within the copy (as wkhandles loads them)."""
    if isinstance(o, wkhandles.Handle):
        if id(o) not in memo:
            h = wkhandles.Handle(None)
            memo[id(o)] = h
            h.data = dup(o.data, memo)
        return memo[id(o)]
    if isinstance(o, dict):
        return {k: dup(v, memo) for k, v in o.items()}
    if isinstance(o, list):
        return [dup(v, memo) for v in o]
    return o


def rebind(comp, field, name):
    comp[field].data['bindName'] = cname(name)


ids = {c['id'] for c in A['components']}


def new_id(name):
    i = str(fnv64('dioscuri.' + name) & 0x3FFFFFFFFFFFFFFF)
    assert i not in ids, name
    ids.add(i)
    return i


body_old = named(A['components'], 'dioscuri_body_mesh')
assert body_old['$type'] == 'entMeshComponent', 'already patched? %s' % body_old['$type']

bolt = dup(named(S['components'], 'Barrel'), {})         # base1 rig, weapon.animgraph, base1 anim sets
bolt['name'] = cname('DioscuriBolt')
bolt['id'] = new_id('DioscuriBolt')
assert bolt['parentTransform'].data['bindName']['$value'] == 'Receiver'  # Dioscuri has a Receiver too
# the two-round reload (finish_two_round_reload.py): the player's base1 set is
# Dioscuri's own copy, its three empty_reload clips 180 frames long with the
# bolt held back through the second round. The NPC sets stay vanilla.
ASHURA_BASE1 = 'base\\animations\\weapon\\firearms\\rifle_sniper\\tsunami_ashura\\w_rifle_sniper__tsunami_ashura__base1.anims'
DIOSCURI_BASE1 = 'mod\\dioscuri\\anims\\dioscuri_base1.anims'
swapped = 0
# 2026-10-28 A/B: with the two-round build the whole gun vanished during the
# reload, V's hands stayed. `--vanilla-bolt-clips` keeps the Ashura's own base1
# set on the bolt (the bolt then closes early in the second round) to tell
# whether Dioscuri's re-encoded base1 clips or V's new arm set hide the gun.
if '--vanilla-bolt-clips' in sys.argv:
    DIOSCURI_BASE1 = ASHURA_BASE1
for e in bolt['animations']['gameplay']:
    ed = e.data if isinstance(e, wkhandles.Handle) else e
    if ed['animSet']['DepotPath']['$value'] == ASHURA_BASE1:
        ed['animSet']['DepotPath'] = {'$type': 'ResourcePath', '$storage': 'string', '$value': DIOSCURI_BASE1}
        swapped += 1
assert swapped == 1, 'the Ashura base1 player set was not found once (%d)' % swapped
print('BOLT CLIPS', DIOSCURI_BASE1)

body = dup(named(S['components'], 'w_rifle_sniper__tsunami_ashura__base1_017481'), {})
body['name'] = cname('dioscuri_body_mesh')
body['id'] = body_old['id']
body['mesh'] = copy.deepcopy(body_old['mesh'])
body['meshAppearance'] = cname('default')
rebind(body, 'parentTransform', 'DioscuriBolt')
rebind(body, 'skinning', 'DioscuriBolt')
new = [bolt, body]

# Dioscuri fires a two-round burst, so V loads two (the maintainer, 2026-10-28):
# round A goes in first, round B second, each on its own cartridge rig and
# clip set; both use the one round mesh.
if ROUNDS:
    for rnd, anims in ROUND_SETS.items():
        rc = dup(named(S['components'], 'Magazine'), {})        # the Ashura's cartridge rig + weapon.animgraph
        rc['name'] = cname('DioscuriRound' + rnd)
        rc['id'] = new_id('DioscuriRound' + rnd)
        rebind(rc, 'parentTransform', 'DioscuriBolt')
        # Its animation comes from the component it hangs from, as every vanilla
        # part's does (Ashura: Magazine -> Barrel for both). The copy kept the
        # name 'Barrel', which in Dioscuri's app is the Kang Tao Dian's leftover
        # part with no mesh on it, and the rounds never left the chamber in game
        # (2026-10-29).
        rebind(rc, 'controlBinding', 'DioscuriBolt')
        # only this round's own set: the Ashura's player and NPC cartridge sets
        # would fly the moved mesh around
        entry = rc['animations']['gameplay'][0]
        ed = entry.data if isinstance(entry, wkhandles.Handle) else entry
        ed['animSet']['DepotPath'] = {'$type': 'ResourcePath', '$storage': 'string', '$value': anims}
        rc['animations']['gameplay'] = [entry]
        rm = dup(named(S['components'], 'w_rifle_sniper__tsunami_ashura__mag_std_017138'), {})
        rm['name'] = cname('dioscuri_round_%s_mesh' % rnd.lower())
        rm['id'] = new_id('dioscuri_round_%s_mesh' % rnd.lower())
        rm['mesh']['DepotPath'] = {'$type': 'ResourcePath', '$storage': 'string', '$value': ROUND_MESH}
        rebind(rm, 'parentTransform', 'DioscuriRound' + rnd)
        rebind(rm, 'skinning', 'DioscuriRound' + rnd)
        new += [rc, rm]

# TEST BUILDS ONLY (`--probe-slots`): slot components on the bolt's and each
# round's moving bone, so a CET probe can read where the game puts them
# (SlotComponent.GetSlotTransform, as the player's own 'slots' are read).
PROBE_SLOTS = '--probe-slots' in sys.argv
PROBES = {'DioscuriProbeBolt': ('DioscuriBolt', 'cocking_mechanism')}
if ROUNDS:
    PROBES.update({'DioscuriProbeRound' + rnd: ('DioscuriRound' + rnd, 'mag_std') for rnd in ROUND_SETS})
if PROBE_SLOTS:
    for name, (parent, bone) in PROBES.items():
        sc = dup(named(A['components'], 'FX_slots'), {})
        sc['name'] = cname(name)
        sc['id'] = new_id(name)
        rebind(sc, 'parentTransform', parent)
        slot = copy.deepcopy(sc['slots'][0])
        slot['boneName'] = cname(bone)
        slot['slotName'] = cname('probe')
        slot['relativePosition'] = {'$type': 'Vector3', 'X': 0, 'Y': 0, 'Z': 0}
        sc['slots'] = [slot]
        new.append(sc)
    print('PROBE SLOTS', PROBES)

cd = A['compiledData']['Data']
for lst in (A['components'], cd['Chunks']):
    i = [k for k, c in enumerate(lst) if c.get('name', {}).get('$value') == 'dioscuri_body_mesh']
    assert len(i) == 1
    lst[i[0]:i[0] + 1] = new          # the same dicts in both lists: they share the binding handles
cd['CruidDict'] = {str(i): c['id'] for i, c in enumerate(cd['Chunks'])}

have = {r['DepotPath']['$value'] for r in A['resolvedDependencies']}
for r in S['resolvedDependencies']:
    p = r['DepotPath']['$value']
    if p not in have and '__base1.anims' in p:
        dep = copy.deepcopy(r)
        if p == ASHURA_BASE1:
            dep['DepotPath'] = {'$type': 'ResourcePath', '$storage': 'string', '$value': DIOSCURI_BASE1}
        A['resolvedDependencies'].append(dep)
        have.add(dep['DepotPath']['$value'])
if ROUNDS:
    template = [r for r in S['resolvedDependencies'] if r['DepotPath']['$value'].endswith('__mag_std.anims')][0]
    for anims in ROUND_SETS.values():
        dep = copy.deepcopy(template)
        dep['DepotPath'] = {'$type': 'ResourcePath', '$storage': 'string', '$value': anims}
        A['resolvedDependencies'].append(dep)

patched = os.path.join(app_dir, 'patched', 'dioscuri_weapon.app.json')
os.makedirs(os.path.dirname(patched))
wkhandles.dump(doc, patched)
app_out = fresh('app', 'out')
wk('convert', 'deserialize', patched, '-o', app_out)
built_app = os.path.join(app_out, 'dioscuri_weapon.app')
assert os.path.exists(built_app), built_app

# Gate: the built app reads back with the new components wired as intended
back = json.load(open(serialize(built_app), encoding='utf-8'))
H = {}


def walk(x):
    if isinstance(x, dict):
        if 'HandleId' in x:
            H[x['HandleId']] = x['Data']
        for v in x.values():
            walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)


walk(back)
ba = [a['Data'] for a in back['Data']['RootChunk']['appearances'] if a['Data']['name']['$value'] == 'default'][0]


def binding(c, f):
    h = c.get(f)
    if not h:
        return '-'
    d = H[h['HandleRefId']] if 'HandleRefId' in h else h['Data']
    return d['bindName']['$value']


for where, lst in (('components', ba['components']), ('compiledData', ba['compiledData']['Data']['Chunks'])):
    rows = {c['name']['$value']: (c['$type'], binding(c, 'parentTransform'), binding(c, 'skinning')) for c in lst}
    for n in ('DioscuriBolt', 'dioscuri_body_mesh', 'DioscuriRoundA', 'dioscuri_round_a_mesh', 'DioscuriRoundB', 'dioscuri_round_b_mesh'):
        if n in rows:
            print('APP %-12s %-22s %s' % (where, n, rows[n]))
    assert rows['dioscuri_body_mesh'] == ('entSkinnedMeshComponent', 'DioscuriBolt', 'DioscuriBolt'), rows['dioscuri_body_mesh']
    assert rows['DioscuriBolt'][1] == 'Receiver'
    for rnd in (ROUND_SETS if ROUNDS else ()):
        assert rows['DioscuriRound' + rnd] == ('entAnimatedComponent', 'DioscuriBolt', '-'), rows['DioscuriRound' + rnd]
        assert rows['dioscuri_round_%s_mesh' % rnd.lower()] == ('entSkinnedMeshComponent', 'DioscuriRound' + rnd, 'DioscuriRound' + rnd)
    # every animated part we add takes its animation from its own parent
    for c in lst:
        if c['name']['$value'].startswith('Dioscuri') and c['$type'] == 'entAnimatedComponent':
            ctl = binding(c, 'controlBinding')
            print('APP %-12s %-22s control %s' % (where, c['name']['$value'], ctl))
            assert ctl == binding(c, 'parentTransform'), (c['name']['$value'], ctl)
    for name, (parent, bone) in (PROBES.items() if PROBE_SLOTS else ()):
        c = [x for x in lst if x['name']['$value'] == name][0]
        assert binding(c, 'parentTransform') == parent and c['slots'][0]['boneName']['$value'] == bone, name
    assert PROBE_SLOTS or not any(c['name']['$value'].startswith('DioscuriProbe') for c in lst)
cdb = ba['compiledData']['Data']
assert all(cdb['CruidDict'][str(i)] == c['id'] for i, c in enumerate(cdb['Chunks']))
print('APP resolvedDependencies', len(ba['resolvedDependencies']))

# For preview_moving_parts.py: the built mesh, packed and uncooked back to GLB
# the way the game reads it. Under its own name, so `uncook -gp` (which also
# searches the game's archives, CLAUDE.md) finds nothing else.
ver = fresh('verify')
vm = os.path.join(ver, 'DioscuriVerify', 'mod', 'dioscuri', 'meshes')
os.makedirs(vm)
shutil.copy(built_mesh, os.path.join(vm, 'dioscuri_body_verify.mesh'))
wk('pack', os.path.join(ver, 'DioscuriVerify'), '-o', ver)
wk('uncook', os.path.join(ver, 'DioscuriVerify.archive'), '-o', os.path.join(ver, 'uncook'), '-gp', GAME,
   '-w', '*dioscuri_body_verify.mesh', '--uext', 'png',
   allow=('Failed to export materials',))  # this throwaway archive has no Dioscuri materials; geometry is what is checked
vg = [os.path.join(d, f) for d, _, fs in os.walk(os.path.join(ver, 'uncook')) for f in fs if f.endswith('.glb')]
assert len(vg) == 1, vg
print('VERIFY GLB', vg[0])

shutil.copy(built_mesh, os.path.join(STAGE, 'meshes', 'dioscuri_body.mesh'))
shutil.copy(built_app, os.path.join(STAGE, 'dioscuri_weapon.app'))
print('STAGED', os.path.join(STAGE, 'meshes', 'dioscuri_body.mesh'), os.path.join(STAGE, 'dioscuri_weapon.app'))
print('FINISH MOVING PARTS DONE')
