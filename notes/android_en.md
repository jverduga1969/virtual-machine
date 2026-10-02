**ℹ️ Notes about Android on QEMU/KVM**

**✅ Works:** create the VM, boot, VNC/SPICE console, disk-only snapshots and USB passthrough.

**❌ Not available on Android:** shared folders (9p / VirtioFS), QEMU Guest Agent, bidirectional clipboard and automount. Android-x86 / Bliss OS kernels do not include those modules. To transfer files, use ADB or the network.

**✅ Recommended ISO:** [Android-x86 9.0](https://www.android-x86.org/download.html) — tested, uses QXL automatically.

**⚠️ Bliss OS:** more modern (Android 12/13) but requires ≥8 GB RAM, 4 cores and Q35 chipset. The "Bliss-Surface" variant does not boot under QEMU. If it hangs on "Have A Truly Blissful Experience", raise RAM/cores or use Android-x86. Download: [blissos.org](https://blissos.org/)
