# Build + deploy the Dioscuri mod.
#   .\build.ps1              pack archive and deploy everything to the game
#   .\build.ps1 -Export      re-export the Blender model first (after mesh edits)
#   .\build.ps1 -Dist        also produce dist\MalorianArmsDioscuri-<ver>.zip for Nexus/Vortex
param(
    [switch]$Export,
    [switch]$Dist,
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"
$proj    = $PSScriptRoot
$cli     = "C:\Users\jtrac\dev\tools\WolvenKit.Console\WolvenKit.CLI.exe"
$blender = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
$game    = "C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077"

if ($Export) {
    Write-Host "== Blender export (join + GLB) =="
    & $blender --background --python "$proj\mesh-work\export_game_mesh_v2.py"
    Write-Host "== WolvenKit import over game mesh =="
    Copy-Item "$proj\mesh-work\dioscuri_body.glb" "$proj\mesh-work\mesh-import\dioscuri_body.glb" -Force
    & $cli import "$proj\mesh-work\mesh-import\dioscuri_body.glb" -o "$proj\mesh-work\mesh-import" -k
    Copy-Item "$proj\mesh-work\mesh-import\dioscuri_body.mesh" "$proj\archive-staging\Dioscuri\mod\dioscuri\meshes\dioscuri_body.mesh" -Force
}

Write-Host "== Pack archive =="
& $cli pack "$proj\archive-staging\Dioscuri" -o "$proj\archive-staging" -v Minimal

Write-Host "== Deploy to game =="
Copy-Item "$proj\archive-staging\Dioscuri.archive" "$game\archive\pc\mod\Dioscuri.archive" -Force
Copy-Item "$proj\archive-staging\Dioscuri.archive.xl" "$game\archive\pc\mod\Dioscuri.archive.xl" -Force
Copy-Item "$proj\r6\tweaks\Dioscuri\dioscuri.yaml" "$game\r6\tweaks\Dioscuri\dioscuri.yaml" -Force
Write-Host "Deployed."

if ($Dist) {
    Write-Host "== Dist zip =="
    $stage = "$proj\dist\_stage"
    if (Test-Path $stage) { Remove-Item $stage -Recurse -Force -Confirm:$false }
    New-Item -ItemType Directory -Force "$stage\archive\pc\mod", "$stage\r6\tweaks\Dioscuri" | Out-Null
    Copy-Item "$proj\archive-staging\Dioscuri.archive"    "$stage\archive\pc\mod\"
    Copy-Item "$proj\archive-staging\Dioscuri.archive.xl" "$stage\archive\pc\mod\"
    Copy-Item "$proj\r6\tweaks\Dioscuri\dioscuri.yaml"    "$stage\r6\tweaks\Dioscuri\"
    $zip = "$proj\dist\MalorianArmsDioscuri-$Version.zip"
    if (Test-Path $zip) { Remove-Item $zip -Force -Confirm:$false }
    Compress-Archive -Path "$stage\archive", "$stage\r6" -DestinationPath $zip
    Remove-Item $stage -Recurse -Force -Confirm:$false
    Write-Host "Built $zip"
}
