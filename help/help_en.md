**Virtual.Machine** is a graphical assistant for creating and managing virtual machines with QEMU/KVM.

### Getting started

- Press **New VM** in the left panel to create a virtual machine from scratch.
- Select a VM in the list to see its status and configure it.
- Use the **Start** button to boot it and the **Shut down** button to stop it.

### Right panel

- **Resource usage**: live CPU, RAM, disk and network of the VM.
- **General information**: status, PID, IP, MAC, disks, snapshots and guest integration state.
- **Last snapshot**: preview of the most recent snapshot.
- **Suggestions**: warnings and recommendations based on the VM state.

### Virtual machine tabs

- **Overview**: actions on the VM (Clone, Import, Export, Delete).
- **Settings**: hardware, storage, network, devices and advanced options.
- **Passthrough**: pass physical hardware (PCI/USB) to the VM.
- **Shared folders**: integrate the guest with the host.
- **Snapshots**: create, restore and delete snapshots.
- **Graphical Console**: view the VM inside the app (if available).
- **Progress Console**: detailed application log.

### Keyboard shortcuts

- **Ctrl+M**: open the Media menu (CD/DVD, USB).
- Inside the VNC widget: click inside to capture the keyboard. Click outside to release it.
- In VNC fullscreen: the combination configured in the Graphical Console bar (Right Ctrl by default).

### Common issues

- **The VM does not boot**: check the Progress Console. Press **VM health** for diagnostics.
- **No graphical output**: try changing the mode in Settings → Display.
- **USB does not connect**: check the permissions in Passthrough → USB permissions.
- **Special keys do not reach the guest**: on Wayland, Meta/Super and Ctrl+Alt+F* cannot be captured by design. Log in to X11 if you need them.

---

Virtual.Machine — QEMU/KVM Multi-VM Assistant.
