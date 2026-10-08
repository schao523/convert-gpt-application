[CmdletBinding()]
param(
    [switch]$ProbeOnly,
    [string]$Executable,
    [string[]]$CommandArgument = @(),
    [switch]$KeepRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-ContainedPath {
    param(
        [Parameter(Mandatory = $true)][string]$Child,
        [Parameter(Mandatory = $true)][string]$Parent
    )

    $childPath = [IO.Path]::GetFullPath($Child).TrimEnd('\', '/')
    $parentPath = [IO.Path]::GetFullPath($Parent).TrimEnd('\', '/')
    return $childPath.StartsWith(
        $parentPath + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase
    )
}

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string[]]$Argument
    )

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $Command @Argument 2>&1
        $nativeExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($nativeExitCode -ne 0) {
        throw "$Command exited $nativeExitCode`: $($output -join [Environment]::NewLine)"
    }
}

function Invoke-CapabilityProbe {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )

    try {
        & $Action
        return [pscustomobject]@{ name = $Name; status = "PASS"; diagnostic = $null }
    }
    catch {
        return [pscustomobject]@{
            name = $Name
            status = "FAIL"
            diagnostic = "$Name`: $($_.Exception.Message)"
        }
    }
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localAppData = [Environment]::GetFolderPath(
    [Environment+SpecialFolder]::LocalApplicationData
)
if ([string]::IsNullOrWhiteSpace($localAppData)) {
    throw "Windows LocalApplicationData is unavailable"
}

$systemTemp = [IO.Path]::GetFullPath((Join-Path $localAppData "Temp"))
if (Test-ContainedPath -Child $systemTemp -Parent $repositoryRoot) {
    throw "canonical system temp resolves inside the repository"
}

$testRoot = Join-Path $systemTemp "obvious-one-plugin-tests"
$disposableRoot = Join-Path $testRoot ([Guid]::NewGuid().ToString("N"))
$capabilities = [ordered]@{
    filesystem = "NOT VERIFIED"
    hard_link = "NOT VERIFIED"
    atomic_replace = "NOT VERIFIED"
    git = "NOT VERIFIED"
    packaging = "NOT VERIFIED"
}
$diagnostics = [System.Collections.Generic.List[string]]::new()
$commandResult = [ordered]@{ status = "NOT APPLICABLE"; exit_code = $null }
$status = "PASS"
$classification = "NONE"
$exitCode = 0
$originalEnvironment = [ordered]@{}
foreach ($name in @("TEMP", "TMP", "PYTHONUTF8", "PYTHONIOENCODING")) {
    $originalEnvironment[$name] = [pscustomobject]@{
        exists = Test-Path -LiteralPath "Env:$name"
        value = [Environment]::GetEnvironmentVariable($name, "Process")
    }
}

