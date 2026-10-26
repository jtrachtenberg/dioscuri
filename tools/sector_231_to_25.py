"""Convert a 2.31 streaming sector JSON (sector version 62, WolvenKit 8.20) to
game 2.5's layout (sector version 68, WolvenKit 10). v0.12.231.

Why: 2.5 replaced each node's setup record. A 2.31 record (Position,
Orientation, Bounds, QuestPrefabRefHash, MaxStreamingDistance, ...) became a
`worldCompiledNodeInstanceSetupInfo` (transform, streaming reference points,
nodeFlags, instanceIndex, globalNodeId, ...). The 2.5 streamer reads a mod's
version-62 sector with the new layout: our first 2.5 body take crashed in the
streamer's node attach loop on a cooked-element getter fed index -1 (PLAN.md
"2.5 port", 21:14 launch). WolvenKit 10 reads our old records as garbage too.

Every rule below is read off vanilla 2.5 sectors (exterior_-2_20_1_0,
always_loaded_1), serialized with WolvenKit 10.0.0-beta.1:
- instanceIndex 4294967295 (-1) on every classic node; only the new
  worldCooked* classes index a cooked element.
- globalNodeId is FNV-1a 64 of the node's ref string exactly as written
  (27 of 29 entity refs, and the community registry's own ref). A 2.31 record
  named its ref in QuestPrefabRefHash: a string is hashed, a stored uint64
  (already that hash) is kept.
- streamingDistance is the 2.31 record's UkFloat1 (the vanilla registry's
  17.320507 matches ours exactly).
- streamingRefPoint and preboostStreamingRefPoint are the node's position;
  nodeFlags FLAG_AllowForceStreamIn, streamingPriority 1, dataGroup Base,
  secondaryRefPointDistance FLT_MAX, as vanilla community and entity nodes.
- persistentNodes repeats nodeData (vanilla always-loaded: 15249 of 15249;
  exterior: every non-variant entry).
The nodes themselves are unchanged.

  python tools/sector_231_to_25.py <2.31 json> <2.5 json out>
"""
import json
import sys

FLT_MAX = 3.40282347e+38


def fnv1a64(text):
    h = 0xCBF29CE484222325
    for c in text.encode('utf-8'):
        h ^= c
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def global_id(ref):
    # the 2.31 QuestPrefabRefHash: a NodeRef stored as a string or as its hash
    if ref.get('$storage') == 'string':
        return fnv1a64(ref['$value'])
    return int(ref['$value'])


def vec3(v):
    return {'$type': 'Vector3', 'X': v['X'], 'Y': v['Y'], 'Z': v['Z']}


def convert_record(old):
    pos = old['Position']
    return {
        '$type': 'worldCompiledNodeInstanceSetupInfo',
        'dataGroup': 'Base',
        'externalInplaceResourceHash': {'DepotPath': old['CookedPrefabData']['DepotPath'], 'Flags': 'Default'},
        'globalNodeId': {'$type': 'worldGlobalNodeID', 'hash': str(global_id(old['QuestPrefabRefHash']))},
        'instanceIndex': 4294967295,
        'nodeFlags': 'FLAG_AllowForceStreamIn',
        'nodeIdx': str(old['NodeIndex']),
        'patchedNode': {'$type': 'NodeRef', '$storage': 'uint64', '$value': '0'},
        'preboostStreamingRefPoint': vec3(pos),
        'proxyMeshId': {'$type': 'worldGlobalNodeID', 'hash': '0'},
        'scale': old['Scale'],
        'secondaryRefPointDistance': FLT_MAX,
        'secondaryRefPointPosition': {'$type': 'Vector3', 'X': 0, 'Y': 0, 'Z': 0},
        'streamingDistance': old['UkFloat1'],
        'streamingPriority': '1',
        'streamingRefPoint': vec3(pos),
        'todvisMask': '0',
        'transform': {'$type': 'Transform', 'orientation': old['Orientation'], 'position': pos},
    }


def main(src, dst):
    d = json.load(open(src, encoding='utf-8'))
    s = d['Data']['RootChunk']
    if s['version'] != 62:
        sys.exit(f'{src}: sector version {s["version"]}, expected 62 (2.31)')
    records = [convert_record(r) for r in s['nodeData']['Data']]
    s['nodeData']['Data'] = records
    s['persistentNodes'] = [dict(r) for r in records]
    s['version'] = 68
    d['Header']['WolvenKitVersion'] = '10.0.0-beta.1'
    d['Header']['GameVersion'] = 2500
    with open(dst, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f'{dst}: {len(records)} records, version 68, ids',
          [r['globalNodeId']['hash'] for r in records])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
