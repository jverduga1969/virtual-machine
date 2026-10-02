**ℹ️ Notes about Windows on QEMU/KVM**

**✅ Works:** installation, snapshots, shared folders (SMB), Guest Agent, clipboard via SPICE Guest Tools, PCI/USB passthrough.

**⚠️ Windows 11** requires UEFI + Secure Boot + TPM 2.0. The app applies this automatically when you choose it.

**⚠️ VirtIO Guest Tools:** install them from the app's ISO so the VirtIO disk and network are visible inside the guest.

**💡** For bidirectional clipboard and remote audio, use SPICE instead of VNC.