try {
    New-Item -ItemType Directory -Path $disposableRoot -Force | Out-Null
    $env:TEMP = $disposableRoot
    $env:TMP = $disposableRoot
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"

    $probes = @(
        (Invoke-CapabilityProbe -Name "filesystem" -Action {
            $path = Join-Path $disposableRoot "filesystem.txt"
            [IO.File]::WriteAllText($path, "utf8-測試", [Text.UTF8Encoding]::new($false))
            if ([IO.File]::ReadAllText($path, [Text.Encoding]::UTF8) -ne "utf8-測試") {
                throw "UTF-8 round trip failed"
            }
        }),
        (Invoke-CapabilityProbe -Name "hard_link" -Action {
            $target = Join-Path $disposableRoot "hard-link-target.txt"
            $link = Join-Path $disposableRoot "hard-link.txt"
            [IO.File]::WriteAllText($target, "hard-link", [Text.UTF8Encoding]::new($false))
            New-Item -ItemType HardLink -Path $link -Target $target | Out-Null
            if ([IO.File]::ReadAllText($link) -ne "hard-link") {
                throw "hard-link bytes differ"
            }
        }),
        (Invoke-CapabilityProbe -Name "atomic_replace" -Action {
            $destination = Join-Path $disposableRoot "replace-destination.txt"
            $staged = Join-Path $disposableRoot "replace-staged.txt"
            $backup = Join-Path $disposableRoot "replace-backup.txt"
            [IO.File]::WriteAllText($destination, "before")
            [IO.File]::WriteAllText($staged, "after")
            [IO.File]::Replace($staged, $destination, $backup)
            if ([IO.File]::ReadAllText($destination) -ne "after") {
                throw "atomic replacement failed"
            }
        }),
        (Invoke-CapabilityProbe -Name "git" -Action {
            $source = Join-Path $disposableRoot "git-source"
            $clone = Join-Path $disposableRoot "git-clone"
            New-Item -ItemType Directory -Path $source | Out-Null
            Invoke-NativeCommand -Command "git" -Argument @("init", "-q", $source)
            Invoke-NativeCommand -Command "git" -Argument @("-C", $source, "config", "user.email", "windows-probe@example.invalid")
            Invoke-NativeCommand -Command "git" -Argument @("-C", $source, "config", "user.name", "Windows Probe")
            [IO.File]::WriteAllText((Join-Path $source "fixture.txt"), "fixture`n")
            Invoke-NativeCommand -Command "git" -Argument @("-C", $source, "add", "fixture.txt")
            Invoke-NativeCommand -Command "git" -Argument @("-C", $source, "commit", "-q", "-m", "fixture")
            Invoke-NativeCommand -Command "git" -Argument @("clone", "--no-hardlinks", "--no-checkout", $source, $clone)
            Invoke-NativeCommand -Command "git" -Argument @("-C", $clone, "checkout", "-q", "--detach", "HEAD")
            if (-not (Test-Path -LiteralPath (Join-Path $clone "fixture.txt") -PathType Leaf)) {
                throw "fresh checkout fixture is missing"
            }
        }),
        (Invoke-CapabilityProbe -Name "packaging" -Action {
            $source = Join-Path $disposableRoot "package-source"
            $archive = Join-Path $disposableRoot "package.zip"
            New-Item -ItemType Directory -Path $source | Out-Null
            [IO.File]::WriteAllText((Join-Path $source "member.txt"), "package`n")
            Compress-Archive -LiteralPath (Join-Path $source "member.txt") -DestinationPath $archive
            if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {
                throw "ZIP archive was not created"
            }
        })
    )

    foreach ($probe in $probes) {
        $capabilities[$probe.name] = $probe.status
        if ($null -ne $probe.diagnostic) {
            $diagnostics.Add($probe.diagnostic)
        }
    }

    if ($capabilities.Values -contains "FAIL") {
        $status = "BLOCKED"
        $classification = "ENVIRONMENT"
        $exitCode = 2
    }
    elseif (-not $ProbeOnly) {
        if ([string]::IsNullOrWhiteSpace($Executable)) {
            $status = "BLOCKED"
            $classification = "TEST_FIXTURE"
            $diagnostics.Add("Executable is required unless -ProbeOnly is selected")
            $exitCode = 2
        }
        else {
            try {
                & $Executable @CommandArgument
                $commandExitCode = $LASTEXITCODE
                if ($null -eq $commandExitCode) {
                    $commandExitCode = 0
                }
            }
            catch {
                $commandExitCode = 1
                $diagnostics.Add("command launch failed: $($_.Exception.Message)")
            }
            $commandResult.exit_code = $commandExitCode
            if ($commandExitCode -ne 0) {
                $commandResult.status = "FAIL"
                $status = "FAIL"
                $classification = "REQUIRES_TRIAGE"
                $exitCode = $commandExitCode
            }
            else {
                $commandResult.status = "PASS"
            }
        }
    }
}
catch {
    $status = "BLOCKED"
    $classification = "ENVIRONMENT"
    $diagnostics.Add($_.Exception.Message)
    $exitCode = 2
}
finally {
    try {
        if (-not $KeepRoot -and (Test-Path -LiteralPath $disposableRoot)) {
            if (-not (Test-ContainedPath -Child $disposableRoot -Parent $testRoot)) {
                throw "refusing cleanup outside the owned disposable test root"
            }
            Remove-Item -LiteralPath $disposableRoot -Recurse -Force
        }
    }
    catch {
        $diagnostics.Add("cleanup failed: $($_.Exception.Message)")
        if ($status -ne "FAIL") {
            $status = "BLOCKED"
            $classification = "ENVIRONMENT"
            $exitCode = 2
        }
    }
    finally {
        foreach ($name in $originalEnvironment.Keys) {
            $saved = $originalEnvironment[$name]
            if ($saved.exists) {
                [Environment]::SetEnvironmentVariable($name, $saved.value, "Process")
            }
            else {
                [Environment]::SetEnvironmentVariable($name, $null, "Process")
            }
        }
    }
}

$report = [ordered]@{
    schema = "windows-test-environment-v1"
    status = $status
    classification = $classification
    system_temp = $systemTemp
    disposable_root = $disposableRoot
    inside_repository = (Test-ContainedPath -Child $disposableRoot -Parent $repositoryRoot)
    environment = [ordered]@{
        PYTHONUTF8 = "1"
        PYTHONIOENCODING = "utf-8"
        TEMP = $disposableRoot
        TMP = $disposableRoot
    }
    capabilities = $capabilities
    command = $commandResult
    diagnostics = @($diagnostics)
}

$report | ConvertTo-Json -Depth 6 -Compress
exit $exitCode
