"""Import build_two_round_reload.py's clips into Dioscuri's own copies of the
Ashura's sets, gate them, patch the sound events, stage them (2026-10-28).

Run after build_two_round_reload.py:  python mesh-work\\finish_two_round_reload.py

Per set (V's arms pwa/pma, the gun's bolt base1):
1. Headless import (aeroboard tools\\wkit-anims-import, the GUI's own importer:
   "Use existing file" on a COPY of the vanilla set). It rebuilds the three
   clips the GLB holds and keeps every other clip verbatim.
2. Gates on the result against the vanilla set:
   - the untouched clips' data bytes are identical;
   - the rebuilt clips' bytes CHANGED (a failed import that leaves the old
     clips must not pass; CLAUDE.md, aeroboard launch 19), 180 frames,
     numExtraJoints 0, same joints and tracks;
   - fallbackFrameIndices: restored to the vanilla clip's values (the
     importer has written out-of-range ones before: a hard crash) and checked
     in range of the set's fallbackAnimDescIndexes.
   Chunk sizes are printed beside the largest vanilla chunk: the vanilla
   Ashura empty_reload alone is 356,714 B, so CLAUDE.md's "131,062 B
   ceiling" does not hold for SIMD buffers.
3. Sound events (arms only): an event inside the repeated stretch (A..B]
   plays again L = B - A frames later (the second mag_new_grab/move_long and
   load); an event after B moves L frames later (handle_release, grab).
4. Deserialize, copy to archive-staging\\Dioscuri\\mod\\dioscuri\\anims\\.
"""
import base64, copy, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import wkhandles  # noqa: E402

WK_DIR = r'C:\Users\jtrac\dev\tools\WolvenKit.Console'
WK = os.path.join(WK_DIR, 'WolvenKit.CLI.exe')
IMPORTER = r'C:\Users\jtrac\dev\cp2077-mods\aeroboard\tools\wkit-anims-import\bin\Release\net8.0\wkit-anims-import.dll'
R = os.path.join(HERE, 'ashura-reload')
U = os.path.join(R, 'uncooked', 'base', 'animations', 'weapon', 'firearms', 'rifle_sniper', 'tsunami_ashura')
TR = os.path.join(R, 'work', 'two_round')
STAGE = os.path.join(ROOT, 'archive-staging', 'Dioscuri', 'mod', 'dioscuri', 'anims')
SETS = [  # (glb, vanilla set, Dioscuri set, has sound events)
    ('pwa', 'pwa_w_rifle_sniper__tsunami_ashura', 'pwa_dioscuri', True),
    ('pma', 'pma_w_rifle_sniper__tsunami_ashura', 'pma_dioscuri', True),
    ('base1', 'w_rifle_sniper__tsunami_ashura__base1', 'dioscuri_base1', False),
]
splice = json.load(open(os.path.join(TR, 'splice.json')))


def wk(*args):
    r = subprocess.run([WK, *args], capture_output=True, text=True)
    if r.returncode != 0 or 'rror' in r.stdout.replace('0 errors', ''):
        print(r.stdout[-2000:], r.stderr[-1000:])
        raise SystemExit('WolvenKit %s failed' % args[0])


def clips(root):
    return {e['Data']['animation']['Data']['name']['$value']: e for e in root['animations']}


def clip_bytes(root, entry):
    buf = entry['Data']['animation']['Data']['animBuffer']['Data']
    a = buf['dataAddress']
    if a['unkIndex'] == 4294967295:
        return base64.b64decode(buf['inplaceCompressedBuffer']['Bytes'])
    chunk = base64.b64decode(root['animationDataChunks'][a['unkIndex']]['buffer']['Bytes'])
    return chunk[a['fsetInBytes']:a['fsetInBytes'] + a['zeInBytes']]


def chunk_sizes(root):
    return [len(base64.b64decode(c['buffer']['Bytes'])) for c in root['animationDataChunks']]


