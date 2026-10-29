# Malorian Arms Dioscuri — Project Handoff

## STANDING USER RULE (saved to memory, applies to all future work)
If a manual/GUI path is >99% likely to work and the headless path is
unproven, OFFER THE MANUAL PATH FIRST. The sector saga violated this.
Current plan follows it: user runs WolvenKit GUI + Script Manager's
Object Spawner import on their export (walkthrough given in chat 2026-08-16;
export at bin\...\mods\entSpawner\export\malorian_exported.json), packs &
installs from the GUI, tests the vanilla control case. Next session then
injects the Malorian case + loot table into the GENERATED (proven) sector.
Note: auto-grant pragmatic mode was built then REJECTED by user and reverted
— CET mod is cleanup-only (tags DioscuriCache + DioscuriCacheProp).

## ✅ MOD COMPLETE (2026-08-16 ~16:00) — v1.0.0 shipped

Everything works and is user-confirmed in game: weapon (model, twin-lock
burst, stats, tier scaling), lootable Malorian case at the factory site
(native Open prompt + lid animation), level-banded crafting spec drop,
custom matte-black/red materials, tuned gunmetal pipeline, inventory icon
(moody top-lit), HUD holo line-art icon. Repo consolidated + git initialized;
`build.ps1` packs/deploys/produces the Nexus zip (`dist\`). Nexus page copy
in NEXUS-PAGE.md. Key late-stage lessons appended below the original log:

- Loot prompt requires MESH COLLISION: custom meshes need a grafted
  meshMeshParamPhysics (box colliders, both Simple+Complex filters).
- Cooked meshes read externals from preloadExternalMaterials (NOT
  externalMaterials); locals live editable in preloadLocalMaterialInstances.
- Lid animation: gameTransformAnimatorComponent "Open" anim; pivot at the
  lid's measured back-bottom edge, sunk ~1cm into the rim to kill the gap.
- Icon brightness: png→xbm import gamma-LIFTS renders in game; author dark
  (power-curve the pixels, e.g. ^3.0) and keep speculars via curve not multiply.
- HUD icons: Freestyle line art, thin strokes (~1.15px) at native res —
  supersample+downscale merges lines into blobs.
- mlsetup editing: MLSetupBuilder (dev\tools\MLSetupBuilder) — WolvenKit GUI
  shows only hex lookup keys. Export json via CLI serialize, edit, deserialize.
- 65,535 verts/submesh engine cap (double-siding all gunmetal exceeded it).

## Visible rounds (2026-10-28 night): built + deployed as working 1.3.0, NOT yet seen in game

The maintainer, on the published 1.2.0: "there are still no bullet showing in
the chamber". Now each of the two rounds shows: it comes up in V's loading
hand, goes into its slot on top of the receiver, lies there beside the other
round while the bolt is open, and rides the bolt forward into the chamber,
where it is hidden. Preview of the decoded clips:
`mesh-work\ashura-reload\preview\dioscuri_rounds_preview.png` (gitignored;
`study_round_hand.py -- --final`).

- **The parts.** Each round is the Ashura's cartridge mesh on the Ashura's
  3-bone cartridge rig (`mag_std`, `weapon.animgraph`), in an animated
  component of its own (`DioscuriRoundA`/`B`, parented to `DioscuriBolt`).
  Each plays its own set, `mod\dioscuri\anims\dioscuri_round_a/b.anims`
  (the three `empty_reload` clips at 180 frames, `first_equip` held still),
  and both use `mod\dioscuri\meshes\dioscuri_round.mesh`. That mesh is the
  vanilla cartridge with its vertices moved into the chamber, so the rounds
  rest hidden whenever no clip plays (idle, firing). Nothing depends on a
  component `localTransform`, which is unproven in game.
- **Where (gun frame, +Y muzzle, +Z up)**, measured with
  `study_round_hand.py` and a ray test from 200 directions:
  - the chamber, (0, 0.165, 0.072), is hidden from every direction, bolt
    open or closed. It is the rest and the park spot.
  - the slots, x -0.0075 (A) and +0.0075 (B) at y 0.065, are the open
    channel on top of the receiver in front of the open bolt's rear block.
    That is where V's hand delivers and where the rounds read as loaded
    from V's eye. Each slot rides the bolt, so its 10 cm travel carries
    both rounds into the chamber.
- **Which hand loads:** the left in `empty_reload`, the right in `_01`/`_02`
  (the gun turns sideways and the left hand holds it). Male and female V's
  arm clips put the hands in the same place to a micrometre, so one clip
  serves both.
- **Timing, per variant and round** (`build_rounds.py`, from the DECODED arm
  and bolt clips):
  - insert end: the frame near the round's "load" sound where V's
    thumb-index pinch is closest to the slot's rear end. The round is held by
    its base, along the gun's axis at that frame, and fixed to the hand
    before it.
  - the insert: the last 6 frames add the remaining 1.2-2.9 cm.
  - appearance: the jump from the hidden chamber into the hand happens on
    the frame where the hand is furthest outside V's view. That is 7.3 view
    half-widths outside in `empty_reload`, but only 0.5-1.1 in `_01`/`_02`:
    a wide FOV setting might catch a one-frame pop at the screen edge.
- **Why not the Ashura's own cartridge clip:** it is in V's hand only for the
  ~8 frames before its insert (measured). The rest of the time CDPR parks it
  36-78 cm away, out of view. That park spot is what floated below the gun
  in the first try.
- **Pipeline:**
  - `build_rounds.py` (Blender): the poses, the hidden-spot ray test, the
    keys, the GLB gates, and the moved mesh;
  - `finish_rounds.py`: the headless import into copies of the vanilla
    cartridge set (Compressed, fallback indices, every clip rebuilt), and
    the mesh via `import -k`. The bind matrix is restored, and the epsilon
    is 0.3, since the round sits 0.2 m from its bone. The packed mesh is
    then uncooked back and its bounds checked: off by 0.0000 m;
  - `finish_moving_parts.py`: the app components (`--no-rounds` leaves
    them out);
  - the decoded clips vs the authored poses: worst 0.96 mm / 0.14 deg.
- **Traps:** WolvenKit's anims importer counts `int(last key * 30) + 1`
  frames, so a 4.7 s clip comes back 141 frames, not 142. The vanilla
  cartridge set is SIMD; ours is Compressed, as the bolt's is.
- **Deployed** 2026-10-29 04:10 UTC (archive md5 aa9f12f2..., 26 entries).
  Rollback: `.modwright\backups\20261029-041010`, byte-identical to the
  published 1.2.0 archive.
- **In-game check:** reload several times to see all three variants. Look
  for:
  - the round in the hand on the way up;
  - the first round lying in its slot while the second is fetched;
  - both rounds disappearing forward as the bolt closes;
  - no round visible at rest;
  - no pop at the screen edge when a round appears.

## The moving bolt (2026-10-28, working version 1.2.0, NOT published)

The maintainer: "this mod is outside the contest range, can you try an
automated pass at cutting the bolt and getting ashura's animation?" Done
with no cutting at all, because the kitbash took Dioscuri's receiver from the
Ashura's own `base1_01` mesh, untransformed:
- `mesh-work\build_moving_parts.py` (Blender): each vertex of the SHIPPED
  mesh finds its twin on the Ashura (within 0.3 mm) and takes that vertex's
  bone. A connected island moves if at least 90% of its vertices land on a
  moving bone, and everything else goes on `barrel`, which the clips never
  move. Result: `cocking_mechanism` 5,534 vertices, `hammer` 1,147, `l_grip`
  392, `r_grip` 396, `barrel` the rest. 111 islands are 100% moving; 9
  static islands touch the bolt with only 1-2 vertices.
- `mesh-work\finish_moving_parts.py`: `import -k` over 1.1.0's mesh (taken
  from git, commit fdac8c3, so reruns are identical), with the bone data set
  by the GLB's joint order and copied from the Ashura's mesh (`barrel`
  epsilon 1.2 for Dioscuri's 1.13 m reach). Three importer traps are in
  CLAUDE.md, under the `import -k` bullet.
  - The app: it adds `DioscuriBolt` (the Ashura's `Barrel` component: the
    `base1` rig, `weapon.animgraph` and the Ashura's base1 anim sets) under
    Dioscuri's `Receiver`. `dioscuri_body_mesh` becomes an
    `entSkinnedMeshComponent` bound to it (same id, same mesh).
  - Both go into `components` AND `compiledData` (the copy the game reads),
    sharing their binding handles; CruidDict is rebuilt;
    `resolvedDependencies` gains the three base1 anim sets. Both files go
    to `archive-staging`.
  - Then it packs the mesh under a unique name and uncooks it back, the way
    the game reads it.
- `mesh-work\preview_moving_parts.py` (Blender) gates that build: every
  vertex where 1.1.0 has it (0.000000 m), the skin counts, and in
  `empty_reload` `barrel` moves 0.0 mm while the bolt, hammer and grips move
  100 mm. Renders: `ashura-reload\preview\dioscuri_bolt_strip.png`.
- The cartridge (the Ashura's `Magazine` component + its vanilla mesh,
  `finish_moving_parts.py --round`, two of them 1.6 cm apart) was tried in
  game on 2026-10-28 and DROPPED.
  - Dioscuri 1.1.0 shows NO round in a reload. Its `slotPartListPreset` is
    its own (body part + iconic mod, no Magazine part), and parts don't
    paint anyway (lesson 2): only `dioscuri_weapon.app` draws. A first
    reading here, that the rounds come from the Ashura's magazine parts,
    was wrong.
  - The Ashura's own cartridge clip does not keep the round in V's hand.
    Measured offline (`pwa` LeftHand vs the `mag_std` bone, in the gun-space
    weapon frame): while it is out of the gun it is 36-78 cm from the left
    hand in all three variants. Only `empty_reload` brings it to the hand,
    at the insert (7-9 cm, f54-66); `_01`/`_02` never get closer than 13/21
    cm. In game (the maintainer): in the forward reload "the cartridges
    floating in the air just below the gun for a moment".
  - At rest it sat in Dioscuri's trigger guard: the Ashura hides it inside
    its Nekomata receiver, which Dioscuri lacks.
  - Visible rounds need their own cartridge clip, baked from V's left hand
    (a step of its own).
- **Open (the maintainer, 2026-10-28):** "the dioscuri fires two - so it
  needs to put in two rounds". V's reload is the Ashura's arm animation,
  made for its 1-round magazine (`mag 1/1`); Dioscuri holds 2. Showing two
  rounds going in means a different arm reload: authored in the Meigetsu
  animation pipeline, or another weapon family's, which changes all of V's
  handling. The weapon's own clips (bolt timing) would have to match it.

### Two-round reload: CONFIRMED IN GAME 2026-10-28 ("the animation is now perfect")

**Status at the end of 2026-10-28:** the Compressed-bolt build (deployed
18:40 UTC, commits 3edba12 + 1eb8e46) is confirmed by the maintainer: "ok,
the animation is now perfect". Open: "there are still no bullet showing in
the chamber". Visible rounds are the next step: a cartridge component in
`dioscuri_weapon.app` on a clip baked from V's hand (the Ashura's own
cartridge clip strays 36-78 cm from the hand, see the cartridge note
above). Its clips go Compressed, like the bolt's. PUBLISHED as 1.2.0 on
2026-10-28 (redscript now required); the rounds came after it, see
"Visible rounds" at the top.

Built as planned below (commits 3edba12, 1eb8e46):
- `mesh-work\build_two_round_reload.py` (Blender: the cut, seam blend,
  retimed tracks, GLB gate);
- `finish_two_round_reload.py` (headless import into Dioscuri's own sets,
  the gates, sound events: a second `mag_new_grab`/`move_long` and `load`,
  the rest shifted 54 frames);
- `verify_two_round_reload.py` (the decoded clips vs the TIME-MAPPED
  vanilla clips, and vs our export);
- `build_anim_patch.py` (the player-entity patches, made from Meigetsu's);
- `scripts\Dioscuri\Dioscuri_TwoRoundReload.reds` (raises
  `w_rifle_sniper_dioscuri` while a `DioscuriWeapon`-tagged item is in
  WeaponRight);
- yaml: `baseEmptyReloadTime` 3.93 and `EmptyReloadTime` +0.9 (3.0 s, 1.31x);
- modwright.json: a scripts source, a redscript deploy target, the dist
  entry, and redscript as a new requirement.

In game (the maintainer):
- First build: "the entire gun vanished during the reload ... just the
  hands remained". The bolt clips were re-encoded SIMD like vanilla's
  (16-bit, 14 joints); WolvenKit read them back perfectly, the game did not
  (CLAUDE.md lesson).
- A/B (`finish_moving_parts.py --vanilla-bolt-clips`): "the gun stays".
  V's two-round arm clips work, and the second insert plays, but the
  vanilla bolt "snaps shut after the first ... the second one plays but the
  gun is already closed", as expected.
- Now deployed (2026-10-28 18:40 UTC): the bolt clips as a Compressed
  buffer (`preferSIMD` false), decoded within 0.11 mm / 0.005 deg of the
  vanilla motion. NOT yet seen in game. Rollbacks:
  `.modwright\backups\20261028-184008` (the A/B build), `20261028-180119`
  (the first two-round build), `20261028-175210` (bolt only).
- Still no visible rounds (as planned: a later step).

### Two-round reload: research (2026-10-28)

What a reload is made of (all game 2.5, read offline):
- V's arms: `pwa_`/`pma_w_rifle_sniper__tsunami_ashura.anims`, mounted on
  the record's friendlyName `w_rifle_sniper_tsunami_ashura`. Three clips,
  `empty_reload`, `_01`, `_02`, each 4.167 s (126 frames). There is no
  plain `reload`: the Ashura's magazine holds 1.
- The gun: the bolt (`DioscuriBolt`, the Ashura's base1 set). The Ashura
  also has a cartridge (its weapon app's `Magazine` component on the
  mag_std set); Dioscuri has none, see above. All use the same three clip
  names and length.
- Which variant plays: `RandDifferent(previous, 3)` in the weapon PSM's
  reload OnEnter (`weaponTransitions.script`), one index shared by arms
  and gun, never the same twice in a row.
- Speed: the clip plays at `baseEmptyReloadTime / EmptyReloadTime` (the
  Ashura: 2.1 / 2.1 = 1.0). The ammo refills when the logical reload ends
  (2.1 s), which lines up with the "load" sound at 2.13 s; the clip plays
  on to its 4.167 s end.
- The clips carry only sound events (`empty_reload`): move 0.10 s,
  handle_pull 0.67, mag_new_grab 1.37, load 2.13, handle_release 2.83,
  grab 3.67 (`_01`/`_02` within 2 frames; `_01` has move_long instead of
  mag_new_grab).
- The engine's own per-round reload (the Tactician: `ReloadAmount` 1,
  `reload_start`/`reload_loop` clips, `continueLoop` + `RightReloadLoop`)
  runs the loop AFTER the first round is chambered. Dioscuri "chambers a
  pair" (yaml), so the loop would put the second round in after the bolt
  closes. Not this route.

The plan: one longer `empty_reload` per variant:
- Take frames [0..B], then [A..B] again, then [B..125]:
  - A = handle_pull + 7: bolt fully back;
  - B = handle_release - 4: round in, hand still at the breech;
  - A..B is f27..f81 (f29..f83 in `_02`).
- The same time map applies to all four tracks, so they stay in step:
  - V's arms, `pwa` and `pma`;
  - the bolt (back for the whole of A..B);
  - the cartridge: between rounds it jumps from the receiver back to its
    out-of-view spot, where the hand fetches it.
  - Sound events after B shift by 54 frames, and a second mag_new_grab and
    load are added.
- 126 + 54 = 180 frames, 6.0 s. The second round goes in at about 3.9 s.
- The seam B→A, measured: `_01`/`_02` move the gun 3-4 cm and 15 deg, with
  the left hand in the same place on the gun (0 mm); `empty_reload` moves
  it 6 cm and 25 deg, the hand 8 cm. Blend across about 8 frames.
- Dioscuri-only: the arm clips must not change the vanilla Ashura.
  - Recommended: the Meigetsu route. A small extension set holding only the
    three reload clips, gated on a custom AnimWrapper variable that a small
    redscript raises while Dioscuri is drawn. Lower priority number wins,
    sets override by clip name, and both ep1 player ents get patched.
    Proven in Meigetsu.
  - The alternative is a new friendlyName: no script, but every other
    Ashura animation keyed by that name would need copying, third person
    included.
- The gun side: DioscuriBolt points at a Dioscuri copy of the base1 set.
  Visible rounds come later, as their own step: a cartridge component in
  `dioscuri_weapon.app` (parts don't paint) on a clip baked from V's hand.
- The maintainer chose 3.0 s (2026-10-28: "In between: about 3.0 s, the
  animation a bit quicker (1.3x)"). So `baseEmptyReloadTime` 3.93 (the
  second "load" sound's clip time) and `EmptyReloadTime` 3.0, giving speed
  1.31: the ammo lands as the second round goes in.
- Pipeline: the CP77 add-on's importer and the headless anims import
  (aeroboard `tools\wkit-anims-import`), with every gate CLAUDE.md lists:
  numExtraJoints 0, rootMotionType Unknown, fallbackFrameIndices, LINEAR
  keys, the chunk ceiling, the 23 float tracks retimed with the bones.
  Then a Blender preview of arms and gun together before any launch.
- The maintainer's calls: the reload length (the natural pace makes it
  2.1 → 3.9 s; keeping 2.1 s plays it 1.87x; in between, e.g. 3.0 s at
  1.3x), and whether to do all three variants or one.
- **CONFIRMED IN GAME by the maintainer (2026-10-28): "ok the bolt moves".**
  Unattended runs (`soak.py dioreload --turn 180 --only dioscuri`, ModWright)
  showed it loads, fires and reloads cleanly, but could not show the bolt:
  10 cm on a moving gun is lost in the run-to-run sway of a frame diff. Ask
  for eyes on for a small part. Also: Dioscuri's 1.13 m reach puts it in
  the obstructed (raised) pose near a wall, where the Ashura is not, so film
  it in the open (`--turn`).
- Built (ModWright, 18 entries) and deployed 2026-10-28 15:46 UTC. Rollback:
  `.modwright\backups\20261028-154630` (the previous archive, md5 318EB2...).
  `modwright.json` version 1.2.0 so the test zip doesn't overwrite the
  1.1.0 one.

## Game 2.5: "no reload animation" report (2026-10-27) — NOT reproduced

A user reported no reload animation for V on 2.5 (no Possession involved).
Tested unattended with ModWright's soak runner
(`field-probe\launch\cp2077-bridge\soak.py dioreload [--ads]`, research 57):
game 2.5, frameworks on their 2.5 releases, Dioscuri 1.1.0 as published
(same yaml, same archive file list), female V. Each gun was put on wheel
slot 3 and drawn with the 3 key, fired once, and filmed; the vanilla
`Items.Preset_Ashura_Default` (Dioscuri's base) was the control. Runs are
in `cp2077-mods\_soak\20261027-2154*-dioreload` (hip) and
`20261027-215748-dioreload` (aimed).
- Hip fire: both bursts fired (ammo 175 -> 173 -> 171), and the film shows
  the full reload: V tips the rifle, the off hand brings the rounds in, and
  the gun comes back up at 002. The Ashura control does the same at 001.
- Aimed: Dioscuri drops out of the scope, runs the same full reload and
  comes back up. The Ashura matches.
- Possession's reload trace (it logs V's reloads too): V's weapon state
  machine takes the right-hand route on 2.5 (`WeaponRight`, sends
  RightReloadData), and V's hands still animate. Possession's 247 fix
  touches possessed bodies only.

What the offline checks ruled out (all 2.31 vs 2.5):
- the Ashura records and every record Dioscuri inherits are unchanged (the
  only diffs are an `[ EP1 ]` tag and a new blueprint Dioscuri does not use);
- the vanilla Dian `.app`, which `dioscuri_weapon.app` was cloned from, is
  unchanged (same components, rigs, anim sets);
- V's arms pick the reload clips by the record's `friendlyName`
  (`w_rifle_sniper_tsunami_ashura`, inherited), and both
  `player_wa_fpp_ep1.ent` and `player_ma_fpp_ep1.ent` on 2.5 still mount
  the Ashura's arm set (`pwa_`/`pma_w_rifle_sniper__tsunami_ashura.anims`)
  under that name.

Not covered: male V in game (only the entity was checked), Smart Link
installed (this V has none), and a reload with a partly full magazine
(Dioscuri's burst always empties it). Questions for the reporter: does the
vanilla Ashura (or any other gun) animate its reload? Which animation or
weapon mods do they run, and are any 2.31-era builds? Are they playing as a
replacer (a mod that swaps V's body)? That is a guess from Possession, not a
tested link: Possession's replacer bodies on 2.5 refilled the magazine with
the hands frozen (filmed with pistols), because their graph reads the
reload speed under its 2.31 name. V's own graph does not have the problem.

Note on Dioscuri's own mesh: `dioscuri_body_mesh` is a static
`entMeshComponent`, so the gun itself never had moving reload parts (no
bolt or magazine motion), on 2.31 either. If "no reload animation" means
the gun and not the hands, that is by design.

**2026-10-28: that IS what the reporter meant** (the maintainer, in game,
with a vanilla Ashura and a Legendary Dioscuri given through the bridge:
"the hands move the same as the ashura - but the gun parts on the ashura
move when reloaded, but the dioscuri does not"). The maintainer wants to
design moving parts in Blender. Study file, built headlessly:
`mesh-work\ashura-reload\ashura_reload_vs_dioscuri.blend`, made by
`mesh-work\build_ashura_reload_blend.py` (its docstring has the run line).
The folder is gitignored: it holds vanilla assets.
- **How the Ashura's gun moves** (its 2.5 `.app`): three
  `entAnimatedComponent`s, each with its own rig, `weapon.animgraph` and
  anim set, all at one origin (no slot bindings):
  - `Receiver` (root, rig `w_rifle_sniper__rcv1`, mesh: the Nekomata's
    receiver): its anim set has no clips, so the receiver never moves;
  - `Barrel` (rig `..._ashura__base1`, mesh `base1_01` + two diodes): moves
    `cocking_mechanism`, `hammer`, `l_grip`, `r_grip` and `mag_slot`;
  - `Magazine` (rig `..._ashura__mag_std`, mesh `mag_std_01`, which is a
    single 7.5 cm cartridge): moves `magazine`, `mag_std` and `mag_plug`.
  Clips: `empty_reload` (126 frames at 30 fps), `empty_reload_01`, `_02`,
  `first_equip`. In `empty_reload`, the cartridge leaves the receiver by
  ~f9 (to ~0.6 m behind the gun, in V's hand) and is back in by ~f81. The
  bolt (cocking_mechanism with hammer and grips) slides 10 cm back between
  ~f18 and f27, and forward between ~f90 and f99.
- **The blend:** each Ashura mesh is rebound to its anim rig. Each mesh's
  bind pose matches its rig's rest pose exactly (gated, 0.000000 m). All
  three parts play one clip; the text block `set_clip.py` switches them
  together. Dioscuri's `dioscuri_body` (uncooked from the deployed 1.1.0
  archive) is at its in-game origin: the Ashura and Dioscuri share their
  width to the mm and line up along the barrel. Previews:
  `ashura-reload\preview\` (`ashura_strip.png`, `bolt_strip.png`,
  `overlay_dioscuri_red.png`).
- **The route to moving Dioscuri parts, with no new animation:** split the
  moving pieces out of Dioscuri's mesh. Skin them to the Ashura's bone
  names: bolt to `cocking_mechanism`, and a round or magazine to `mag_std`.
  Then give `dioscuri_weapon.app` the matching animated components (rig +
  `weapon.animgraph` + the Ashura's `.anims`), as the Ashura's `.app` does.
  The Ashura's own clips then drive them, in step with V's hands.
- Traps hit building it:
  - `uncook -gp <game> -w '*.mesh'` on ONE mod archive went through EVERY
    game archive (7 GB in 5 minutes, stopped). With `-gp`, the pattern
    must name the file.
  - `--mesh-export-type WithRig` wrote no GLB at all. The default export's
    skins carry the real bone names, which is all a rebind needs.
  - The Cyberpunk add-on dies building the magazine's multilayer material
    (its `.mlsetup` was not uncooked). The script falls back to Blender's
    standard glTF importer for meshes only (plain material); `.anims`
    always go through the add-on.

**What the user did next** (resolved — Option B injection worked):
1. In Object Spawner window: despawn/delete their placed suitcase + the
   "Malorian" group (else the tool respawns an unlootable copy on top).
2. Launch, walk to the site (their placed spot: -835.76, 328.63, 7.88).
3. Report: which of the TWO cases renders, and which (if either) LOOTS.
   - Node 0 = our custom Malorian case; Node 1 = vanilla suitcase control
     (+1.5m x, neomilitary appearance), both with loot instanceData.

**Decision tree on their report**:
- Both render, control loots, ours doesn't → bug is in our custom
  cache_case.ent (bisect: animator removal / appearance chain / meshes).
  Fallback: ship vanilla-shell container with our loot + our case as an
  adjacent prop.
- Both render + both loot → DONE: remove control node from build_sector.py,
  rebuild, reship. Project complete.
- Still invisible/unlootable → STOP hand-authoring. Next: run the user's
  export (bin\...\mods\entSpawner\export\malorian_exported.json) through
  WolvenKit GUI's official entSpawner import script (Script Manager) and
  diff its generated sector against ours; or ask CP77 modding discord.
  Also available: the pragmatic close — CET-spawned visible case + proximity
  auto-grant (mechanism previously proven working; user preferred real loot).

**Key learnings this final stretch** (already applied in build_sector.py):
- entSpawner (worldBuilder 1.0.81) installed from GitHub (old install was a
  hollow Vortex skeleton — same disease as SilentSilencersAndKnives).
- Its export = recipe JSON, not a sector; revealed: sector+descriptor
  category "Exterior" level 1 (NOT AlwaysLoaded/0); node appearanceName must
  be the appearance's FULL NAME (e.g. suitcase_small_neomilitary_a) — a
  wrong/unresolvable name spawns an INVISIBLE entity (explains all the
  invisible-with-loot-ping symptoms); streaming fields were already right.
- Sector JSON: HandleIds AND BufferIds must be unique file-wide.
- The "case was always open" saga: the vanilla gun-case meshes are AUTHORED
  open, exterior-up. Closing = 180° spin about Z + translate onto bottom
  (build_cache_lid.py; plaque placed by raycast — vertex sampling fails on
  large flat faces).
- The visible cases in early screenshots were legacy DYNAMIC spawns (now
  auto-cleaned every 3s by the CET script); hand-built sector entities had
  never rendered.

CP2077 weapon mod built 2026-08-15 with Claude. A custom iconic smart sniper
("Malorian Arms Dioscuri") with kitbashed mesh, lore, icon, and a world-placed
treasure-hunt acquisition. Read this top to bottom before touching anything.

## EXPORT-RECIPE BUILD (latest — read this first)

entSpawner (worldBuilder v1.0.81, installed from GitHub after discovering the
old install was a hollow Vortex skeleton) was used by the user to place a
vanilla suitcase in-game and export project "malorian". The export JSON
(bin\...\mods\entSpawner\export\malorian_exported.json) is entSpawner's
RECIPE format, not a final sector — but it revealed the likely invisibility
causes in my hand-built sectors:
- sector/descriptor category should be "Exterior" level 1 (mine was
  AlwaysLoaded/0);
- node appearanceName must be the appearance's full NAME
  (e.g. "suitcase_small_neomilitary_a"), not "default" — wrong name = entity
  spawns INVISIBLE (matches the invisible-with-loot-ping symptom);
- nodeData streaming fields (MaxStreamingDistance 120/UkFloat1 100/
  Uk10 1056/Uk11 512) already matched.
build_sector.py now builds from the export's values: user-placed position
(-835.758, 328.628, 7.884) + rotation (k .75299, r .65803), Exterior/level 1,
streamingBox from export, control node with proper appearance name. Deployed
(archive queued behind game lock). Both our case (node 0) and vanilla control
(node 1, +1.5m x) carry the loot instanceData.
Remaining alternative if still broken: run the export through WolvenKit GUI's
official entSpawner import script (Script Manager) and diff its sector
against ours.

## CONTROL EXPERIMENT (prior build)

The sector now contains TWO nodes at the site:
1. **Our custom case** at (-838.7, 324.8, 7.9) — lid now correctly closed
   EXTERIOR-UP (the vanilla gun-case meshes are authored open with exterior
   facing up, so closing = spin 180° about Z + translate onto bottom — the
   earlier X-axis fold put it exterior-down/upside-down).
2. **CONTROL: untouched vanilla common_suitcase_small.ent** 1.5m east
   (-837.2, 324.8, 7.9) with identical instanceData loot config.

Outcome decision tree:
- Control loots, ours doesn't → our custom .ent is broken (bisect its edits:
  animator removal? appearance chain? custom meshes' collision?). Consider
  shipping the vanilla-shell container with our loot as a fallback.
- Neither loots → sector instanceData insufficient for interactions;
  data-side exhausted → redscript instrumentation or community help.
- Both loot → DONE (remove the control node and reship).
Sector JSON gotchas learned: HandleIds AND BufferIds must be unique across
the whole file (duplicate BufferId "1" broke deserialization at the second
node; error message is a useless generic JsonException at the buffer's
closing brace).

## Current status (end of session)

**Everything is deployed (final build ~22:45).** Awaiting user verification of
the cache case. This build has ALL known fixes:

1. **Case meshes now CLOSED**: the vanilla gun-case meshes are authored lying
   OPEN (lid folded back flat — every earlier "case is already open" report
   was the mesh pose, not state!). build_cache_lid.py now FLIPS the lid 180°
   and seats it on the bottom via bbox math; plaque placed by RAYCAST
   (vertex-sampling fails on large flat faces — recurring trap).
2. **Sector node has instanceData** (per wiki "Lootable world objects" +
   verified against a WORKING modded ShardCaseContainer node from
   AldecaldosHighStakes — template saved at
   mesh-work\templates\reference_container_sector.json): complete
   LootContainerObjectAnimatedByTransform chunk with lootTables
   [LootTables.DioscuriCacheLoot], lootQuality Legendary, displayName
   LocKey#Dioscuri-Cache-Name. NOTE: chunk built by ADAPTING the reference
   chunk (our ent-derived chunk had some field the RedPackage JSON reader
   rejects — bisected but exact field not identified; use the reference-based
   builder in build_sector.py).
3. Loot table yaml matches wiki exactly ($type gamedataLootTable_Record,
   lootGenerationType dropChance, gamedataLootItem_Record entries).
4. CET mod = continuous cleanup of legacy dynamic cases (every 3s).

If STILL not lootable after this: data-side options are exhausted — next is
redscript instrumentation or community help (CP77 modding discord).

## The weapon (fully working, user-confirmed in game)

- **Record**: `Items.Preset_Dioscuri` (TweakXL). Base = `Items.Preset_Ashura_Default`.
- Twin smart-lock (hip+ADS 2 targets), **true 2-round burst** per pull
  (TriggerMode.Burst primary, NumShotsInBurst +2, CycleTime_Burst +0.06) —
  fires 2, consumes 2, mag = 2 (twin chambers). Integral silencer
  (WeaponNoise −10, CanSilentKill +1 **on the weapon record** — StealthRunner's
  detection patch scans record statModifiers), +400% headshot (+2.5 additive),
  velocity 100, +25% smart reticle, −10.4% DamagePerHit (twin-shot tradeoff,
  calibrated so Tier 5 shows 333 dmg).
- **Progression-correct iconic**: quality Random + CraftableIconicQualityRandomisation,
  tiered craftables `Items.$(tier)_Dioscuri` + recipes with hideOnItemsAdded.
  The cache grants ONE spec: `Items.Recipe_Preset_Dioscuri` (crafts at player level).
- **Visuals**: custom kitbash mesh `mod\dioscuri\meshes\dioscuri_body.mesh` —
  Ashura sniper frame + Malorian 3516 grip/trigger section, both-side
  MALORIAN wordmark + 4/3 dot logo + "MALORIAN ARMS NIGHT CITY" lettering
  (extruded geometry). Painted via **weapon-level app** `mod\dioscuri\dioscuri_weapon.app`
  (appearanceResourceName: Dioscuri_Weapon → factory csv). CRITICAL LESSON:
  weapon visuals come from the weapon-level .app resolved via
  appearanceResourceName + factory — slotPartListPreset parts do NOT paint the gun.
- Materials: mesh imported over the Malorian 3516 mesh as donor →
  chunkMaterials [pasted__malorian_ml_base, malorian_ml_handle2 (red grip),
  pasted__malorian_ml_base].
- **Icon**: custom (rendered from the model) — `UIIcon.DioscuriIcon` →
  mod\dioscuri\icons.inkatlas (declared HD_1280_720, part = centered
  0.2656..0.7344 × 0.3555..0.6445 = 600×208 effective px) → dioscuri_icon.xbm.
- **Name/lore**: ArchiveXL onscreens (mod\dioscuri\en-us.json): Dioscuri-Name
  ("Malorian Arms Dioscuri"), -Description (Eran Malor dead-twin lore),
  -Mod-Description, -Gameplay-Description, -Cache-Name ("Malorian Arms Case").

## The cache (final architecture)

- **World object via ArchiveXL streaming sector** (NOT dynamic spawn):
  - `mod\dioscuri\dioscuri.streamingsector` — one worldEntityNode →
    `mod\dioscuri\cache_case.ent`, nodeData entry at **(-838.7, 324.8, 7.9)**
    (user-calibrated: old Malorian factory site, City Center NE waterfront).
  - `mod\dioscuri\dioscuri.streamingblock` — one AlwaysLoaded descriptor.
  - Registered in Dioscuri.archive.xl under `streaming: blocks:`.
- `cache_case.ent` = clone of common_suitcase_small.ent (LootContainerObjectAnimatedByTransform)
  with: **lootTables = [LootTables.DioscuriCacheLoot]** (THE spawn-seeding field;
  contentAssignment alone insufficient), lootQuality Legendary,
  displayName LocKey#Dioscuri-Cache-Name, appearance → cache_case.app.
- `cache_case.app` = suitcase_small.app default appearance, lid → custom
  `meshes\cache_case_top.mesh` (gun-case top + embossed MALORIAN plaque in
  the lid inset at (0, 0.20, z0.099); Constitutional Arms decal quads DELETED),
  box → custom `meshes\cache_case_bottom.mesh` (pistol submesh_02 removed —
  empty twin foam cutouts), + handle. **TransformAnimator REMOVED** (its
  open-pose floats our longer lid — case stays closed permanently).
- `LootTables.DioscuriCacheLoot` (in dioscuri.yaml): min/max 1, guaranteed
  Recipe_Preset_Dioscuri.
- CET mod `DioscuriCache` = **cleanup only**, running CONTINUOUSLY every 3s
  (one-shot cleanup missed late-streaming persistent entities → two overlapping
  cases, neither lootable). Deletes tag "DioscuriCache" dynamic entities.
  `GetMod("DioscuriCache").Status()`.
  Moving the case now = edit X/Y/Z in mesh-work\build_sector.py → rebuild →
  repack (no more SetHere).

## File map

- Project: `C:\Users\jtrac\dev\cp2077-mods\dioscuri\`
  - `r6\tweaks\Dioscuri\dioscuri.yaml` — ALL TweakDB (weapon, part, recipes, loot table, UIIcon)
  - `archive-staging\Dioscuri\mod\dioscuri\` — archive payload (apps, ent, meshes, csv, inkatlas, xbm, en-us.json, sector, block)
  - `archive-staging\Dioscuri.archive.xl` — localization + factories + streaming
  - `en-us.source.json` — editable localization source (W2RC json)
  - `cet\DioscuriCache\init.lua` — cleanup script source
  - `mesh-work\` — all Blender/CLI pipeline scripts + source GLBs + renders
    - kitbash_v22.py = CANONICAL weapon kitbash (earlier versions historical)
    - export_game_mesh.py, edit_mesh_materials.py — weapon mesh pipeline
    - build_cache_lid.py, build_cache_bottom.py, build_cache_entity.py,
      build_sector.py, render_case_preview.py, render_icon.py, build_inkatlas.py
    - `source\` — uncooked vanilla assets (meshes, apps, factories, tweak templates)
- Game deploys: `r6\tweaks\Dioscuri\`, `archive\pc\mod\Dioscuri.archive(+.xl)`,
  `bin\x64\plugins\cyber_engine_tweaks\mods\DioscuriCache\`
- Tools: WolvenKit GUI + **WolvenKit.CLI** at `C:\Users\jtrac\dev\tools\WolvenKit.Console\`;
  Blender 5.1 (`C:\Program Files\Blender Foundation\Blender 5.1\blender.exe`)
  with Cyberpunk IO Suite 2.0.0 installed.

## Pipelines (rebuild anything)

- **Weapon mesh**: blender --background --python kitbash_v22.py (saves
  dioscuri_kitbash.blend) → export_game_mesh.py (3 submeshes, UVs, tris,
  tangents → dioscuri_body.glb) → copy Malorian donor mesh as
  mesh-import\dioscuri_body.mesh → `CLI import <glb> -o <dir> --keep` →
  `CLI convert serialize` → edit_mesh_materials.py → `convert deserialize` →
  copy to staging → pack.
- **Case meshes**: build_cache_lid.py / build_cache_bottom.py → import over
  gun_suitcase_top/bottom.mesh donors → fix_case_mats (scratchpad) →
  deserialize → stage. Entities: build_cache_entity.py → deserialize both.
  Sector: build_sector.py → deserialize both.
- **Localization**: edit en-us.source.json → copy to staging as en-us.json.json
  → `convert deserialize` → pack.
- **Pack/deploy**: `CLI pack archive-staging\Dioscuri -o archive-staging` →
  copy .archive+.xl to game (if game running, background retry loop —
  archive locked while game runs). yaml copies freely; TweakXL.Reload() in
  CET console hot-reloads yaml; archives need game restart.

## Hard-won lessons (do not relearn)

1. Ground truth for TweakDB = `tools\redmod\tweaks\` vanilla sources (2,684 files).
2. Weapon visuals = weapon-level .app via appearanceResourceName+factory. Parts don't paint.
3. Item tier badge = Quality STAT ×2 (EffectiveTier); `quality:` field only seeds loot rolls.
4. Damage on Ashura: panel derives from DPS/DamagePerHit interplay — calibrate
   empirically (DamagePerHit −0.25→278@T5, −0.104→333).
5. WolvenKit GLB import needs triangulated+tangents(+UVs) and **ignores node
   transforms** — transform_apply(location=True,...) before export. GLBs from
   WolvenKit contain a junk 2m Icosphere — delete it.
6. CR2W JSON: enums are STRINGS ("Always"); .app/.ent need `extract` not `uncook`;
   `obj.dimensions` is zero on fresh Blender FONT objects (measure via
   evaluated_get().to_mesh()).
7. CET mods are sandboxed — console access via `GetMod("name")`, init.lua must return a table.
8. Dynamically spawned loot containers DO NOT interact properly. Use streaming sectors.
9. Never regex-derive script versions — values silently fail to match (v20/v21
   dot bug). Use the Edit tool on copies.
10. Icon atlases: displayed size = UV fraction × declared textureResolution
    (valid enums: HD_1280_720, FullHD_1920_1080, UltraHD_3840_2160).
11. PowerShell guard blocks Remove-Item chained near certain quoted strings —
    run Remove-Item in separate commands.

## Immediate next steps

1. User tests world-sector case (launch → cleanup runs → walk to site).
2. If prompt works: DONE. Optional polish: readme + Nexus packaging (structure
   is ready), case orientation tweak (rotate via Orientation quaternion in
   build_sector.py if it clips the wall), gameplay tuning passes.
3. If case missing: debug sector (compare vs LizziesBDs template; check
   ArchiveXL log for streaming errors: red4ext\plugins\ArchiveXL\ArchiveXL-*.log).
4. If case present but unlootable: engine-level; consider redscript or accept
   CET auto-grant fallback (worked previously; user preferred real loot).
