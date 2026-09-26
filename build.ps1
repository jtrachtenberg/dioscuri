# Build + deploy the Dioscuri mod.
#   .\build.ps1              pack archive and deploy everything to the game
#   .\build.ps1 -Export      re-export the Blender model first (after mesh edits)
#   .\build.ps1 -Dist        also produce dist\MalorianArmsDioscuri-<ver>.zip for Nexus/Vortex
#   .\build.ps1 -TweaksOnly  deploy dioscuri.yaml only (no pack; game may be running,
#                            then TweakXL.Reload() in the CET console)
# <ver> defaults to modwright.json's "version". Tool and game paths can be
# overridden with $env:WOLVENKIT_CLI, $env:BLENDER and $env:CP2077_DIR.
# Every existing game file is copied to dist\backup\<timestamp>\ before it is
# overwritten.
param(
    [switch]$Export,
    [switch]$Dist,
    [switch]$TweaksOnly,
    [string]$Version
)

$ErrorActionPreference = "Stop"
if (-not $PSScriptRoot) { throw "Run build.ps1 as a script file (.\build.ps1), not pasted into a console." }
$proj    = $PSScriptRoot
$cli     = if ($env:WOLVENKIT_CLI) { $env:WOLVENKIT_CLI } else { "C:\Users\jtrac\dev\tools\WolvenKit.Console\WolvenKit.CLI.exe" }
$blender = if ($env:BLENDER)       { $env:BLENDER }       else { "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" }
$game    = if ($env:CP2077_DIR)    { $env:CP2077_DIR }    else { "C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077" }
if (-not $Version) { $Version = (Get-Content "$proj\modwright.json" -Raw | ConvertFrom-Json).version }
if ($TweaksOnly -and ($Export -or $Dist)) { throw "-TweaksOnly cannot be combined with -Export or -Dist." }

# Native tools don't trip $ErrorActionPreference, and Blender exits 0 when its
# --python script raises unless told otherwise, so check every exit code.
function Invoke-Tool([string]$step, [string]$exe, [string[]]$toolArgs) {
    & $exe @toolArgs
    if ($LASTEXITCODE -ne 0) { throw "$step failed (exit code $LASTEXITCODE)" }
}
# A tool can also exit 0 having written nothing: require a fresh output file.
function Assert-Fresh([string]$step, [string]$file, [datetime]$since) {
    if (-not (Test-Path $file) -or (Get-Item $file).LastWriteTime -lt $since) {
        throw "$step did not produce $file"
    }
}

$deploy = @(
    @{ From = "$proj\r6\tweaks\Dioscuri\dioscuri.yaml"; To = "$game\r6\tweaks\Dioscuri\dioscuri.yaml" }
)
if (-not $TweaksOnly) {
    $deploy = @(
        @{ From = "$proj\archive-staging\Dioscuri.archive";    To = "$game\archive\pc\mod\Dioscuri.archive" },
        @{ From = "$proj\archive-staging\Dioscuri.archive.xl"; To = "$game\archive\pc\mod\Dioscuri.archive.xl" }
    ) + $deploy
    # the running game locks the .archive; fail before anything is built or copied
    if (Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue) {
        throw "Cyberpunk 2077 is running and locks Dioscuri.archive. Quit the game, or use -TweaksOnly."
    }
}

if ($Export) {
    Write-Host "== Blender export (join + GLB) =="
    $glb = "$proj\mesh-work\dioscuri_body.glb"
    $t = Get-Date
    Invoke-Tool "Blender export" $blender @("--background", "--python-exit-code", "1",
        "--python", "$proj\mesh-work\export_game_mesh_v2.py", "--", $glb)
    Assert-Fresh "Blender export" $glb $t
    Write-Host "== WolvenKit import over game mesh =="
    Copy-Item $glb "$proj\mesh-work\mesh-import\dioscuri_body.glb" -Force
    $t = Get-Date
    Invoke-Tool "WolvenKit import" $cli @("import", "$proj\mesh-work\mesh-import\dioscuri_body.glb", "-o", "$proj\mesh-work\mesh-import", "-k")
    Assert-Fresh "WolvenKit import" "$proj\mesh-work\mesh-import\dioscuri_body.mesh" $t
    Copy-Item "$proj\mesh-work\mesh-import\dioscuri_body.mesh" "$proj\archive-staging\Dioscuri\mod\dioscuri\meshes\dioscuri_body.mesh" -Force
}

if (-not $TweaksOnly) {
    # build_*.py write *.json intermediates into the staging tree; only the
    # localization resource (a cooked CR2W file named en-us.json) belongs in the archive
    $strays = @(Get-ChildItem "$proj\archive-staging\Dioscuri" -Recurse -File -Filter *.json | Where-Object Name -ne "en-us.json")
    if ($strays) { throw "Stray .json in archive-staging would be packed: $($strays.FullName -join ', ')" }

    Write-Host "== Pack archive =="
    $archive = "$proj\archive-staging\Dioscuri.archive"
    if (Test-Path $archive) { Remove-Item $archive -Force }
    $t = Get-Date
    Invoke-Tool "WolvenKit pack" $cli @("pack", "$proj\archive-staging\Dioscuri", "-o", "$proj\archive-staging", "-v", "Minimal")
    Assert-Fresh "WolvenKit pack" $archive $t
}

Write-Host "== Deploy to game =="
$backup = "$proj\dist\backup\$(Get-Date -Format yyyyMMdd-HHmmss)"
foreach ($f in $deploy) {
    if (Test-Path $f.To) {
        $rel = $f.To.Substring($game.Length).TrimStart('\', '/')
        $dest = Join-Path $backup $rel
        New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
        Copy-Item $f.To $dest -Force
    }
}
if (Test-Path $backup) { Write-Host "Backed up previous game files to $backup" }
foreach ($f in $deploy) {
    New-Item -ItemType Directory -Force (Split-Path $f.To) | Out-Null
    Copy-Item $f.From $f.To -Force
}
Write-Host "Deployed."

if ($Dist) {
    Write-Host "== Dist zip =="
    $stage = "$proj\dist\_stage"
    if (Test-Path $stage) { Remove-Item $stage -Recurse -Force -Confirm:$false }
    New-Item -ItemType Directory -Force "$stage\archive\pc\mod", "$stage\r6\tweaks\Dioscuri" | Out-Null
    Copy-Item "$proj\archive-staging\Dioscuri.archive"    "$stage\archive\pc\mod\"
    Copy-Item "$proj\archive-staging\Dioscuri.archive.xl" "$stage\archive\pc\mod\"
    Copy-Item "$proj\r6\tweaks\Dioscuri\dioscuri.yaml"    "$stage\r6\tweaks\Dioscuri\"
    $zip = Join-Path (Convert-Path "$proj\dist") "MalorianArmsDioscuri-$Version.zip"
    if (Test-Path $zip) { Remove-Item $zip -Force -Confirm:$false }
    # ZipFile writes '/' entry separators; Windows PowerShell 5.1's
    # Compress-Archive writes '\', which some Linux/Proton mod managers reject
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::CreateFromDirectory((Convert-Path $stage), $zip)
    Remove-Item $stage -Recurse -Force -Confirm:$false
    Write-Host "Built $zip"
}
