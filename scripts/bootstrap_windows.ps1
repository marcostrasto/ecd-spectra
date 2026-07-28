[CmdletBinding()]
param(
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$repository = "marcostrasto/ecd-spectra"
$pluginId = "ecd-spectra@ecd-spectra"
$setupRoot = Join-Path $env:LOCALAPPDATA "ECDSpectra"
$runtimeRoot = Join-Path $setupRoot "runtime"
$cliPrefix = Join-Path $setupRoot "codex-cli"

function Find-CommandPath {
    param([Parameter(Mandatory = $true)][string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        return $null
    }
    return $command.Source
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath exited with code $LASTEXITCODE."
    }
}

function Test-CodexCli {
    param([Parameter(Mandatory = $true)][string]$Path)

    try {
        & $Path "--version" *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Get-Architecture {
    $architecture = $env:PROCESSOR_ARCHITECTURE
    if ($architecture -eq "ARM64") {
        return "arm64"
    }
    if ($architecture -eq "AMD64") {
        return "x64"
    }
    throw "Unsupported Windows architecture: $architecture"
}

function Install-PrivateNode {
    New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null

    $architecture = Get-Architecture
    $releases = Invoke-RestMethod -Uri "https://nodejs.org/dist/index.json"
    $release = $releases |
        Where-Object { $_.lts -and ($_.files -contains "win-$architecture-zip") } |
        Select-Object -First 1

    if ($null -eq $release) {
        throw "No current Node.js LTS archive was found for Windows $architecture."
    }

    $archiveName = "node-$($release.version)-win-$architecture.zip"
    $archiveUrl = "https://nodejs.org/dist/$($release.version)/$archiveName"
    $archivePath = Join-Path $setupRoot $archiveName
    $expandedFolder = Join-Path $runtimeRoot "node-$($release.version)-win-$architecture"

    if (-not (Test-Path -LiteralPath $expandedFolder)) {
        New-Item -ItemType Directory -Force -Path $setupRoot | Out-Null
        Invoke-WebRequest -Uri $archiveUrl -OutFile $archivePath
        Expand-Archive -LiteralPath $archivePath -DestinationPath $runtimeRoot -Force
        Remove-Item -LiteralPath $archivePath -Force
    }

    return @{
        Node = Join-Path $expandedFolder "node.exe"
        Npm = Join-Path $expandedFolder "npm.cmd"
    }
}

function Resolve-NodeTools {
    $nodePath = Find-CommandPath "node"
    $npmPath = Find-CommandPath "npm"

    if ($nodePath -and $npmPath) {
        return @{
            Node = $nodePath
            Npm = $npmPath
            Private = $false
        }
    }

    $privateTools = Install-PrivateNode
    return @{
        Node = $privateTools.Node
        Npm = $privateTools.Npm
        Private = $true
    }
}

function Resolve-CodexCli {
    $codexPath = Find-CommandPath "codex"
    if ($codexPath -and (Test-CodexCli -Path $codexPath)) {
        return @{
            Path = $codexPath
            Private = $false
        }
    }

    $privateCodex = Join-Path $cliPrefix "codex.cmd"
    if (-not (Test-Path -LiteralPath $privateCodex)) {
        $nodeTools = Resolve-NodeTools
        New-Item -ItemType Directory -Force -Path $cliPrefix | Out-Null
        Invoke-Checked -FilePath $nodeTools.Npm -Arguments @(
            "install",
            "--global",
            "--prefix",
            $cliPrefix,
            "@openai/codex"
        )
    }

    if (-not (Test-Path -LiteralPath $privateCodex)) {
        throw "Codex CLI installation completed, but codex.cmd was not found."
    }

    return @{
        Path = $privateCodex
        Private = $true
    }
}

function Write-Status {
    param(
        [string]$Status,
        [string]$Detail
    )

    [pscustomobject]@{
        status = $Status
        detail = $Detail
    } | ConvertTo-Json -Compress
}

if ($env:OS -ne "Windows_NT") {
    throw "This bootstrap is intended for Windows 10 or Windows 11."
}

$existingCodex = Find-CommandPath "codex"
if ($CheckOnly) {
    if ($existingCodex -and (Test-CodexCli -Path $existingCodex)) {
        Write-Status -Status "ready" -Detail "Codex CLI is available at $existingCodex."
        exit 0
    }

    $privateCodex = Join-Path $cliPrefix "codex.cmd"
    if ((Test-Path -LiteralPath $privateCodex) -and (Test-CodexCli -Path $privateCodex)) {
        Write-Status -Status "ready" -Detail "A private Codex CLI is available at $privateCodex."
        exit 0
    }

    Write-Status -Status "setup_required" -Detail "Codex CLI and the ECD Spectra plugin must be installed."
    exit 2
}

$codex = Resolve-CodexCli
Invoke-Checked -FilePath $codex.Path -Arguments @("--version")
Invoke-Checked -FilePath $codex.Path -Arguments @(
    "plugin",
    "marketplace",
    "add",
    $repository,
    "--ref",
    "main"
)
Invoke-Checked -FilePath $codex.Path -Arguments @(
    "plugin",
    "add",
    $pluginId
)
Invoke-Checked -FilePath $codex.Path -Arguments @(
    "plugin",
    "list"
)

Write-Status -Status "complete" -Detail (
    "ECD Spectra is installed. Restart the Codex desktop app and start a new conversation in the PDF project."
)
