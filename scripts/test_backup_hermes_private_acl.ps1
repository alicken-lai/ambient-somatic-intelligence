# Synthetic ACL/creation regression only. The production script is never run.
$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$source = Join-Path $PSScriptRoot 'backup_hermes_for_upgrade.ps1'
$ast = [System.Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$parseErrors)
if (@($parseErrors).Count -ne 0) { throw 'Production source parse failed.' }
$wanted = @('Test-PrivateDirectoryAcl', 'Assert-PrivateDirectory', 'Assert-NewTarget', 'New-PrivateRunDirectory')
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
$ownerSid = 'S-1-5-21-111111111-222222222-333333333-1001'
function New-SyntheticAcl {
    param([string]$Owner = $ownerSid, [bool]$Protected = $true, [switch]$ExtraRule,
          [switch]$WeakRights, [switch]$WrongInheritance, [switch]$Deny)
    $acl = [System.Security.AccessControl.DirectorySecurity]::new()
    $acl.SetOwner([System.Security.Principal.SecurityIdentifier]::new($Owner))
    $acl.SetAccessRuleProtection($Protected, $false)
    foreach ($sid in @($ownerSid, 'S-1-5-18')) {
        $rights = if ($WeakRights) { [System.Security.AccessControl.FileSystemRights]::Read } else { [System.Security.AccessControl.FileSystemRights]::FullControl }
        $inheritance = if ($WrongInheritance) { [System.Security.AccessControl.InheritanceFlags]::None } else { [System.Security.AccessControl.InheritanceFlags]3 }
        $type = if ($Deny) { [System.Security.AccessControl.AccessControlType]::Deny } else { [System.Security.AccessControl.AccessControlType]::Allow }
        $acl.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new(
            [System.Security.Principal.SecurityIdentifier]::new($sid), $rights, $inheritance,
            [System.Security.AccessControl.PropagationFlags]::None, $type))
    }
    if ($ExtraRule) {
        $acl.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new(
            [System.Security.Principal.SecurityIdentifier]::new('S-1-1-0'),
            [System.Security.AccessControl.FileSystemRights]::Read,
            [System.Security.AccessControl.InheritanceFlags]3,
            [System.Security.AccessControl.PropagationFlags]::None,
            [System.Security.AccessControl.AccessControlType]::Allow))
    }
    return $acl
}
$script:currentAcl = New-SyntheticAcl
Assert-Synthetic (Test-PrivateDirectoryAcl $script:currentAcl $ownerSid) 'exact synthetic private ACL'
foreach ($bad in @((New-SyntheticAcl -Protected $false), (New-SyntheticAcl -Owner 'S-1-5-18'),
                   (New-SyntheticAcl -ExtraRule), (New-SyntheticAcl -WeakRights),
                   (New-SyntheticAcl -WrongInheritance), (New-SyntheticAcl -Deny))) {
    Assert-Synthetic (-not (Test-PrivateDirectoryAcl $bad $ownerSid)) 'unsafe ACL must fail closed'
}
$parent = 'C:\Synthetic-Asi-Backup-Only'
$target = Join-Path $parent 'new-run'
$script:existingRun = $false
$script:atomicSuccess = $true
$script:creates = 0
$script:reparse = $false
function Get-Item { param($LiteralPath, [switch]$Force, $ErrorAction)
    $attributes = if ($script:reparse) { [System.IO.FileAttributes]::ReparsePoint } else { [System.IO.FileAttributes]::Directory }
    return [pscustomobject]@{PSIsContainer=$true; Attributes=$attributes}
}
function Get-Acl { param($LiteralPath) return $script:currentAcl }
function Test-Path { param($LiteralPath) return $script:existingRun }
function Invoke-AtomicPrivateDirectoryCreate { param($Path, $OwnerSid)
    Assert-Synthetic ($Path -eq $target) 'only new target can be created'
    $script:creates++
    return $script:atomicSuccess
}
function Set-Acl { throw 'An existing parent ACL must never be changed.' }
function icacls.exe { throw 'No ACL command is allowed in these synthetic tests.' }

Assert-PrivateDirectory $parent $ownerSid
Assert-Synthetic ($script:creates -eq 0) 'existing parent verification is read-only'
$script:currentAcl = New-SyntheticAcl -ExtraRule
$refused = $false
try { New-PrivateRunDirectory $target $parent $ownerSid } catch { $refused = $true }
Assert-Synthetic ($refused -and $script:creates -eq 0) 'invalid parent is refused without target creation'
$script:currentAcl = New-SyntheticAcl
$script:existingRun = $true
$refused = $false
try { New-PrivateRunDirectory $target $parent $ownerSid } catch { $refused = $true }
Assert-Synthetic ($refused -and $script:creates -eq 0) 'existing target is refused without creation or ACL change'
$script:existingRun = $false
$script:atomicSuccess = $false
$refused = $false
try { New-PrivateRunDirectory $target $parent $ownerSid } catch { $refused = $true }
Assert-Synthetic ($refused -and $script:creates -eq 1) 'atomic race/failure is not retried'
$script:atomicSuccess = $true
New-PrivateRunDirectory $target $parent $ownerSid
Assert-Synthetic ($script:creates -eq 2) 'successful new target is post-verified'
$script:reparse = $true
$refused = $false
try { Assert-PrivateDirectory $parent $ownerSid } catch { $refused = $true }
Assert-Synthetic $refused 'reparse directory rejected'
Write-Output ("PASS $script:checks synthetic-only ACL assertions; native creation was mocked")