os.makedirs(STAGE, exist_ok=True)
for glb, van, out, has_events in SETS:
    work = os.path.join(TR, 'import', out)
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    imported = os.path.join(work, out + '.anims')
    r = subprocess.run(['dotnet', 'exec', '--runtimeconfig', os.path.join(WK_DIR, 'WolvenKit.CLI.runtimeconfig.json'),
                        '--depsfile', os.path.join(WK_DIR, 'WolvenKit.CLI.deps.json'), IMPORTER,
                        WK_DIR, os.path.join(TR, glb + '.glb'), os.path.join(U, van + '.anims'), imported],
                       cwd=WK_DIR, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(imported):
        print(r.stdout[-3000:], r.stderr[-2000:])
        raise SystemExit('import failed: %s' % out)
    wk('convert', 'serialize', imported, '-o', work)
    doc = json.load(open(imported + '.json', encoding='utf-8'))
    root = doc['Data']['RootChunk']
    vroot = json.load(open(os.path.join(U, van + '.anims.json'), encoding='utf-8'))['Data']['RootChunk']
    nc, vc = clips(root), clips(vroot)
    assert set(nc) == set(vc), 'clip list changed: %s' % (set(nc) ^ set(vc))
    nfb = len(root['fallbackAnimDescIndexes'])
    for name in sorted(nc):
        nb, vb = clip_bytes(root, nc[name]), clip_bytes(vroot, vc[name])
        if name not in splice:
            assert nb == vb, '%s: an untouched clip changed' % name
            continue
        assert nb != vb, '%s: NOT rebuilt (the import left the old clip)' % name
        buf = nc[name]['Data']['animation']['Data']['animBuffer']['Data']
        vbuf = vc[name]['Data']['animation']['Data']['animBuffer']['Data']
        assert buf['numFrames'] == splice[name]['frames'], (name, buf['numFrames'])
        assert buf['numExtraJoints'] == 0 and buf['numJoints'] == vbuf['numJoints'] and buf['numTracks'] == vbuf['numTracks'], name
        if buf['fallbackFrameIndices'] != vbuf['fallbackFrameIndices']:
            print('  %s %s: fallbackFrameIndices %s -> restored %s' % (out, name, buf['fallbackFrameIndices'], vbuf['fallbackFrameIndices']))
            buf['fallbackFrameIndices'] = list(vbuf['fallbackFrameIndices'])
        assert all(0 <= i < nfb for i in buf['fallbackFrameIndices']), name
        print('  %-14s %-16s %s %d frames %.3f s, %d B (vanilla %d B)' % (out, name, buf['$type'][4:], buf['numFrames'], nc[name]['Data']['animation']['Data']['duration'], len(nb), len(vb)))
    print('  %-14s chunks %s (largest vanilla %d B)' % (out, chunk_sizes(root), max(chunk_sizes(vroot))))
    json.dump(doc, open(imported + '.json', 'w', encoding='utf-8'), indent=1)

    if has_events:
        hd = wkhandles.load(imported + '.json')
        for e in hd['Data']['RootChunk']['animations']:
            d = e.data if isinstance(e, wkhandles.Handle) else e['Data']
            name = d['animation'].data['name']['$value'] if isinstance(d['animation'], wkhandles.Handle) else d['animation']['Data']['name']['$value']
            if name not in splice:
                continue
            A, B = splice[name]['A'], splice[name]['B']
            L = B - A
            cont = d['events'].data
            before = len(cont['events'])
            vevs = [x['Data'] for x in vc[name]['Data']['events']['Data']['events']]
            evs = [x.data for x in cont['events']]
            # start from the vanilla timing whatever the import left
            assert sorted((x['eventName']['$value'], x['startFrame']) for x in evs) == sorted((x['eventName']['$value'], x['startFrame']) for x in vevs), name
            new = []
            for x in cont['events']:
                sf = x.data['startFrame']
                if sf > B:
                    x.data['startFrame'] = sf + L
                elif sf > A:
                    twin = wkhandles.Handle(copy.deepcopy(x.data))
                    twin.data['startFrame'] = sf + L
                    new.append(twin)
            cont['events'].extend(new)
            cont['events'].sort(key=lambda h: h.data['startFrame'])
            print('  %-14s %-16s events %d -> %d: %s' % (out, name, before, len(cont['events']),
                  ', '.join('%s@%d' % (h.data['eventName']['$value'].replace('w_gun_sniper_smart_ashura_', ''), h.data['startFrame']) for h in cont['events'])))
        wkhandles.dump(hd, imported + '.json')

    final = os.path.join(work, 'final')
    os.makedirs(final)
    wk('convert', 'deserialize', imported + '.json', '-o', final)
    built = os.path.join(final, out + '.anims')
    assert os.path.exists(built), built
    shutil.copy(built, os.path.join(STAGE, out + '.anims'))
    print('STAGED', os.path.join(STAGE, out + '.anims'))
print('FINISH TWO ROUND RELOAD DONE')
