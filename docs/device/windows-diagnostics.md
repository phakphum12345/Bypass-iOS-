# Windows Apple-device connection diagnostic

This is a **read-only connection diagnostic**, not an unlocking utility.

## Run

Open PowerShell in the repository folder and run:

```powershell
pwsh -NoProfile -File .\tools\windows\Inspect-AppleDeviceConnection.ps1
```

For machine-readable output:

```powershell
pwsh -NoProfile -File .\tools\windows\Inspect-AppleDeviceConnection.ps1 -Json
```

Run its offline self-tests without a connected iPhone:

```powershell
pwsh -NoProfile -File .\tools\windows\Inspect-AppleDeviceConnection.ps1 -SelfTest
```

## What it checks

- Whether Windows' Plug and Play inventory reports a matching Apple USB device.
- Whether the Apple Mobile Device Service is present and its service state can be read.
- Whether the Apple Devices Windows app package is detected for the current user.

## What it cannot determine

It does **not** inspect or infer the screen passcode, Activation Lock, Apple Account ownership, MDM enrollment, device trust, or whether the device can be unlocked. A missing USB device can mean the cable, port, driver, device mode, or connection is not detected; it does not prove the device is locked or broken. A detected device does not prove ownership or authorization.

The script does not invoke idevice tools, attempt pairing, change services, install drivers, enter recovery/DFU mode, restore the device, or write device data. It does not print serial numbers or UDIDs.

For recovery, use Apple's official instructions and understand that restoring a device can erase local data:
- [Apple iPhone Support](https://support.apple.com/iphone)
- [If you forgot your iPhone passcode](https://support.apple.com/en-us/118430)
- [Activation Lock](https://support.apple.com/en-us/108934)

## Output semantics

- `DEVICE_DETECTED`: a matching Apple USB device name was returned by Windows.
- `NOT_DETECTED`: the Windows query succeeded but found no matching device.
- `UNKNOWN`: Windows' device query could not be performed.
- `NOT_INSPECTED`: this tool deliberately does not inspect that security state.

The diagnostic is evidence about the Windows connection only, not a security decision.
