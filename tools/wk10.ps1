# WolvenKit 10.0.0-beta.1's CLI on the portable .NET 10 runtime (v0.12.231):
# the first WolvenKit that writes game 2.5's streaming sectors (version 68).
# The build uses it for the four sectors only; everything else stays on 8.20.
$env:DOTNET_ROOT = 'C:\Users\jtrac\dev\tools\dotnet-10.0.14'
& 'C:\Users\jtrac\dev\tools\WolvenKit.Console-10.0.0-beta.1\WolvenKit.CLI.exe' @args
exit $LASTEXITCODE
