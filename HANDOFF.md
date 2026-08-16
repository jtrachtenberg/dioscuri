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

## Historical: resume notes from the cache-case saga (superseded)

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
