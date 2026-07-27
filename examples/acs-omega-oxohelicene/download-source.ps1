param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$exampleDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceDir = Join-Path $exampleDir "source"
$manifestPath = Join-Path $exampleDir "source-manifest.json"
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json

if ((Test-Path -LiteralPath $sourceDir) -and -not $Force) {
    throw "The source directory already exists. Use -Force to replace the downloaded example files."
}

$workDir = Join-Path ([System.IO.Path]::GetTempPath()) ("ecd-source-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $workDir | Out-Null

try {
    $archivePath = Join-Path $workDir "source.tar.gz"
    Invoke-WebRequest -Uri $manifest.oa_package_url -OutFile $archivePath -UseBasicParsing

    $archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    if ($archiveHash -ne $manifest.oa_package_sha256) {
        throw "Archive checksum mismatch. Expected $($manifest.oa_package_sha256), received $archiveHash."
    }

    tar -xzf $archivePath -C $workDir

    if (Test-Path -LiteralPath $sourceDir) {
        $resolvedExample = [System.IO.Path]::GetFullPath($exampleDir)
        $resolvedSource = [System.IO.Path]::GetFullPath($sourceDir)
        if (-not $resolvedSource.StartsWith($resolvedExample, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to replace a source directory outside the example directory."
        }
        Remove-Item -LiteralPath $resolvedSource -Recurse -Force
    }
    New-Item -ItemType Directory -Path $sourceDir | Out-Null

    foreach ($file in $manifest.files) {
        $archiveRelativePath = $file.archive_path -replace "/", [System.IO.Path]::DirectorySeparatorChar
        $inputPath = Join-Path $workDir $archiveRelativePath
        $actualHash = (Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash
        if ($actualHash -ne $file.sha256) {
            throw "Checksum mismatch for $($file.archive_path). Expected $($file.sha256), received $actualHash."
        }
        Copy-Item -LiteralPath $inputPath -Destination (Join-Path $sourceDir $file.local_name)
    }

    Write-Output "Verified source files written to $sourceDir"
}
finally {
    if (Test-Path -LiteralPath $workDir) {
        Remove-Item -LiteralPath $workDir -Recurse -Force
    }
}

