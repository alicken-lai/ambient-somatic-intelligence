[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$BackupRoot,

    [Parameter()]
    [string]$RunId = (Get-Date -Format 'yyyyMMddTHHmmssK').Replace(':', ''),

    [Parameter()]
    [string]$AsiWorktree = (Split-Path -Parent $PSScriptRoot),

    [Parameter()]
    [string]$HermesHome = (Join-Path $env:USERPROFILE '.hermes'),

    [Parameter()]
    [string]$HermesAgentWorktree = (Join-Path (Join-Path $env:USERPROFILE '.hermes') 'hermes-agent'),

    [Parameter(Mandatory)][string]$PythonPath,
    [Parameter(Mandatory)][string]$PythonSha256,
    [Parameter(Mandatory)][string]$BootstrapPath,
    [Parameter(Mandatory)][string]$BootstrapSha256,
    [Parameter(Mandatory)][string]$HelperPath,
    [Parameter(Mandatory)][string]$HelperSha256,
    [Parameter(Mandatory)][string]$PreflightPath,
    [Parameter(Mandatory)][string]$PreflightSha256,
    [Parameter(Mandatory)][string]$CryptoPackagePath,
    [Parameter(Mandatory)][string]$CryptoPackageSha256,
    [Parameter(Mandatory)][string]$YamlPackagePath,
    [Parameter(Mandatory)][string]$YamlPackageSha256,
    [Parameter(Mandatory)][string]$CffiExtensionPath,
    [Parameter(Mandatory)][string]$CffiExtensionSha256,

    [Parameter()]
    [long]$MemoryBudgetBytes = 536870912,

    [Parameter()]
    [long]$MaxPlaintextBytes = 130023424,

    [Parameter()]
    [int]$OperationTimeoutSeconds = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-NormalizedPath {
    param([Parameter(Mandatory)][string]$Path, [switch]$MustExist)
    $full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
    if ($MustExist -and -not (Test-Path -LiteralPath $full)) {
        throw 'A required target does not exist.'
    }
    return $full
}

function Test-AtOrBelow {
    param([Parameter(Mandatory)][string]$Candidate, [Parameter(Mandatory)][string]$Parent)
    if ($Candidate.Equals($Parent, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    return $Candidate.StartsWith(
        $Parent.TrimEnd('\') + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Assert-NewTarget {
    param([Parameter(Mandatory)][string]$Path)
    if (Test-Path -LiteralPath $Path) {
        throw 'An output target already exists; overwrite refused.'
    }
}

function Write-Utf8Exclusive {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Text)
    Assert-NewTarget -Path $Path
    $encoding = [System.Text.UTF8Encoding]::new($false)
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $writer = [System.IO.StreamWriter]::new($stream, $encoding)
        try { $writer.Write($Text); $writer.Flush(); $stream.Flush($true) }
        finally { $writer.Dispose() }
    }
    finally { $stream.Dispose() }
}

function Copy-FileExclusive {
    param([Parameter(Mandatory)][string]$Source, [Parameter(Mandatory)][string]$Destination)
    Assert-NewTarget -Path $Destination
    $parent = Split-Path -Parent $Destination
    [System.IO.Directory]::CreateDirectory($parent) | Out-Null
    $inputStream = [System.IO.File]::Open(
        $Source, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
    )
    try {
        $outputStream = [System.IO.File]::Open(
            $Destination, [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write, [System.IO.FileShare]::None
        )
        try { $inputStream.CopyTo($outputStream); $outputStream.Flush($true) }
        finally { $outputStream.Dispose() }
    }
    finally { $inputStream.Dispose() }
}

function Invoke-ProcessToExclusiveFile {
    param(
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string]$Destination
    )
    Assert-NewTarget -Path $Destination
    $parent = Split-Path -Parent $Destination
    [System.IO.Directory]::CreateDirectory($parent) | Out-Null
    $outputStream = [System.IO.File]::Open(
        $Destination, [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write, [System.IO.FileShare]::None
    )
    try {
        $start = [System.Diagnostics.ProcessStartInfo]::new()
        $start.FileName = $Executable
        $start.WorkingDirectory = $WorkingDirectory
        $start.UseShellExecute = $false
        $start.RedirectStandardOutput = $true
        $start.RedirectStandardError = $true
        $start.CreateNoWindow = $true
        foreach ($argument in $Arguments) { $start.ArgumentList.Add($argument) }
        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $start
        if (-not $process.Start()) { throw 'Failed to start a required local process.' }
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.StandardOutput.BaseStream.CopyTo($outputStream)
        $process.WaitForExit()
        $stderrTask.GetAwaiter().GetResult() | Out-Null
        if ($process.ExitCode -ne 0) {
            throw "A required local process failed with exit code $($process.ExitCode)."
        }
        $outputStream.Flush($true)
    }
    finally { $outputStream.Dispose() }
}

function Get-GitOutput {
    param([Parameter(Mandatory)][string]$Repo, [Parameter(Mandatory)][string[]]$Arguments)
    $output = @(& git -C $Repo @Arguments 2>$null)
    if ($LASTEXITCODE -ne 0) { throw 'A required read-only Git query failed.' }
    return $output
}

function Get-RelativePathChecked {
    param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][string]$Path)
    $resolved = Resolve-NormalizedPath -Path $Path -MustExist
    if (-not (Test-AtOrBelow -Candidate $resolved -Parent $Root)) {
        throw 'A discovered file escaped its declared source root.'
    }
    return [System.IO.Path]::GetRelativePath($Root, $resolved)
}

function Get-StringSha256 {
    param([Parameter(Mandatory)][string]$Text)
    return [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($Text))
    ).ToLowerInvariant()
}

function Test-PrivateDirectoryAcl {
    param([Parameter(Mandatory)]$Acl, [Parameter(Mandatory)][string]$OwnerSid)
    try {
        if (-not $Acl.AreAccessRulesProtected -or
            $Acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value -ne $OwnerSid) { return $false }
        $rules = @($Acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
        if ($rules.Count -ne 2) { return $false }
        $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
        foreach ($rule in $rules) {
            $sid = $rule.IdentityReference.Value
            if ($sid -notin @($OwnerSid, 'S-1-5-18') -or -not $seen.Add($sid) -or
                $rule.IsInherited -or [int]$rule.AccessControlType -ne 0 -or
                [int]$rule.FileSystemRights -ne [int][System.Security.AccessControl.FileSystemRights]::FullControl -or
                [int]$rule.InheritanceFlags -ne 3 -or [int]$rule.PropagationFlags -ne 0) { return $false }
        }
        return $true
    } catch { return $false }
}

function Assert-PrivateDirectory {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$OwnerSid)
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if (-not $item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Private parent/run is not a regular directory.' }
    if (-not (Test-PrivateDirectoryAcl -Acl (Get-Acl -LiteralPath $Path) -OwnerSid $OwnerSid)) {
        throw 'Private parent/run owner or exact protected ACL differs; no ACL repair is performed.'
    }
}

function Invoke-AtomicPrivateDirectoryCreate {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$OwnerSid)
    if (-not ('AsiBackupPrivateDirectoryNativeV1' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class AsiBackupPrivateDirectoryNativeV1 {
    [StructLayout(LayoutKind.Sequential)]
    public struct SecurityAttributes {
        public int Length;
        public IntPtr Descriptor;
        [MarshalAs(UnmanagedType.Bool)] public bool InheritHandle;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, ExactSpelling=true, SetLastError=true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CreateDirectoryW(string path, ref SecurityAttributes attributes);
}
'@
    }
    $acl = [System.Security.AccessControl.DirectorySecurity]::new()
    $owner = [System.Security.Principal.SecurityIdentifier]::new($OwnerSid)
    $acl.SetOwner($owner)
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($sid in @($OwnerSid, 'S-1-5-18')) {
        $rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
            [System.Security.Principal.SecurityIdentifier]::new($sid),
            [System.Security.AccessControl.FileSystemRights]::FullControl,
            [System.Security.AccessControl.InheritanceFlags]3,
            [System.Security.AccessControl.PropagationFlags]::None,
            [System.Security.AccessControl.AccessControlType]::Allow)
        $acl.AddAccessRule($rule)
    }
    $descriptor = $acl.GetSecurityDescriptorBinaryForm()
    $pinned = [System.Runtime.InteropServices.GCHandle]::Alloc($descriptor, [System.Runtime.InteropServices.GCHandleType]::Pinned)
    try {
        $attributes = [AsiBackupPrivateDirectoryNativeV1+SecurityAttributes]::new()
        $attributes.Length = [System.Runtime.InteropServices.Marshal]::SizeOf($attributes)
        $attributes.Descriptor = $pinned.AddrOfPinnedObject()
        $attributes.InheritHandle = $false
        # Unlike Directory.CreateDirectory, this native result distinguishes
        # successful creation from a pre-existing/racing target. No retry.
        return [AsiBackupPrivateDirectoryNativeV1]::CreateDirectoryW($Path, [ref]$attributes)
    } finally { $pinned.Free() }
}

function New-PrivateRunDirectory {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Parent,
          [Parameter(Mandatory)][string]$OwnerSid)
    if ([System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($Path)) -ne
        [System.IO.Path]::GetFullPath($Parent).TrimEnd('\', '/')) { throw 'Run target is not a direct child of its approved parent.' }
    Assert-PrivateDirectory -Path $Parent -OwnerSid $OwnerSid
    Assert-NewTarget -Path $Path
    if (-not (Invoke-AtomicPrivateDirectoryCreate -Path $Path -OwnerSid $OwnerSid)) {
        throw 'Atomic private run creation failed or target already exists; target retained unchanged.'
    }
    Assert-PrivateDirectory -Path $Path -OwnerSid $OwnerSid
}

function Assert-PinnedRuntimeFile {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Sha256)
    if ($Sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'Invalid runtime file pin.' }
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if ($item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Sha256) {
        throw 'Runtime file identity mismatch.'
    }
}

function Get-BackupBootstrapArguments {
    param([Parameter(Mandatory)]$Runtime, [Parameter(Mandatory)][string]$TargetHelper,
          [Parameter(Mandatory)][string]$TargetSha256, [string[]]$HelperArguments = @())
    return @('-I', '-S', '-B', $Runtime.BootstrapPath,
        '--helper', $TargetHelper, '--helper-sha256', $TargetSha256,
        '--crypto-package', $Runtime.CryptoPackagePath,
        '--crypto-package-sha256', $Runtime.CryptoPackageSha256,
        '--yaml-package', $Runtime.YamlPackagePath,
        '--yaml-package-sha256', $Runtime.YamlPackageSha256,
        '--cffi-extension', $Runtime.CffiExtensionPath,
        '--cffi-extension-sha256', $Runtime.CffiExtensionSha256, '--') + $HelperArguments
}

function Invoke-BackupBootstrapProcess {
    param([Parameter(Mandatory)]$Runtime, [Parameter(Mandatory)][string[]]$NativeArguments)
    & $Runtime.PythonPath @NativeArguments | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Isolated backup child failed.' }
}

function Invoke-IsolatedBackupHelper {
    param([Parameter(Mandatory)]$Runtime, [string[]]$Arguments = @(), [switch]$Preflight)
    Assert-PinnedRuntimeFile -Path $Runtime.PythonPath -Sha256 $Runtime.PythonSha256
    Assert-PinnedRuntimeFile -Path $Runtime.BootstrapPath -Sha256 $Runtime.BootstrapSha256
    Assert-PinnedRuntimeFile -Path $Runtime.HelperPath -Sha256 $Runtime.HelperSha256
    $target, $pin = $Runtime.HelperPath, $Runtime.HelperSha256
    if ($Preflight) {
        Assert-PinnedRuntimeFile -Path $Runtime.PreflightPath -Sha256 $Runtime.PreflightSha256
        $target, $pin = $Runtime.PreflightPath, $Runtime.PreflightSha256
        $Arguments = @('--target-helper', $Runtime.HelperPath, '--target-helper-sha256', $Runtime.HelperSha256)
    }
    $nativeArguments = @(Get-BackupBootstrapArguments -Runtime $Runtime -TargetHelper $target `
        -TargetSha256 $pin -HelperArguments $Arguments)
    Invoke-BackupBootstrapProcess -Runtime $Runtime -NativeArguments $nativeArguments
}

function Test-IsolatedBackupRuntime {
    param([Parameter(Mandatory)]$Runtime)
    foreach ($name in @('PythonSha256', 'BootstrapSha256', 'HelperSha256', 'PreflightSha256',
                        'CryptoPackageSha256', 'YamlPackageSha256', 'CffiExtensionSha256')) {
        if ($Runtime[$name] -cnotmatch '^[0-9a-f]{64}$') { throw 'Invalid explicit runtime pin.' }
    }
    Assert-PinnedRuntimeFile -Path $Runtime.CffiExtensionPath -Sha256 $Runtime.CffiExtensionSha256
    foreach ($name in @('CryptoPackagePath', 'YamlPackagePath')) {
        $item = Get-Item -LiteralPath $Runtime[$name] -Force -ErrorAction Stop
        if (-not $item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Invalid explicit dependency package directory.'
        }
    }
    Invoke-IsolatedBackupHelper -Runtime $Runtime -Preflight
}

function Start-IsolatedBackupRun {
    param([Parameter(Mandatory)]$Runtime, [Parameter(Mandatory)][string]$RunPath,
          [Parameter(Mandatory)][string]$Parent, [Parameter(Mandatory)][string]$OwnerSid)
    # Pin/dependency/syntax failure must precede directory creation or DPAPI.
    Test-IsolatedBackupRuntime -Runtime $Runtime
    New-PrivateRunDirectory -Path $RunPath -Parent $Parent -OwnerSid $OwnerSid
}

function Protect-File {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination,
        [Parameter(Mandatory)][string]$Report
    )
    Invoke-IsolatedBackupHelper -Runtime $backupRuntime -Arguments @('encrypt-file', '--key-file', $keyFile,
        '--source', $Source, '--destination', $Destination, '--report', $Report, '--payload-format', 'HEB2',
        '--max-plaintext-bytes', [string]$MaxPlaintextBytes)
}

function Protect-CommandOutput {
    param(
        [Parameter(Mandatory)][string]$Destination,
        [Parameter(Mandatory)][string]$Report,
        [Parameter(Mandatory)][string[]]$Arguments
    )
    $helperArguments = @('encrypt-command', '--key-file', $keyFile, '--destination', $Destination,
        '--report', $Report, '--cwd', $agent, '--payload-format', 'HEB2', '--max-plaintext-bytes',
        [string]$MaxPlaintextBytes, '--timeout-seconds', [string]$OperationTimeoutSeconds, '--', 'git.exe') + $Arguments
    Invoke-IsolatedBackupHelper -Runtime $backupRuntime -Arguments $helperArguments
}

function Copy-TreeControlled {
    param(
        [Parameter(Mandatory)][string]$SourceRoot,
        [Parameter(Mandatory)][string]$DestinationRoot,
        [Parameter(Mandatory)][string]$LogicalPrefix,
        [Parameter(Mandatory)][System.Collections.Generic.List[object]]$Inventory,
        [switch]$SkipDatabases
    )
    $excludedDirectories = @(
        'cache', 'caches', '.cache', '__pycache__', 'logs', 'log',
        'hermes-agent', 'node_modules', 'venv', '.venv', 'backups'
    )
    $files = Get-ChildItem -LiteralPath $SourceRoot -Recurse -File -Force |
        Where-Object {
            $relative = [System.IO.Path]::GetRelativePath($SourceRoot, $_.FullName)
            $segments = $relative -split '[\\/]'
            -not ($segments | Where-Object { $excludedDirectories -contains $_ })
        }
    foreach ($file in $files) {
        if ($SkipDatabases -and $file.Name -match '(?i)(\.db|\.sqlite|\.sqlite3|-wal|-shm)$') {
            continue
        }
        $relative = Get-RelativePathChecked -Root $SourceRoot -Path $file.FullName
        # Object names are content-address-like labels so Windows MAX_PATH does
        # not prevent backup of deeply nested skill assets.  The manifest keeps
        # the source-relative path.
        $logicalPath = ($LogicalPrefix.TrimEnd('/', '\') + '/' + ($relative -replace '\\', '/'))
        $label = Get-StringSha256 -Text $logicalPath
        $target = Join-Path $objectsRoot ($label + '.heb')
        $report = Join-Path $reportsRoot ($label + '.json')
        Protect-File -Source $file.FullName -Destination $target -Report $report
        $detail = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
        $Inventory.Add([pscustomobject]@{
            category = 'hermes-home-file'
            relative_path = $logicalPath
            backup_object = ('hermes-home-controlled/objects/' + $label + '.heb')
            verification_report = ('hermes-home-controlled/reports/' + $label + '.json')
            plaintext_bytes = $detail.plaintext_bytes
            plaintext_sha256 = $detail.plaintext_sha256
            ciphertext_sha256 = $detail.ciphertext_sha256
            ciphertext_bytes = $detail.ciphertext_bytes
            payload_format = $detail.payload_format
        })
    }
}

$asi = Resolve-NormalizedPath -Path $AsiWorktree -MustExist
$hermesHomePath = Resolve-NormalizedPath -Path $HermesHome -MustExist
$agent = Resolve-NormalizedPath -Path $HermesAgentWorktree -MustExist
$backup = Resolve-NormalizedPath -Path $BackupRoot
$backupRuntime = @{
    PythonPath = Resolve-NormalizedPath -Path $PythonPath -MustExist
    PythonSha256 = $PythonSha256
    BootstrapPath = Resolve-NormalizedPath -Path $BootstrapPath -MustExist
    BootstrapSha256 = $BootstrapSha256
    HelperPath = Resolve-NormalizedPath -Path $HelperPath -MustExist
    HelperSha256 = $HelperSha256
    PreflightPath = Resolve-NormalizedPath -Path $PreflightPath -MustExist
    PreflightSha256 = $PreflightSha256
    CryptoPackagePath = Resolve-NormalizedPath -Path $CryptoPackagePath -MustExist
    CryptoPackageSha256 = $CryptoPackageSha256
    YamlPackagePath = Resolve-NormalizedPath -Path $YamlPackagePath -MustExist
    YamlPackageSha256 = $YamlPackageSha256
    CffiExtensionPath = Resolve-NormalizedPath -Path $CffiExtensionPath -MustExist
    CffiExtensionSha256 = $CffiExtensionSha256
}

if (-not (Test-Path -LiteralPath (Join-Path $asi '.git'))) { throw 'ASI target is not a Git worktree.' }
if (-not (Test-Path -LiteralPath (Join-Path $agent '.git'))) { throw 'Hermes Agent target is not a Git worktree.' }
if (Test-AtOrBelow -Candidate $backup -Parent $asi) { throw 'Backup root may not be inside the ASI worktree.' }
if (Test-AtOrBelow -Candidate $backup -Parent $agent) { throw 'Backup root may not be inside the Hermes Agent worktree.' }
if ($RunId -notmatch '^[A-Za-z0-9][A-Za-z0-9._+-]{0,79}$') { throw 'RunId contains unsupported characters.' }

if (-not (Test-Path -LiteralPath $backup -PathType Container)) { throw 'Approved private backup parent must already exist.' }
$backup = Resolve-NormalizedPath -Path $backup -MustExist
if (Test-AtOrBelow -Candidate $backup -Parent $asi) { throw 'Resolved backup root is inside the ASI worktree.' }
if (Test-AtOrBelow -Candidate $backup -Parent $agent) { throw 'Resolved backup root is inside the Hermes Agent worktree.' }

$backupOwnerSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
Assert-PrivateDirectory -Path $backup -OwnerSid $backupOwnerSid
$runRoot = Join-Path $backup $RunId
Start-IsolatedBackupRun -Runtime $backupRuntime -RunPath $runRoot -Parent $backup -OwnerSid $backupOwnerSid

$keyFile = Join-Path $runRoot 'master-key.dpapi'
Invoke-IsolatedBackupHelper -Runtime $backupRuntime -Arguments @('init-key', '--key-file', $keyFile)

$sourceRoot = Join-Path $runRoot 'hermes-agent-source'
$dirtyRoot = Join-Path $sourceRoot 'dirty-files'
$homeRoot = Join-Path $runRoot 'hermes-home-controlled'
$databaseRoot = Join-Path $runRoot 'sqlite-online'
$objectsRoot = Join-Path $homeRoot 'objects'
$reportsRoot = Join-Path $homeRoot 'reports'
foreach ($directory in @($sourceRoot, $dirtyRoot, $homeRoot, $databaseRoot, $objectsRoot, $reportsRoot)) {
    [System.IO.Directory]::CreateDirectory($directory) | Out-Null
}

$inventory = [System.Collections.Generic.List[object]]::new()
$head = (Get-GitOutput -Repo $agent -Arguments @('rev-parse', 'HEAD') | Select-Object -First 1)
$gitState = [ordered]@{
    source_worktree = $agent
    head = $head
    branch = (Get-GitOutput -Repo $agent -Arguments @('branch', '--show-current') | Select-Object -First 1)
    tags_at_head = @(Get-GitOutput -Repo $agent -Arguments @('tag', '--points-at', 'HEAD'))
    porcelain_v2 = @(Get-GitOutput -Repo $agent -Arguments @('status', '--porcelain=v2', '--branch'))
}

Protect-CommandOutput -Destination (Join-Path $sourceRoot 'head.zip.heb') `
    -Report (Join-Path $sourceRoot 'head.zip.report.json') `
    -Arguments @('-C', $agent, 'archive', '--format=zip', 'HEAD')
Protect-CommandOutput -Destination (Join-Path $sourceRoot 'unstaged.patch.heb') `
    -Report (Join-Path $sourceRoot 'unstaged.patch.report.json') `
    -Arguments @('-C', $agent, 'diff', '--binary', '--no-ext-diff')
Protect-CommandOutput -Destination (Join-Path $sourceRoot 'staged.patch.heb') `
    -Report (Join-Path $sourceRoot 'staged.patch.report.json') `
    -Arguments @('-C', $agent, 'diff', '--cached', '--binary', '--no-ext-diff')
foreach ($capture in @(
    @{ logical = 'head.zip'; object = 'hermes-agent-source/head.zip.heb'; report = 'hermes-agent-source/head.zip.report.json' },
    @{ logical = 'unstaged.patch'; object = 'hermes-agent-source/unstaged.patch.heb'; report = 'hermes-agent-source/unstaged.patch.report.json' },
    @{ logical = 'staged.patch'; object = 'hermes-agent-source/staged.patch.heb'; report = 'hermes-agent-source/staged.patch.report.json' }
)) {
    $detail = Get-Content -LiteralPath (Join-Path $runRoot $capture.report) -Raw | ConvertFrom-Json
    $inventory.Add([pscustomobject]@{
        category = 'source-capture'
        relative_path = $capture.logical
        backup_object = $capture.object
        verification_report = $capture.report
        plaintext_bytes = $detail.plaintext_bytes
        plaintext_sha256 = $detail.plaintext_sha256
        ciphertext_sha256 = $detail.ciphertext_sha256
        ciphertext_bytes = $detail.ciphertext_bytes
        payload_format = $detail.payload_format
    })
}

$dirtyPaths = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase
)
foreach ($arguments in @(
    @('diff', '--name-only'),
    @('diff', '--cached', '--name-only'),
    @('ls-files', '--others', '--exclude-standard')
)) {
    foreach ($relative in Get-GitOutput -Repo $agent -Arguments $arguments) {
        if (-not [string]::IsNullOrWhiteSpace($relative)) { $dirtyPaths.Add($relative) | Out-Null }
    }
}
foreach ($relative in ($dirtyPaths | Sort-Object)) {
    $source = Join-Path $agent $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { continue }
    $checkedRelative = Get-RelativePathChecked -Root $agent -Path $source
    $destination = (Join-Path $dirtyRoot $checkedRelative) + '.heb'
    $report = $destination + '.report.json'
    Protect-File -Source $source -Destination $destination -Report $report
    $detail = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    $inventory.Add([pscustomobject]@{
        category = 'hermes-agent-dirty-file'
        relative_path = $checkedRelative
        backup_object = ('hermes-agent-source/dirty-files/' + ($checkedRelative -replace '\\', '/') + '.heb')
        verification_report = ('hermes-agent-source/dirty-files/' + ($checkedRelative -replace '\\', '/') + '.heb.report.json')
        plaintext_bytes = $detail.plaintext_bytes
        plaintext_sha256 = $detail.plaintext_sha256
        ciphertext_sha256 = $detail.ciphertext_sha256
        ciphertext_bytes = $detail.ciphertext_bytes
        payload_format = $detail.payload_format
    })
}

$gitStateJson = $gitState | ConvertTo-Json -Depth 5
Write-Utf8Exclusive -Path (Join-Path $sourceRoot 'git-state.json') -Text ($gitStateJson + "`n")

$homeInventoryDraft = Join-Path $runRoot 'home-source-inventory.metadata.json'
Invoke-IsolatedBackupHelper -Runtime $backupRuntime -Arguments @('inventory-home', '--source', $hermesHomePath,
    '--report', $homeInventoryDraft)
$homeSourceInventory = Get-Content -LiteralPath $homeInventoryDraft -Raw | ConvertFrom-Json
$homeRootAcl = Get-Acl -LiteralPath $hermesHomePath
$homeSourceInventory | Add-Member -NotePropertyName source_acl_sddl -NotePropertyValue $homeRootAcl.Sddl
$homeSourceInventory | Add-Member -NotePropertyName source_acl_sddl_sha256 -NotePropertyValue (Get-StringSha256 -Text $homeRootAcl.Sddl)
foreach ($entry in $homeSourceInventory.entries) {
    if ($entry.disposition -notin @('keep_encrypted', 'preserve_directory')) { continue }
    $source = Join-Path $hermesHomePath $entry.relative_path
    $sourceAcl = Get-Acl -LiteralPath $source
    $entry | Add-Member -NotePropertyName source_acl_sddl -NotePropertyValue $sourceAcl.Sddl
    $entry | Add-Member -NotePropertyName source_acl_sddl_sha256 -NotePropertyValue (Get-StringSha256 -Text $sourceAcl.Sddl)
    if ($entry.disposition -ne 'keep_encrypted') { continue }
    $label = $entry.relative_path_sha256
    $destination = Join-Path $objectsRoot ($label + '.heb')
    $report = Join-Path $reportsRoot ($label + '.json')
    Protect-File -Source $source -Destination $destination -Report $report
    $detail = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    if ($detail.plaintext_bytes -ne $entry.source_size_bytes) { throw 'Source file changed size during preservation.' }
    $inventory.Add([pscustomobject]@{
        category = 'hermes-home-file'
        relative_path = $entry.relative_path
        backup_object = ('hermes-home-controlled/objects/' + $label + '.heb')
        verification_report = ('hermes-home-controlled/reports/' + $label + '.json')
        plaintext_bytes = $detail.plaintext_bytes
        plaintext_sha256 = $detail.plaintext_sha256
        ciphertext_sha256 = $detail.ciphertext_sha256
        source_acl_sddl = $entry.source_acl_sddl
        source_acl_sddl_sha256 = $entry.source_acl_sddl_sha256
        ciphertext_bytes = $detail.ciphertext_bytes
        payload_format = $detail.payload_format
    })
}
$homeInventoryPath = Join-Path $runRoot 'home-source-inventory.json'
Write-Utf8Exclusive -Path $homeInventoryPath -Text (($homeSourceInventory | ConvertTo-Json -Depth 10) + "`n")
$homeInventoryHash = (Get-FileHash -LiteralPath $homeInventoryPath -Algorithm SHA256).Hash.ToLowerInvariant()

# Preserve reconstructable Git remote metadata only as ciphertext.  The public
# manifest retains hashes and object references, never remote URLs.
$remoteObject = Join-Path $sourceRoot 'git-remotes-v.heb'
$remoteReport = Join-Path $sourceRoot 'git-remotes-v.report.json'
Protect-CommandOutput -Destination $remoteObject -Report $remoteReport `
    -Arguments @('-C', $agent, 'remote', '-v')
$remoteDetail = Get-Content -LiteralPath $remoteReport -Raw | ConvertFrom-Json
$inventory.Add([pscustomobject]@{
    category = 'git-recovery-metadata'
    relative_path = 'git.remote-v'
    backup_object = 'hermes-agent-source/git-remotes-v.heb'
    verification_report = 'hermes-agent-source/git-remotes-v.report.json'
    plaintext_bytes = $remoteDetail.plaintext_bytes
    plaintext_sha256 = $remoteDetail.plaintext_sha256
    ciphertext_sha256 = $remoteDetail.ciphertext_sha256
    ciphertext_bytes = $remoteDetail.ciphertext_bytes
    payload_format = $remoteDetail.payload_format
})

# Git reports more than one hundred thousand ignored dependency/cache files in
# this checkout.  Bound the review, fail closed above the cap, expose only
# SHA-256 path tokens publicly, and preserve the exact path mapping encrypted.
$ignoredPaths = @(Get-GitOutput -Repo $agent -Arguments @('ls-files', '--others', '--ignored', '--exclude-standard'))
$ignoredLimit = 200000
if ($ignoredPaths.Count -gt $ignoredLimit) { throw 'Ignored inventory exceeded its predeclared bound.' }
$ignoredFiltered = [System.Collections.Generic.List[object]]::new()
$ignoredDecisionCounts = [ordered]@{
    dependency_tree_excluded = 0
    cache_excluded = 0
    log_excluded = 0
    build_excluded = 0
    generated_excluded = 0
    recovery_candidate_kept_encrypted = 0
}
foreach ($relative in ($ignoredPaths | Sort-Object -Unique)) {
    $normalized = $relative -replace '\\', '/'
    $pathToken = Get-StringSha256 -Text $normalized
    $decision = 'exclude'
    $reason = 'generated_excluded'
    if ($normalized -match '(^|/)(venv|\.venv|node_modules)(/|$)') {
        $reason = 'dependency_tree_excluded'
    }
    elseif ($normalized -match '(^|/)(cache|caches|\.cache|__pycache__)(/|$)|(?i)\.pyc$') {
        $reason = 'cache_excluded'
    }
    elseif ($normalized -match '(^|/)(logs?|\.logs?)(/|$)') {
        $reason = 'log_excluded'
    }
    elseif ($normalized -match '(^|/)(dist|build|\.pytest_cache|\.mypy_cache|\.ruff_cache)(/|$)') {
        $reason = 'build_excluded'
    }
    elseif ($normalized -match '(?i)\.(tmp|temp|bak|swp|swo)$') {
        $reason = 'generated_excluded'
    }
    else {
        $decision = 'keep_encrypted'
        $reason = 'recovery_candidate_kept_encrypted'
        $source = Join-Path $agent $relative
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw 'A required ignored recovery candidate is not a regular file.'
        }
        $ignoredObject = Join-Path $dirtyRoot ('ignored-' + $pathToken + '.heb')
        $ignoredReport = $ignoredObject + '.report.json'
        Protect-File -Source $source -Destination $ignoredObject -Report $ignoredReport
        $ignoredDetail = Get-Content -LiteralPath $ignoredReport -Raw | ConvertFrom-Json
        $inventory.Add([pscustomobject]@{
            category = 'hermes-agent-ignored-required'
            relative_path = ('ignored-required/' + $pathToken)
            source_path_sha256 = $pathToken
            backup_object = ('hermes-agent-source/dirty-files/ignored-' + $pathToken + '.heb')
            verification_report = ('hermes-agent-source/dirty-files/ignored-' + $pathToken + '.heb.report.json')
            plaintext_bytes = $ignoredDetail.plaintext_bytes
            plaintext_sha256 = $ignoredDetail.plaintext_sha256
            ciphertext_sha256 = $ignoredDetail.ciphertext_sha256
            ciphertext_bytes = $ignoredDetail.ciphertext_bytes
            payload_format = $ignoredDetail.payload_format
        })
    }
    $ignoredDecisionCounts[$reason]++
    $ignoredFiltered.Add([ordered]@{ path_sha256 = $pathToken; decision = $decision; reason = $reason })
}
$ignoredFilteredDocument = [ordered]@{
    schema = 'hermes-secret-filtered-ignored-inventory/v1'
    source_count = $ignoredPaths.Count
    unique_count = $ignoredFiltered.Count
    maximum_entries = $ignoredLimit
    path_disclosure = 'sha256-only'
    decision_counts = $ignoredDecisionCounts
    entries = @($ignoredFiltered)
}
$ignoredFilteredPath = Join-Path $sourceRoot 'ignored-inventory.filtered.json'
Write-Utf8Exclusive -Path $ignoredFilteredPath -Text (($ignoredFilteredDocument | ConvertTo-Json -Depth 6 -Compress) + "`n")

# The exact path inventory is required for disaster recovery, but may contain
# credential-signalling names.  Retain it only in the authenticated ciphertext.
$ignoredRawObject = Join-Path $sourceRoot 'ignored-inventory.raw.heb'
$ignoredRawReport = Join-Path $sourceRoot 'ignored-inventory.raw.report.json'
Protect-CommandOutput -Destination $ignoredRawObject -Report $ignoredRawReport `
    -Arguments @('-C', $agent, 'ls-files', '-z', '--others', '--ignored', '--exclude-standard')
$ignoredRawDetail = Get-Content -LiteralPath $ignoredRawReport -Raw | ConvertFrom-Json
$inventory.Add([pscustomobject]@{
    category = 'git-recovery-metadata'
    relative_path = 'git.ignored-path-map'
    backup_object = 'hermes-agent-source/ignored-inventory.raw.heb'
    verification_report = 'hermes-agent-source/ignored-inventory.raw.report.json'
    plaintext_bytes = $ignoredRawDetail.plaintext_bytes
    plaintext_sha256 = $ignoredRawDetail.plaintext_sha256
    ciphertext_sha256 = $ignoredRawDetail.ciphertext_sha256
    ciphertext_bytes = $ignoredRawDetail.ciphertext_bytes
    payload_format = $ignoredRawDetail.payload_format
})

$databaseFiles = @($homeSourceInventory.entries | Where-Object disposition -EQ 'sqlite_online_backup' |
    ForEach-Object { Get-Item -LiteralPath (Join-Path $hermesHomePath $_.relative_path) })
$databaseIndex = 0
foreach ($database in ($databaseFiles | Sort-Object FullName -Unique)) {
    $databaseIndex++
    $label = 'database-{0:D3}' -f $databaseIndex
    $destination = Join-Path $databaseRoot ($label + '.sqlite3.heb')
    $report = Join-Path $databaseRoot ($label + '.report.json')
    Invoke-IsolatedBackupHelper -Runtime $backupRuntime -Arguments @('sqlite-backup', '--key-file', $keyFile,
        '--source', $database.FullName, '--destination', $destination, '--report', $report, '--payload-format', 'HEB2',
        '--max-plaintext-bytes', [string]$MaxPlaintextBytes, '--memory-budget-bytes', [string]$MemoryBudgetBytes,
        '--timeout-seconds', [string]$OperationTimeoutSeconds)
    $detail = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    $inventory.Add([pscustomobject]@{
        category = 'sqlite-online-backup'
        source_path_sha256 = [Convert]::ToHexString(
            [Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($database.FullName))
        ).ToLowerInvariant()
        backup_label = $label
        relative_path = $database.Name
        source_relative_path = ((Get-RelativePathChecked -Root $hermesHomePath -Path $database.FullName) -replace '\\', '/')
        backup_object = ('sqlite-online/' + $label + '.sqlite3.heb')
        plaintext_bytes = $detail.plaintext_bytes
        plaintext_sha256 = $detail.plaintext_sha256
        ciphertext_sha256 = $detail.ciphertext_sha256
        verification_report = ('sqlite-online/' + [System.IO.Path]::GetFileName($report))
        ciphertext_bytes = $detail.ciphertext_bytes
        payload_format = $detail.payload_format
    })
}

$manifest = [ordered]@{
    schema = 'hermes-upgrade-backup-manifest/v4'
    home_source_inventory = [ordered]@{ path = 'home-source-inventory.json'; sha256 = $homeInventoryHash }
    isolated_backup_runtime = [ordered]@{
        python_sha256 = $backupRuntime.PythonSha256
        bootstrap_sha256 = $backupRuntime.BootstrapSha256
        helper_sha256 = $backupRuntime.HelperSha256
        preflight_sha256 = $backupRuntime.PreflightSha256
        cryptography_package_sha256 = $backupRuntime.CryptoPackageSha256
        yaml_package_sha256 = $backupRuntime.YamlPackageSha256
        cffi_extension_sha256 = $backupRuntime.CffiExtensionSha256
        python_flags = @('-I', '-S', '-B')
        preflight_before_run_creation = $true
        dependency_loading = 'Explicit pinned package sources/extensions; no site processing or site-packages search path'
    }
    created_at = [DateTimeOffset]::Now.ToString('o')
    exact_targets = [ordered]@{
        asi_worktree_guard = $asi
        hermes_home = $hermesHomePath
        hermes_agent_worktree = $agent
        backup_run_root = $runRoot
        pinned_upgrade_commit = '939e45c91d751fadd94dcd1b873ac3cb44846213'
    }
    authorization = [ordered]@{
        authorization_ref = 'user-explicit-override:20260913:G2-and-unsigned-v0212'
        exact_backup_run_root = $runRoot
        scope = 'encrypted preservation and isolated in-memory restore rehearsal'
    }
    independent_verifier = $null
    independent_verification = 'Pending assignment and review for this exact new run'
    recovery = [ordered]@{
        key_owner_sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
        key_protection = 'Windows DPAPI CurrentUser'
        retention = 'Retain through successful cutover plus 30 days; removal requires a separately authorized retention action.'
        restore_target_policy = 'New isolated target only; overwrite refused.'
    }
    source_git_metadata = [ordered]@{
        head = $head
        branch = $gitState.branch
        tags_at_head = $gitState.tags_at_head
        remote_names = @(Get-GitOutput -Repo $agent -Arguments @('remote'))
        remote_v_hashes = @((Get-GitOutput -Repo $agent -Arguments @('remote', '-v')) | ForEach-Object { Get-StringSha256 -Text $_ })
        encrypted_remote_metadata = 'hermes-agent-source/git-remotes-v.heb'
        encrypted_ignored_path_map = 'hermes-agent-source/ignored-inventory.raw.heb'
        secret_filtered_ignored_inventory = 'hermes-agent-source/ignored-inventory.filtered.json'
        secret_filtered_ignored_inventory_sha256 = (Get-FileHash -LiteralPath $ignoredFilteredPath -Algorithm SHA256).Hash.ToLowerInvariant()
        ignored_inventory_bound = $ignoredLimit
        ignored_decision_counts = $ignoredDecisionCounts
    }
    runtime_writers = @((Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ExecutablePath -and (Test-AtOrBelow -Candidate $_.ExecutablePath -Parent (Join-Path $agent 'venv'))
    }) | ForEach-Object {
        [ordered]@{ pid = $_.ProcessId; executable_path_sha256 = Get-StringSha256 -Text $_.ExecutablePath }
    })
    exclusions = @('cache', 'logs', 'hermes-agent-code-from-home-copy', 'node_modules', 'venv', 'raw-wal', 'raw-shm')
    encryption = [ordered]@{
        payload = 'HEB2 AES-256-GCM chunks plus authenticated whole-stream final record'
        payload_format = 'HEB2'
        operation_plaintext_limit_bytes = $MaxPlaintextBytes
        memory_budget_bytes = $MemoryBudgetBytes
        memory_budget_model = '4 image equivalents plus 16 MiB; not an OS RSS limit'
        key_at_rest = 'Windows DPAPI CurrentUser'
        directory_acl = 'current user and SYSTEM only'
    }
    source_capture = @('encrypted git archive HEAD', 'encrypted unstaged binary patch', 'encrypted staged binary patch', 'encrypted dirty-file physical snapshot', 'encrypted reconstructable git remote metadata', 'encrypted exact ignored path map plus secret-filtered public decision inventory')
    items = @($inventory)
    redaction = @(
        'No config, profile, skill, MCP, patch, or database contents were printed.',
        'The .env credential surface is encrypted and only hashes/size/ACL metadata appear in the manifest.',
        'Remote URLs and exact ignored paths exist only inside authenticated ciphertext.',
        'SQLite source paths are represented in the manifest by SHA-256 only.',
        'Python helper emits fixed status markers and exception class only.'
    )
}
$manifestPath = Join-Path $runRoot 'manifest.json'
Write-Utf8Exclusive -Path $manifestPath -Text (($manifest | ConvertTo-Json -Depth 8) + "`n")
$manifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Utf8Exclusive -Path (Join-Path $runRoot 'manifest.sha256') -Text ($manifestHash + "  manifest.json`n")

$restoreReport = Join-Path $runRoot 'isolated_restore_rehearsal.json'
Invoke-IsolatedBackupHelper -Runtime $backupRuntime -Arguments @('verify-run', '--key-file', $keyFile,
    '--manifest', $manifestPath, '--run-root', $runRoot, '--report', $restoreReport,
    '--expected-manifest-sha256', $manifestHash, '--max-plaintext-bytes', [string]$MaxPlaintextBytes,
    '--memory-budget-bytes', [string]$MemoryBudgetBytes)

$payloads = @(Get-ChildItem -LiteralPath $runRoot -Recurse -File -Filter '*.heb' -Force)
if ($payloads.Count -eq 0) { throw 'No encrypted backup payloads were created; fail closed.' }

Write-Output 'hermes_upgrade_backup: ok'
Write-Output "run_id: $RunId"
Write-Output "manifest_sha256: $manifestHash"
Write-Output 'secret_values_printed: false'
