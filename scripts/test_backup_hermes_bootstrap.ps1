# Synthetic-only caller routing. No Python, backup, DPAPI, native creation or ACL changes.
$ErrorActionPreference = 'Stop'
$tokens, $parseErrors = $null, $null
$source = Join-Path $PSScriptRoot 'backup_hermes_for_upgrade.ps1'
$ast = [System.Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$parseErrors)
if (@($parseErrors).Count -ne 0) { throw 'Caller source parse failed.' }
$wanted = @('Assert-PinnedRuntimeFile', 'Get-BackupBootstrapArguments', 'Invoke-IsolatedBackupHelper',
            'Test-IsolatedBackupRuntime', 'Start-IsolatedBackupRun', 'Protect-File', 'Protect-CommandOutput')
foreach ($name in $wanted) {
    $functionAst = $ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name}, $true)
    if ($null -eq $functionAst) { throw 'Required source function missing.' }
    Invoke-Expression $functionAst.Extent.Text
}
$script:checks = 0
function Assert-Synthetic($condition, $message) {
    if (-not $condition) { throw $message }
    $script:checks++
}
$pin = 'a' * 64
$backupRuntime = @{
    PythonPath='C:\Synthetic Runtime\python.exe'; PythonSha256=$pin
    BootstrapPath='C:\Synthetic Runtime\bootstrap.py'; BootstrapSha256=$pin
    HelperPath='C:\Synthetic Runtime\helper.py'; HelperSha256=$pin
    PreflightPath='C:\Synthetic Runtime\preflight.py'; PreflightSha256=$pin
    CryptoPackagePath='C:\Synthetic Runtime\cryptography'; CryptoPackageSha256=$pin
    YamlPackagePath='C:\Synthetic Runtime\yaml'; YamlPackageSha256=$pin
    CffiExtensionPath='C:\Synthetic Runtime\_cffi_backend.pyd'; CffiExtensionSha256=$pin
}
$script:children = [System.Collections.Generic.List[object]]::new()
$script:failChild = $false
$script:creations = 0
function Get-Item {
    param($LiteralPath, [switch]$Force, $ErrorAction)
    $directory = $LiteralPath -in @($backupRuntime.CryptoPackagePath, $backupRuntime.YamlPackagePath)
    return [pscustomobject]@{PSIsContainer=$directory; Attributes=[System.IO.FileAttributes]::Normal}
}
function Get-FileHash { param($LiteralPath, $Algorithm) return [pscustomobject]@{Hash=$pin} }
function Invoke-BackupBootstrapProcess {
    param($Runtime, [string[]]$NativeArguments)
    $script:children.Add([pscustomobject]@{Executable=$Runtime.PythonPath; Arguments=$NativeArguments})
    if ($script:failChild) { throw 'Synthetic child failed.' }
}
function New-PrivateRunDirectory { param($Path, $Parent, $OwnerSid) $script:creations++ }

Test-IsolatedBackupRuntime -Runtime $backupRuntime
Assert-Synthetic ($script:children.Count -eq 1) 'one dependency preflight child'
$preflight = $script:children[0].Arguments
Assert-Synthetic (($preflight[0..2] -join ',') -ceq '-I,-S,-B') 'isolated no-site bytecode-disabled Python argv'
$helperIndex = [Array]::IndexOf([string[]]$preflight, '--helper')
Assert-Synthetic ($preflight[$helperIndex+1] -ceq $backupRuntime.PreflightPath) 'preflight uses only the pinned smoke helper'
$separator = [Array]::IndexOf([string[]]$preflight, '--')
Assert-Synthetic ($preflight[$separator+1] -ceq '--target-helper' -and
    $preflight[$separator+2] -ceq $backupRuntime.HelperPath) 'preflight checks target helper before execution'

$script:failChild = $true
$refused = $false
try { Start-IsolatedBackupRun $backupRuntime 'C:\Synthetic\new' 'C:\Synthetic' 'synthetic-owner' }
catch { $refused = $true }
Assert-Synthetic ($refused -and $script:creations -eq 0) 'dependency failure precedes run creation'
$script:failChild = $false
$script:children.Clear()
$backupRuntime.HelperSha256 = 'b' * 64
$refused = $false
try { Start-IsolatedBackupRun $backupRuntime 'C:\Synthetic\new' 'C:\Synthetic' 'synthetic-owner' }
catch { $refused = $true }
Assert-Synthetic ($refused -and $script:children.Count -eq 0 -and $script:creations -eq 0) 'helper pin failure precedes child/run creation'
$backupRuntime.HelperSha256 = $pin
$backupRuntime.YamlPackageSha256 = 'not-a-pin'
$refused = $false
try { Start-IsolatedBackupRun $backupRuntime 'C:\Synthetic\new' 'C:\Synthetic' 'synthetic-owner' }
catch { $refused = $true }
Assert-Synthetic ($refused -and $script:children.Count -eq 0 -and $script:creations -eq 0) 'invalid package pin precedes all side effects'
$backupRuntime.YamlPackageSha256 = $pin
Start-IsolatedBackupRun $backupRuntime 'C:\Synthetic\new' 'C:\Synthetic' 'synthetic-owner'
Assert-Synthetic ($script:children.Count -eq 1 -and $script:creations -eq 1) 'successful preflight admits one mocked private run'

