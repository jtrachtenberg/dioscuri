"""Dioscuri's player-entity patches for the two-round reload (2026-10-28).

V's arms play the Ashura's FPP set, chosen by the record's friendlyName
(w_rifle_sniper_tsunami_ashura, shared with the vanilla Ashura). Dioscuri's
two-round reload clips go in their own sets (pwa_/pma_dioscuri.anims), added to
the player entities by an ArchiveXL resource patch and mounted only while the
AnimWrapper variable VAR is raised (scripts/Dioscuri, while Dioscuri is drawn).
Priority 127 beats the Ashura set's 128, and sets override each other by clip
name. This is Meigetsu's route, proven in game since 2026-08-19 (CLAUDE.md):
patch BOTH the ep1 and the base player entities.

Made from Meigetsu's own patch entities (anim-work/player_[wm]a_anim_ext.ent.json)
by replacing its set, variable, component name and id everywhere they appear
(the component list, compiledData and its CruidDict). Writes the JSON sources
to sources/anim_patch/ and the .ent files to archive-staging.

Run: python mesh-work\\build_anim_patch.py
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MEIGETSU = os.path.join(os.path.dirname(ROOT), 'meigetsu', 'anim-work')
WK = r'C:\Users\jtrac\dev\tools\WolvenKit.Console\WolvenKit.CLI.exe'
SRC = os.path.join(ROOT, 'sources', 'anim_patch')
STAGE = os.path.join(ROOT, 'archive-staging', 'Dioscuri', 'mod', 'dioscuri', 'patch')
VAR = 'w_rifle_sniper_dioscuri'
IDS = {'wa': '2026102800000000201', 'ma': '2026102800000000202'}   # unique component ids
MEIGETSU_IDS = {'wa': '1915671175501699984', 'ma': '1915671175501699985'}

os.makedirs(SRC, exist_ok=True)
os.makedirs(STAGE, exist_ok=True)
for g in ('wa', 'ma'):
    s = open(os.path.join(MEIGETSU, 'player_%s_anim_ext.ent.json' % g), encoding='utf-8').read()
    swaps = [
        ('mod\\\\meigetsu\\\\anims\\\\p%s_meigetsu.anims' % g, 'mod\\\\dioscuri\\\\anims\\\\p%s_dioscuri.anims' % g),
        ('w_melee_meigetsu', VAR),
        ('Meigetsu Animation Setup', 'Dioscuri Animation Setup'),
        (MEIGETSU_IDS[g], IDS[g]),
    ]
    for old, new in swaps:
        n = s.count(old)
        assert n >= 2, '%s: %r found %d times' % (g, old, n)
        s = s.replace(old, new)
    assert 'meigetsu' not in s.lower().replace('"archivefilename"', ''), [l for l in s.splitlines() if 'eigetsu' in l][:3]
    src = os.path.join(SRC, 'player_%s_anim_ext.ent.json' % g)
    open(src, 'w', encoding='utf-8').write(s)
    r = subprocess.run([WK, 'convert', 'deserialize', src, '-o', STAGE], capture_output=True, text=True)
    out = os.path.join(STAGE, 'player_%s_anim_ext.ent' % g)
    assert r.returncode == 0 and os.path.exists(out), r.stdout[-1500:]
    print('PATCH', out)
print('BUILD ANIM PATCH DONE')
