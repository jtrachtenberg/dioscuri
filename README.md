# Malorian Arms Dioscuri

A custom iconic smart sniper rifle mod for Cyberpunk 2077 — built from scratch as a
kitbash of the Tsunami Ashura and the Malorian 3516, with its own lore, world
placement, and acquisition.

> *Before the 3516 ever bore Johnny Silverhand's name, Eran Malor chased a
> stranger obsession: a rifle that fired in pairs. Factory rumor said it was for
> the twin brother who died in infancy — one trigger, two rounds, so no shot
> would ever be alone. The Dioscuri never shipped. One case survived the
> factory's closing.*

## Features

- **Twin-lock smart targeting** — locks up to two targets simultaneously, fires a
  2-round burst (both rounds real: two chambers, two locks, one pull)
- **Integral suppressor** — silenced, no ricochet, supports stealth takedown bonuses
- **Iconic scaling** — drops as a crafting spec whose tier follows player level,
  exactly like vanilla iconics; 250% headshot multiplier, tuned damage, +25%
  smart reticle, faster projectiles
- **Custom model** — Ashura/Malorian kitbash with engraved MALORIAN ARMS wordmark
  and dot logo, red grip, matte-black hoses and fittings, and the Overwatch
  suppressor; custom inventory icon and HUD holo outline
- **World acquisition** — a lootable Malorian gun case at the old Malorian factory
  site on the City Center NE waterfront (≈ -836, 329) containing the spec

## Requirements

- [RED4ext](https://www.nexusmods.com/cyberpunk2077/mods/2380)
- [ArchiveXL](https://www.nexusmods.com/cyberpunk2077/mods/4198)
- [TweakXL](https://www.nexusmods.com/cyberpunk2077/mods/4197)

## Repository layout

| Path | What |
|---|---|
| `archive-staging/Dioscuri/` | Everything packed into `Dioscuri.archive` (meshes, apps, sector, icons, materials, localization) |
| `archive-staging/Dioscuri.archive.xl` | ArchiveXL manifest (localization, factories, streaming block) |
| `r6/tweaks/Dioscuri/dioscuri.yaml` | All TweakDB records (weapon, iconic mod, recipes, loot table, icons) |
| `mesh-work/` | Blender working files + the scripted asset pipeline |
| `mesh-work/dioscuri_kitbash_edit.blend` | **The editable model** — parts as separate objects |
| `mesh-work/export_game_mesh_v2.py` | Join-by-material → GLB export (submesh order, transforms, doubling) |
| `mesh-work/render_icon_v2.py` | Inventory icon render (moody top-lit pass + gamma curve) |
| `sources/` | Editable JSON sources for shipped binaries (sector, materials, case entity, icons) |
| `cet/DioscuriCache/` | Author-only CET cleanup for legacy dev spawns — **not shipped** |
| `build.ps1` | Pack → deploy (→ dist zip with `-Dist`) |
| `HANDOFF.md` | Full build history, lessons, and pipeline documentation |

Vanilla game extracts (`mesh-work/source/` etc.) are gitignored — regenerate with
WolvenKit CLI `uncook`/`extract` if needed.

## Building

```powershell
.\build.ps1                 # pack + deploy to game
.\build.ps1 -Export         # after editing the .blend: re-export mesh first
.\build.ps1 -Dist           # also produce the Nexus/Vortex zip in dist\
```

Blender 5.1 + Cyberpunk IO Suite, and WolvenKit CLI 8.20 are expected at the
paths in `build.ps1`.

## Credits

- CD PROJEKT RED — base game assets (Ashura, Malorian 3516, Grad suppressor, gun case)
- WolvenKit, TweakXL, ArchiveXL, MLSetupBuilder teams
- Built with Claude (Anthropic)
