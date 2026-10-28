"""Timing chart of the two-round reload (Blender; 2026-10-28).

From the DECODED sets (what the game reads): per variant, the distance of V's
left hand from the breech (the round's seat, in the weapon frame: gun space
with the -90 deg X attach, CLAUDE.md) and the bolt's travel, frame by frame.
Two dips of the hand = two rounds going in; the bolt must be back through both.
Writes ashura-reload/preview/two_round_timing.json for the chart.

Run: & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python chart_two_round_reload.py
"""
import bpy, json, math, os
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.path.join(HERE, 'ashura-reload', 'work', 'two_round')
OUT = os.path.join(HERE, 'ashura-reload', 'preview', 'two_round_timing.json')
CLIPS = ['empty_reload', 'empty_reload_01', 'empty_reload_02']
ATTACH = Matrix.Rotation(math.radians(-90), 4, 'X')
BREECH = Vector((0.0, 0.04, 0.0))   # the round's rest spot (the Ashura mag_std rest, weapon frame)


def load(path):
    before, acts = set(bpy.data.objects), set(bpy.data.actions)
    bpy.ops.io_scene_gltf.cp77(filepath=path, scripting=True, import_tracks=True)
    rig = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
    return rig, {a.name.split('.')[0]: a for a in bpy.data.actions if a not in acts}


def pose(rig, action, f, bones):
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    rig.animation_data_create()
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    return {b: (rig.matrix_world @ rig.pose.bones[b].matrix).copy() for b in bones}


bpy.ops.wm.read_homefile(use_empty=True)
arms, arm_acts = load(os.path.join(TR, 'decoded', 'pwa_dioscuri.anims.glb'))
bolt, bolt_acts = load(os.path.join(TR, 'decoded', 'dioscuri_base1.anims.glb'))
data = {}
for clip in CLIPS:
    rows = []
    rest = None
    for f in range(0, 180):
        p = pose(arms, arm_acts[clip], f, ['arm_right_ik_weapon', 'LeftHand'])
        gun = p['arm_right_ik_weapon'] @ ATTACH
        hand = gun.inverted() @ p['LeftHand'].translation
        b = pose(bolt, bolt_acts[clip], f, ['cocking_mechanism'])['cocking_mechanism'].translation
        rest = rest or b.copy()
        rows.append({'f': f, 'hand_cm': round((hand - BREECH).length * 100, 1), 'bolt_cm': round((b - rest).length * 100, 1)})
    data[clip] = rows
    near = [r['f'] for r in rows if r['hand_cm'] < 12]
    print('%-16s hand within 12 cm of the breech at frames %s' % (clip, near[:1] + ['..'] + near[-1:] if near else []))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(data, open(OUT, 'w'), indent=0)
print('TIMING', OUT)
