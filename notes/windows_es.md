**ℹ️ Notas sobre Windows en QEMU/KVM**

**✅ Funciona:** instalación, snapshots, carpetas compartidas (SMB), Guest Agent, clipboard con SPICE Guest Tools, passthrough PCI/USB.

**⚠️ Windows 11** exige UEFI + Secure Boot + TPM 2.0. La app lo aplica automáticamente al elegirlo.

**⚠️ VirtIO Guest Tools:** instálalos desde la ISO de la app para que el disco y la red VirtIO se vean dentro del guest.

**💡** Para clipboard bidireccional y audio remoto, usa SPICE en vez de VNC.
