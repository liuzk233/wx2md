param(
    [Parameter(Mandatory = $true)]
    [string]$Url,

    [string]$OutputDir
)

$ErrorActionPreference = "Stop"

if ($Url -notlike "*mp.weixin.qq.com*") {
    throw "Invalid URL: wx2md only supports mp.weixin.qq.com article links."
}

$skillRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$exePath = Join-Path $skillRoot "bin\wx2md-cli.exe"
if (-not (Test-Path -LiteralPath $exePath)) {
    throw "wx2md-cli.exe not found at $exePath. Put wx2md-cli.exe in the skill bin directory."
}

$configDir = Join-Path $env:APPDATA "wx2md-skill"
$configPath = Join-Path $configDir "config.json"

function Save-OutputDir {
    param([string]$Path)

    if (-not [System.IO.Path]::IsPathRooted($Path)) {
        throw "OutputDir must be an absolute Windows path."
    }

    $resolved = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
    New-Item -ItemType Directory -Force -Path $resolved | Out-Null
    New-Item -ItemType Directory -Force -Path $configDir | Out-Null

    $config = @{ output_dir = $resolved } | ConvertTo-Json -Depth 3
    Set-Content -LiteralPath $configPath -Value $config -Encoding UTF8
    return $resolved
}

function Load-OutputDir {
    if (-not (Test-Path -LiteralPath $configPath)) {
        throw "No wx2md output directory is configured. Ask the user for an absolute output path, then rerun this script with -OutputDir."
    }

    $config = Get-Content -LiteralPath $configPath -Encoding UTF8 | ConvertFrom-Json
    if (-not $config.output_dir) {
        throw "wx2md config is missing output_dir. Ask the user for an absolute output path, then rerun this script with -OutputDir."
    }

    return (Save-OutputDir -Path $config.output_dir)
}

if ($OutputDir) {
    $targetOutputDir = Save-OutputDir -Path $OutputDir
} else {
    $targetOutputDir = Load-OutputDir
}

Write-Output "wx2md output directory: $targetOutputDir"

$processOutput = & $exePath $Url -o $targetOutputDir 2>&1
$exitCode = $LASTEXITCODE
$processOutput | ForEach-Object { Write-Output $_ }

if ($exitCode -ne 0) {
    throw "wx2md-cli.exe failed with exit code $exitCode."
}

$articlePath = $processOutput |
    Select-String -Pattern '^\s*输出:\s*(.+)$' |
    Select-Object -Last 1 |
    ForEach-Object { $_.Matches[0].Groups[1].Value.Trim() }

if ($articlePath) {
    Write-Output "article.md: $articlePath"
}
