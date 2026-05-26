[CmdletBinding()]
param(
    [int]$Port = 8000,
    [string]$BindHost = "127.0.0.1",
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$CurrentLocation = [System.IO.Path]::GetFullPath((Get-Location).Path)
$ProjectRootTrimmed = $ProjectRoot.TrimEnd("\")
$CurrentLocationTrimmed = $CurrentLocation.TrimEnd("\")
$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$TmpDir = Join-Path $ProjectRoot "tmp"
$StdoutLog = Join-Path $TmpDir ("uvicorn_{0}_stdout.log" -f $Port)
$StderrLog = Join-Path $TmpDir ("uvicorn_{0}_stderr.log" -f $Port)

function Fail-Step {
    param([string]$Message)
    throw $Message
}

function Write-Step {
    param([string]$Message)
    Write-Host ("[dev-launch] {0}" -f $Message)
}

function Normalize-Text {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ""
    }
    return $Value.Trim().ToLowerInvariant()
}

function Get-ListenerPids {
    param([int]$LocalPort)

    $pids = @()

    try {
        $connections = Get-NetTCPConnection -LocalPort $LocalPort -State Listen -ErrorAction Stop
        if ($connections) {
            $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        }
    } catch {
        $pids = @()
    }

    if (-not $pids -or $pids.Count -eq 0) {
        $netstatLines = netstat -ano | Select-String -Pattern (":{0}\s+.*LISTENING\s+(\d+)$" -f $LocalPort)
        foreach ($line in $netstatLines) {
            $match = [regex]::Match($line.Line, "LISTENING\s+(\d+)$")
            if ($match.Success) {
                $pids += [int]$match.Groups[1].Value
            }
        }
    }

    return @($pids | Where-Object { $_ -gt 0 } | Sort-Object -Unique)
}

function Get-ProcessRecord {
    param([int]$ProcessId)

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    $cim = $null

    try {
        $cim = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop
    } catch {
        $cim = $null
    }

    [pscustomobject]@{
        ProcessId = $ProcessId
        Exists = [bool]($proc -or $cim)
        Name = if ($proc) { $proc.ProcessName } elseif ($cim) { $cim.Name } else { $null }
        ExecutablePath = if ($cim) { $cim.ExecutablePath } elseif ($proc) { $proc.Path } else { $null }
        CommandLine = if ($cim) { $cim.CommandLine } else { $null }
        ParentProcessId = if ($cim) { $cim.ParentProcessId } else { $null }
    }
}

function Get-StandaloneSafety {
    param([pscustomobject]$ProcessRecord)

    if (-not $ProcessRecord.Exists) {
        return [pscustomobject]@{
            Safe = $false
            Reason = "process_not_found"
        }
    }

    $processName = Normalize-Text $ProcessRecord.Name
    $exePath = Normalize-Text $ProcessRecord.ExecutablePath
    $commandLine = Normalize-Text $ProcessRecord.CommandLine
    $venvPath = Normalize-Text $VenvPython
    $projectPath = Normalize-Text $ProjectRoot

    if ($processName -notin @("python", "python3")) {
        return [pscustomobject]@{
            Safe = $false
            Reason = "listener_is_not_python"
        }
    }

    if (-not $exePath) {
        return [pscustomobject]@{
            Safe = $false
            Reason = "process_path_unresolved"
        }
    }

    $isVenvPython = $exePath -eq $venvPath
    $looksLikeUvicorn = $commandLine -like "*-m uvicorn*" -and $commandLine -like "*app.main:app*"
    $looksLikeProjectRuntime = $commandLine -like ("*{0}*" -f $projectPath)

    if ($isVenvPython -and ($looksLikeUvicorn -or $looksLikeProjectRuntime)) {
        return [pscustomobject]@{
            Safe = $true
            Reason = "venv_python_for_project_runtime"
        }
    }

    if ($looksLikeUvicorn -and $looksLikeProjectRuntime) {
        return [pscustomobject]@{
            Safe = $true
            Reason = "python_uvicorn_for_project_runtime"
        }
    }

    return [pscustomobject]@{
        Safe = $false
        Reason = "python_process_does_not_look_like_project_runtime"
    }
}

function Get-ListenerStopPlan {
    param([pscustomobject]$ListenerRecord)

    $standalone = Get-StandaloneSafety -ProcessRecord $ListenerRecord
    if ($standalone.Safe) {
        return [pscustomobject]@{
            Safe = $true
            Reason = $standalone.Reason
            StopPids = @($ListenerRecord.ProcessId)
            Records = @($ListenerRecord)
        }
    }

    if (-not $ListenerRecord.ParentProcessId) {
        return [pscustomobject]@{
            Safe = $false
            Reason = $standalone.Reason
            StopPids = @()
            Records = @($ListenerRecord)
        }
    }

    $parentRecord = Get-ProcessRecord -ProcessId ([int]$ListenerRecord.ParentProcessId)
    $parentStandalone = Get-StandaloneSafety -ProcessRecord $parentRecord

    if ($parentStandalone.Safe) {
        return [pscustomobject]@{
            Safe = $true
            Reason = "listener_child_of_safe_project_runtime"
            StopPids = @($ListenerRecord.ProcessId, $parentRecord.ProcessId)
            Records = @($ListenerRecord, $parentRecord)
        }
    }

    return [pscustomobject]@{
        Safe = $false
        Reason = "{0}; parent={1}" -f $standalone.Reason, $parentStandalone.Reason
        StopPids = @()
        Records = @($ListenerRecord, $parentRecord)
    }
}

function Show-ProcessRecord {
    param([pscustomobject]$Record)

    $path = if ($Record.ExecutablePath) { $Record.ExecutablePath } else { "<unknown>" }
    $cmd = if ($Record.CommandLine) { $Record.CommandLine } else { "<unknown>" }
    Write-Host ("  PID {0} | {1} | {2}" -f $Record.ProcessId, $Record.Name, $path)
    Write-Host ("    cmd: {0}" -f $cmd)
}

if ($CurrentLocationTrimmed -ne $ProjectRootTrimmed) {
    Fail-Step "Run this launcher from the project root: $ProjectRoot"
}

if (-not (Test-Path $VenvPython)) {
    Fail-Step "Project venv python was not found: $VenvPython"
}

if (-not (Test-Path $TmpDir)) {
    New-Item -ItemType Directory -Path $TmpDir | Out-Null
}

Write-Step ("Project root confirmed: {0}" -f $ProjectRoot)
Write-Step ("Venv python confirmed: {0}" -f $VenvPython)

$listenerPids = Get-ListenerPids -LocalPort $Port

if ($listenerPids.Count -gt 0) {
    Write-Step ("Port {0} is occupied. Inspecting listeners..." -f $Port)

    $unsafePlans = @()
    $safeStopPids = New-Object System.Collections.Generic.HashSet[int]

    foreach ($listenerPid in $listenerPids) {
        $listenerRecord = Get-ProcessRecord -ProcessId $listenerPid
        Show-ProcessRecord -Record $listenerRecord

        $plan = Get-ListenerStopPlan -ListenerRecord $listenerRecord
        if (-not $plan.Safe) {
            $unsafePlans += $plan
            continue
        }

        foreach ($stopPid in $plan.StopPids) {
            [void]$safeStopPids.Add([int]$stopPid)
        }
    }

    if ($unsafePlans.Count -gt 0) {
        Write-Step "Launcher refused to stop the current listener set automatically."
        foreach ($unsafe in $unsafePlans) {
            Write-Host ("  unsafe reason: {0}" -f $unsafe.Reason)
            foreach ($record in $unsafe.Records) {
                if ($record) {
                    Show-ProcessRecord -Record $record
                }
            }
        }
        Fail-Step "Could not identify a safe single-runtime stop plan for port $Port."
    }

    $orderedStopPids = @($safeStopPids.ToArray() | Sort-Object -Descending)
    if ($orderedStopPids.Count -gt 0) {
        Write-Step ("Safe stop plan for port {0}: {1}" -f $Port, ($orderedStopPids -join ", "))
        if ($NoLaunch) {
            Write-Step "NoLaunch was requested. Stop plan inspected only; no process was terminated."
            return
        }

        foreach ($stopPid in $orderedStopPids) {
            Write-Step ("Stopping PID {0}" -f $stopPid)
            Stop-Process -Id $stopPid -Force -ErrorAction Stop
        }

        Start-Sleep -Seconds 2
        $remainingListeners = Get-ListenerPids -LocalPort $Port
        if ($remainingListeners.Count -gt 0) {
            Fail-Step ("Port {0} is still occupied after safe stop attempt: {1}" -f $Port, ($remainingListeners -join ", "))
        }
    }
} else {
    Write-Step ("Port {0} is free." -f $Port)
    if ($NoLaunch) {
        Write-Step "NoLaunch was requested. Nothing to stop and nothing to start."
        return
    }
}

$argumentList = @(
    "-m",
    "uvicorn",
    "app.main:app",
    "--reload",
    "--host",
    $BindHost,
    "--port",
    "$Port"
)

Write-Step ("Starting uvicorn from venv on http://{0}:{1}" -f $BindHost, $Port)
$launchedProcess = Start-Process `
    -FilePath $VenvPython `
    -ArgumentList $argumentList `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError $StderrLog `
    -PassThru

Start-Sleep -Seconds 3

$liveProcess = Get-Process -Id $launchedProcess.Id -ErrorAction SilentlyContinue
if (-not $liveProcess) {
    Fail-Step "The uvicorn launcher process exited before validation. Check $StderrLog"
}

$baseUrl = "http://127.0.0.1:{0}" -f $Port
try {
    $masterResponse = Invoke-WebRequest -UseBasicParsing -Uri ("{0}/dev/master-screen/LIVE01" -f $baseUrl) -TimeoutSec 5
    if ($masterResponse.StatusCode -lt 200 -or $masterResponse.StatusCode -ge 400) {
        Fail-Step "Master screen check returned HTTP $($masterResponse.StatusCode)."
    }
} catch {
    Fail-Step "Uvicorn started, but the master screen did not respond successfully. Check $StderrLog"
}

Write-Step ("Launcher PID: {0}" -f $launchedProcess.Id)
Write-Step ("stdout log: {0}" -f $StdoutLog)
Write-Step ("stderr log: {0}" -f $StderrLog)
Write-Host ""
Write-Host "Open these URLs:"
Write-Host ("  Master screen: {0}/dev/master-screen/LIVE01" -f $baseUrl)
Write-Host ("  TV screen:     {0}/dev/tv-mode/LIVE01" -f $baseUrl)
Write-Host ("  Onboarding:    {0}/delegation/start" -f $baseUrl)
Write-Host ("  Director:      {0}/dev/games/LIVE01/scenario/director" -f $baseUrl)
Write-Host ("  Master state:  {0}/dev/game-master/LIVE01/state" -f $baseUrl)
