[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$SelfTest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-ConnectionAssessment {
    [CmdletBinding()]
    param(
        [AllowEmptyCollection()]
        [object[]]$Devices = @(),
        [ValidateSet('OK', 'UNAVAILABLE')]
        [string]$ProbeStatus = 'OK',
        [string]$ServiceState = 'Unknown',
        [string]$AppleDevicesApp = 'Unknown'
    )

    $appleDevices = @(
        $Devices | Where-Object {
            $_.FriendlyName -match '(?i)Apple iPhone|Apple Mobile Device USB|Apple Recovery \(iBoot\)|Apple DFU'
        }
    )

    $connection = if ($ProbeStatus -ne 'OK') {
        'UNKNOWN'
    }
    elseif ($appleDevices.Count -gt 0) {
        'DEVICE_DETECTED'
    }
    else {
        'NOT_DETECTED'
    }

    [pscustomobject]@{
        SchemaVersion            = '1.0'
        DeviceConnection         = $connection
        DetectedDeviceCount      = if ($ProbeStatus -eq 'OK') { $appleDevices.Count } else { $null }
        DeviceProbe              = $ProbeStatus
        AppleMobileDeviceService = $ServiceState
        AppleDevicesApp          = $AppleDevicesApp
        PasscodeState            = 'NOT_INSPECTED'
        ActivationLockState      = 'NOT_INSPECTED'
        MdmState                 = 'NOT_INSPECTED'
        DeviceTrustState         = 'NOT_INSPECTED'
        CanUnlockDevice          = $false
        DataChanged              = $false
        Note                     = 'USB presence and Windows software only; lock, ownership, and authorization states are not inspected.'
    }
}

if ($SelfTest) {
    $detected = Get-ConnectionAssessment -Devices @(
        [pscustomobject]@{ FriendlyName = 'Apple Mobile Device USB Composite Device' }
    )
    if ($detected.DeviceConnection -ne 'DEVICE_DETECTED' -or $detected.DetectedDeviceCount -ne 1) {
        throw 'Self-test failed: Apple USB device should be detected.'
    }

    $absent = Get-ConnectionAssessment -Devices @()
    if ($absent.DeviceConnection -ne 'NOT_DETECTED' -or $absent.DetectedDeviceCount -ne 0) {
        throw 'Self-test failed: empty device list should not be detected.'
    }

    $unavailable = Get-ConnectionAssessment -Devices @() -ProbeStatus 'UNAVAILABLE'
    if ($unavailable.DeviceConnection -ne 'UNKNOWN' -or $null -ne $unavailable.DetectedDeviceCount) {
        throw 'Self-test failed: unavailable probe should report UNKNOWN.'
    }

    if ($detected.PasscodeState -ne 'NOT_INSPECTED' -or
        $detected.ActivationLockState -ne 'NOT_INSPECTED' -or
        $detected.MdmState -ne 'NOT_INSPECTED' -or
        $detected.CanUnlockDevice -ne $false -or
        $detected.DataChanged -ne $false) {
        throw 'Self-test failed: security state must remain uninspected and no action may be claimed.'
    }

    Write-Output 'Windows Apple-device diagnostic self-tests: PASS (3 cases + safety invariants)'
    exit 0
}

$probeStatus = 'OK'
$devices = @()
try {
    if (-not (Get-Command Get-PnpDevice -ErrorAction SilentlyContinue)) {
        throw 'Get-PnpDevice cmdlet is unavailable on this Windows installation.'
    }
    $devices = @(Get-PnpDevice -PresentOnly -ErrorAction Stop |
        Select-Object -Property FriendlyName, Class, Status)
}
catch {
    $probeStatus = 'UNAVAILABLE'
}

$serviceState = 'Unknown'
try {
    $service = Get-Service -Name 'Apple Mobile Device Service' -ErrorAction SilentlyContinue
    $serviceState = if ($null -eq $service) { 'NOT_INSTALLED' } else { [string]$service.Status }
}
catch {
    $serviceState = 'UNKNOWN'
}

$appleDevicesApp = 'Unknown'
try {
    $packages = @(Get-AppxPackage -Name '*AppleDevices*' -ErrorAction Stop)
    $appleDevicesApp = if ($packages.Count -gt 0) { 'INSTALLED' } else { 'NOT_DETECTED' }
}
catch {
    $appleDevicesApp = 'UNKNOWN'
}

$result = Get-ConnectionAssessment -Devices $devices -ProbeStatus $probeStatus `
    -ServiceState $serviceState -AppleDevicesApp $appleDevicesApp

if ($Json) {
    $result | ConvertTo-Json -Depth 4
}
else {
    $result | Format-List
    Write-Output ''
    Write-Output 'Next step: open Apple Devices on Windows and follow the official Apple recovery instructions.'
    Write-Output 'This diagnostic is read-only. It does not unlock, restore, trust, pair, or change the device.'
}
