# Package dist\JATIC-Library as a beta zip for testing.
param(
    [string]$Version = "0.1.0-beta.1"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$DistDir = Join-Path $Root "dist\JATIC-Library"
$OutDir = Join-Path $Root "dist"
$ZipName = "JATIC-Library-$Version-win64.zip"
$ZipPath = Join-Path $OutDir $ZipName

if (-not (Test-Path (Join-Path $DistDir "JATIC-Library.exe"))) {
    Write-Error "Build first: .\build.bat (output: dist\JATIC-Library\)"
}

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

Compress-Archive -Path $DistDir -DestinationPath $ZipPath -CompressionLevel Optimal
$sizeMb = [math]::Round((Get-Item $ZipPath).Length / 1MB, 1)
Write-Host "Created: $ZipPath ($sizeMb MB)"