# Exercise the two actual protection functions and four actual top-level helper
# call ASTs. All execution terminates at the fake process adapter above.
$script:children.Clear()
$keyFile='C:\Synthetic\key'
$agent='C:\Synthetic repo'
$MaxPlaintextBytes=130023424
$MemoryBudgetBytes=536870912
$OperationTimeoutSeconds=120
Protect-File -Source 'C:\Synthetic source\value' -Destination 'C:\Synthetic\cipher' -Report 'C:\Synthetic\report'
Protect-CommandOutput -Destination 'C:\Synthetic\cipher' -Report 'C:\Synthetic\report' `
    -Arguments @('-C', 'C:\Synthetic repo', 'diff', '--binary', 'synthetic''$()`')
$hermesHomePath='C:\Synthetic\home'
$homeInventoryDraft='C:\Synthetic\inventory'
$database=[pscustomobject]@{FullName='C:\Synthetic\source.sqlite'}
$destination='C:\Synthetic\cipher'
$report='C:\Synthetic\report'
$manifestPath='C:\Synthetic\manifest'
$manifestHash='b' * 64
$runRoot='C:\Synthetic\new'
$restoreReport='C:\Synthetic\restore'
$topCalls = @($ast.FindAll({param($node)
    if ($node -isnot [System.Management.Automation.Language.CommandAst] -or
        $node.GetCommandName() -ne 'Invoke-IsolatedBackupHelper') { return $false }
    $parent = $node.Parent
    while ($null -ne $parent) {
        if ($parent -is [System.Management.Automation.Language.FunctionDefinitionAst]) { return $false }
        $parent = $parent.Parent
    }
    return $true
}, $true))
Assert-Synthetic ($topCalls.Count -eq 4) 'four actual top-level helper call sites'
foreach ($call in $topCalls) { Invoke-Expression $call.Extent.Text }
Assert-Synthetic ($script:children.Count -eq 6) 'all six helper kinds use the bootstrap process adapter'
$observedKinds = @()
foreach ($child in $script:children) {
    $arguments = $child.Arguments
    Assert-Synthetic ($child.Executable -ceq $backupRuntime.PythonPath -and
        ($arguments[0..2] -join ',') -ceq '-I,-S,-B') 'each helper keeps isolated explicit runtime'
    $helperIndex = [Array]::IndexOf([string[]]$arguments, '--helper')
    Assert-Synthetic ($arguments[$helperIndex+1] -ceq $backupRuntime.HelperPath) 'active helper target stays pinned'
    $separator = [Array]::IndexOf([string[]]$arguments, '--')
    $observedKinds += $arguments[$separator+1]
}
Assert-Synthetic (($observedKinds | Sort-Object -Unique) -join ',' -ceq
    'encrypt-command,encrypt-file,init-key,inventory-home,sqlite-backup,verify-run') 'exactly the six approved kinds'
$commandArgs = $script:children[1].Arguments
$separator = [Array]::IndexOf([string[]]$commandArgs, '--')
$forwarded = @($commandArgs[($separator+1)..($commandArgs.Count-1)])
Assert-Synthetic ($forwarded[-1] -ceq 'synthetic''$()`' -and $forwarded[-4] -ceq 'C:\Synthetic repo') 'nested command argv is literal, including spaces and shell characters'

foreach ($name in @('PythonPath','PythonSha256','BootstrapPath','BootstrapSha256','HelperPath','HelperSha256',
                    'PreflightPath','PreflightSha256','CryptoPackagePath','CryptoPackageSha256',
                    'YamlPackagePath','YamlPackageSha256','CffiExtensionPath','CffiExtensionSha256')) {
    $parameter = @($ast.ParamBlock.Parameters | Where-Object {$_.Name.VariablePath.UserPath -eq $name})
    Assert-Synthetic ($parameter.Count -eq 1 -and $null -eq $parameter[0].DefaultValue) 'runtime inputs have no local/default-venv fallback'
}
Write-Output ("PASS $script:checks synthetic-only caller assertions; process/run creation were mocked")
