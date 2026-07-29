param(
    [string]$UnityPath = $env:UNITY_EDITOR_PATH,
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
$projectPath = [IO.Path]::GetFullPath($PSScriptRoot)

if ([string]::IsNullOrWhiteSpace($UnityPath)) {
    $candidatePaths = @(
        "C:\tmp\unity-6000.0.65f1\Editor\Unity.exe",
        "C:\Program Files\Unity\Hub\Editor\6000.0.65f1\Editor\Unity.exe",
        "C:\Program Files\Unity\Editor\Unity.exe"
    )
    $UnityPath = $candidatePaths |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1
}

if ([string]::IsNullOrWhiteSpace($UnityPath) -or
    -not (Test-Path -LiteralPath $UnityPath)) {
    throw "Unity 6000.0.65f1 was not found. Install Unity with Web Build Support or set UNITY_EDITOR_PATH."
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $projectPath "dist"
}
$OutputPath = [IO.Path]::GetFullPath($OutputPath)
$env:NIMING_UNITY_OUTPUT = $OutputPath

$logPath = Join-Path $projectPath "Logs\web-build.log"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $logPath) | Out-Null

& $UnityPath `
    -batchmode `
    -quit `
    -accept-apiupdate `
    -projectPath $projectPath `
    -buildTarget WebGL `
    -executeMethod NimingDalong.Editor.WebBuild.Build `
    -logFile $logPath

if ($LASTEXITCODE -ne 0) {
    throw "Unity Web build failed with exit code $LASTEXITCODE. See $logPath"
}

Write-Host "Unity Web build completed: $OutputPath"
