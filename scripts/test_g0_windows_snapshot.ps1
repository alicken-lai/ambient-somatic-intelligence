# Synthetic-only tests. No Get-G0WindowsSnapshot invocation or host queries.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'g0_windows_snapshot.ps1')
$count = 0
function Assert-G0($Condition, [string]$Message) { if (-not $Condition) { throw $Message }; $script:count++ }
$created = [datetime]::SpecifyKind([datetime]'2026-01-02T00:00:00', [DateTimeKind]::Utc)
$p = { [pscustomobject]@{ ProcessId=42; Name='python.exe'; ExecutablePath='C:\private\secret.exe'; CommandLine='secret'; CreationDate=$created } }
$s = { [pscustomobject]@{ Name='example'; State='Running'; ProcessId=42; PathName='C:\secret.exe' } }
$t = { [pscustomobject]@{ TaskName='example'; TaskPath='\'; State='Ready'; Actions=@([pscustomobject]@{Execute='C:\secret.exe'; Arguments='secret'; WorkingDirectory='C:\private'}) } }
$r = Invoke-G0SnapshotCore -ProcessQuery $p -ServiceQuery $s -TaskQuery $t
Assert-G0 ($r.processes.status -eq 'COMPLETE' -and $r.processes.rows.Count -eq 1) 'process group'
Assert-G0 ($r.processes.rows[0].candidate -eq $true -and $null -ne $r.processes.rows[0].created_ns) 'process identity/candidate'
Assert-G0 ($r.services.rows[0].pid -eq 42 -and $null -eq $r.services.rows[0].created_ns) 'service unbound'
Assert-G0 ($r.tasks.rows[0].state -eq 'READY' -and $null -eq $r.tasks.rows[0].pid) 'task unbound'
$json = $r | ConvertTo-Json -Depth 8 -Compress
Assert-G0 (-not $json.Contains('secret') -and -not $json.Contains('private')) 'redaction'
$missing = { [pscustomobject]@{ProcessId=3; Name='other'; ExecutablePath=$null; CommandLine=$null; CreationDate=$null} }
$empty = { }
$r = Invoke-G0SnapshotCore -ProcessQuery $missing -ServiceQuery $empty -TaskQuery $empty
Assert-G0 ($null -eq $r.processes.rows[0].candidate -and $null -eq $r.processes.rows[0].created_ns) 'unknown fields'
$unmatchedProcess = { [pscustomobject]@{ProcessId=4; Name='worker.exe'; ExecutablePath='C:\Synthetic\worker.exe'; CommandLine='worker --serve'; CreationDate=$created} }
$unmatchedService = { [pscustomobject]@{Name='Example'; State='Running'; ProcessId=4; PathName='C:\Synthetic\worker.exe --serve'} }
$unmatchedTask = { [pscustomobject]@{TaskName='Example'; TaskPath='\Example\'; State='Ready'; Actions=@([pscustomobject]@{Execute='C:\Synthetic\worker.exe'; Arguments='--serve'; WorkingDirectory='C:\Synthetic'})} }
$r = Invoke-G0SnapshotCore -ProcessQuery $unmatchedProcess -ServiceQuery $unmatchedService -TaskQuery $unmatchedTask
Assert-G0 ($r.processes.status -eq 'COMPLETE' -and $null -eq $r.processes.rows[0].candidate) 'complete process nonmatch remains unknown'
Assert-G0 ($r.services.status -eq 'COMPLETE' -and $null -eq $r.services.rows[0].candidate) 'complete service nonmatch remains unknown'
Assert-G0 ($r.tasks.status -eq 'COMPLETE' -and $null -eq $r.tasks.rows[0].candidate) 'complete task nonmatch remains unknown'
$matchedService = { [pscustomobject]@{Name='Example'; State='Running'; ProcessId=4; PathName='C:\Synthetic\python.exe'} }
$matchedTask = { [pscustomobject]@{TaskName='Example'; TaskPath='\Example\'; State='Ready'; Actions=@([pscustomobject]@{Execute='C:\Synthetic\node.exe'; Arguments='--serve'; WorkingDirectory='C:\Synthetic'})} }
$r = Invoke-G0SnapshotCore -ProcessQuery $unmatchedProcess -ServiceQuery $matchedService -TaskQuery $matchedTask
Assert-G0 ($r.services.rows[0].candidate -eq $true -and $r.tasks.rows[0].candidate -eq $true) 'keyword matches remain positive'
$matchedThenOversized = { [pscustomobject]@{ProcessId=5; Name='python.exe'; ExecutablePath='worker.exe'; CommandLine=('x' * 32769); CreationDate=$created} }
$r = Invoke-G0SnapshotCore -ProcessQuery $matchedThenOversized -ServiceQuery $empty -TaskQuery $empty
Assert-G0 ($r.processes.status -eq 'INCOMPLETE' -and $r.processes.rows.Count -eq 0) 'later oversized field rejected after earlier match'
$bad = { [pscustomobject]@{ProcessId=1;Name='x';ExecutablePath='x';CommandLine='x';CreationDate=$null}; throw 'PRIVATE secret' }
$r = Invoke-G0SnapshotCore -ProcessQuery $bad -ServiceQuery $empty -TaskQuery $empty
Assert-G0 ($r.processes.status -eq 'INCOMPLETE' -and $r.processes.rows.Count -eq 0) 'partial failure'
Assert-G0 (-not (($r | ConvertTo-Json -Depth 8) -match 'PRIVATE|secret')) 'error redaction'
$duplicates = { 1..2 | ForEach-Object { [pscustomobject]@{ProcessId=1;Name='x';ExecutablePath='x';CommandLine='x';CreationDate=$null} } }
$r = Invoke-G0SnapshotCore -ProcessQuery $duplicates -ServiceQuery $empty -TaskQuery $empty
Assert-G0 ($r.processes.status -eq 'INCOMPLETE' -and $r.processes.rows.Count -eq 0) 'duplicate pid'
$tooMany = { 1..1025 | ForEach-Object { [pscustomobject]@{ProcessId=$_;Name='x';ExecutablePath='x';CommandLine='x';CreationDate=$null} } }
$r = Invoke-G0SnapshotCore -ProcessQuery $tooMany -ServiceQuery $empty -TaskQuery $empty
Assert-G0 ($r.processes.status -eq 'INCOMPLETE' -and $r.processes.rows.Count -eq 0) 'process cap'
$r = Invoke-G0SnapshotCore -ProcessQuery $empty -ServiceQuery $empty -TaskQuery $empty
Assert-G0 ($r.processes.status -eq 'INCOMPLETE') 'empty process set unknown'
Write-Output ("PASS $count synthetic-only assertions")
