**ℹ️ Notes about Linux on QEMU/KVM**

**✅ Works:** installation, boot, full and disk-only snapshots, shared folders (VirtioFS / 9p), Guest Agent, bidirectional clipboard, PCI/USB passthrough and resource panel.

**💡 Recommended:** VirtIO-GPU 2D or VirGL. The "Automatic" option picks the best for your host.

**⚠️ VirtioFS** needs `virtiofsd` on the host. The app can install it from Shared folders → Dependencies.
