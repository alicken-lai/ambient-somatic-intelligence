# G0 Windows observation adapter. Source preparation only; this script has no
# operational CLI. Dot-source to access the functions, then invoke only after
# separate source/runtime admission and a scope-specific Guardian decision.
# It never opens a database, writes evidence, or issues stop/control commands.
# COMPLETE means only that the provider callback returned within this code's
# row/error checks; it is not proof of writer closure or observation coverage.
# Service/task name hashes are not anonymization: names may be dictionary-guessed.
# This code has no hard timeout for provider callbacks.

function Get-G0Sha256([string] $Value) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    } finally { $sha.Dispose() }
}

function Get-G0Candidate([object[]] $Values) {
    $matched = $false
    foreach ($value in $Values) {
        if ($value -is [string] -and $value.Length -gt 32768) {
            throw 'FIELD_LIMIT'
        } elseif ($value -is [string] -and $value -match '(?i)python|hermes|node|powershell|pwsh|ambient-somatic-intelligence|state\.db|gateway|cron') {
            $matched = $true
        }
    }
    if ($matched) { return $true }
    # A keyword nonmatch is not evidence that the process cannot be a writer,
    # including when all supplied name/path/command fields are present.
    return $null
}

function Get-G0CreatedNs($Value) {
    if ($null -eq $Value -or $Value -isnot [datetime]) { return $null }
    if ($Value.Kind -eq [DateTimeKind]::Unspecified) { return $null }
    $epoch = [datetime]::SpecifyKind([datetime]'1970-01-01T00:00:00', [DateTimeKind]::Utc)
    $ticks = $Value.ToUniversalTime().Ticks - $epoch.Ticks
    if ($ticks -lt 0 -or $ticks -gt [long]::MaxValue / 100) { return $null }
    return [long]($ticks * 100)
}

function Get-G0State($Value) {
    switch ([string]$Value) {
        'Running' { return 'RUNNING' }
        'Stopped' { return 'STOPPED' }
        'Ready' { return 'READY' }
        'Disabled' { return 'DISABLED' }
        default { return 'UNKNOWN' }
    }
}

function Invoke-G0SnapshotCore {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][scriptblock] $ProcessQuery,
        [Parameter(Mandatory)][scriptblock] $ServiceQuery,
        [Parameter(Mandatory)][scriptblock] $TaskQuery
    )
    # Queries and callback execution are NOT hard time-limited in-process. A
    # reviewed external parent must bound/terminate this child and report
    # timeouts as UNKNOWN. Group failure discards all partial rows.
    $snapshot = [ordered]@{}
    foreach ($kind in @('processes', 'services', 'tasks')) {
        $rows = [System.Collections.Generic.List[object]]::new()
        $seen = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        $status = 'INCOMPLETE'
        try {
            $query = switch ($kind) { processes { $ProcessQuery } services { $ServiceQuery } tasks { $TaskQuery } }
            $limit = switch ($kind) { processes { 1024 } services { 512 } tasks { 512 } }
            & $query | ForEach-Object {
                if ($rows.Count -ge $limit) { throw 'ROW_LIMIT' }
                $item = $_
                if ($null -eq $item) { throw 'NULL_ROW' }
                if ($kind -eq 'processes') {
                    if ($null -eq $item.ProcessId -or [long]$item.ProcessId -lt 0) { throw 'BAD_PID' }
                    $pidValue = [long]$item.ProcessId
                    $identity = [string]$pidValue
                    $row = [ordered]@{ pid=$pidValue; created_ns=(Get-G0CreatedNs $item.CreationDate); candidate=(Get-G0Candidate @($item.Name, $item.ExecutablePath, $item.CommandLine)) }
                } else {
                    if ($kind -eq 'services') {
                        if ($item.Name -isnot [string] -or $item.Name.Length -eq 0 -or $item.Name.Length -gt 32768) { throw 'BAD_ID' }
                        $identity = Get-G0Sha256 $item.Name
                        $candidate = Get-G0Candidate @($item.Name, $item.PathName)
                        $pidValue = if ($null -ne $item.ProcessId -and [long]$item.ProcessId -gt 0) { [long]$item.ProcessId } else { $null }
                    } else {
                        if ($item.TaskName -isnot [string] -or $item.TaskPath -isnot [string] -or $item.TaskName.Length -eq 0 -or ($item.TaskName.Length + $item.TaskPath.Length) -gt 32768) { throw 'BAD_ID' }
                        $identity = Get-G0Sha256 ($item.TaskPath + $item.TaskName)
                        $values = [System.Collections.Generic.List[object]]::new()
                        $values.Add($item.TaskName)
                        $values.Add($item.TaskPath)
                        $actions = @($item.Actions)
                        if ($actions.Count -eq 0 -or $actions.Count -gt 32) { $values.Add($null) }
                        if ($actions.Count -gt 32) { throw 'ACTION_LIMIT' }
                        foreach ($action in $actions) {
                            if ($null -eq $action) { $values.Add($null) } else { $values.Add($action.Execute); $values.Add($action.Arguments); $values.Add($action.WorkingDirectory) }
                        }
                        $candidate = Get-G0Candidate $values.ToArray()
                        $pidValue = $null
                    }
                    # No creation time is obtained from service/task itself;
                    # associating PID with a separate query would imply a race-free binding.
                    $row = [ordered]@{ identity_sha256=$identity; state=(Get-G0State $item.State); pid=$pidValue; created_ns=$null; candidate=$candidate }
                }
                if (-not $seen.Add($identity)) { throw 'DUPLICATE_ID' }
                $rows.Add($row)
            }
            # A running collector must observe at least itself; an empty
            # process result is not evidence of an empty host.
            if ($kind -eq 'processes' -and $rows.Count -eq 0) { throw 'EMPTY_PROCESS_SET' }
            # Provider reply completed; this is not writer-closure evidence.
            $status = 'COMPLETE'
        } catch {
            $rows.Clear()
            # Do not publish exception details; they may contain paths or commands.
            $status = 'INCOMPLETE'
        }
        $snapshot[$kind] = [ordered]@{ status=$status; rows=@($rows.ToArray()) }
    }
    return $snapshot
}

function Get-G0WindowsSnapshot {
    # Queries request only the columns used by the projection. Command and
    # executable values are inspected in memory and never returned verbatim.
    # This function is not an authorization check and is not invoked by CLI.
    $process = { Get-CimInstance Win32_Process -Property ProcessId,Name,ExecutablePath,CommandLine,CreationDate -ErrorAction Stop -WarningAction SilentlyContinue }
    $service = { Get-CimInstance Win32_Service -Property Name,State,ProcessId,PathName -ErrorAction Stop -WarningAction SilentlyContinue }
    $tasks = { Get-ScheduledTask -ErrorAction Stop -WarningAction SilentlyContinue }
    $started = [DateTimeOffset]::UtcNow.ToString('o')
    $snapshot = Invoke-G0SnapshotCore -ProcessQuery $process -ServiceQuery $service -TaskQuery $tasks
    $ended = [DateTimeOffset]::UtcNow.ToString('o')
    return [ordered]@{
        schema='asi.g0.windows-metadata-snapshot.v1'
        providers=@('Win32_Process/Get-CimInstance', 'Win32_Service/Get-CimInstance', 'ScheduledTask/Get-ScheduledTask')
        collector_pid=$PID; started_utc=$started; ended_utc=$ended
        time_order_verified=$false; writer_closure='UNKNOWN'; snapshot=$snapshot
    }
}

if ($MyInvocation.InvocationName -ne '.') { throw 'HOST_ENTRY_NOT_ADMITTED_DOT_SOURCE_ONLY' }
