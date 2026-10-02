**ℹ️ Notas sobre Linux en QEMU/KVM**

**✅ Funciona:** instalación, arranque, snapshots completos y de disco, carpetas compartidas (VirtioFS / 9p), Guest Agent, clipboard bidireccional, passthrough PCI/USB y panel de recursos.

**💡 Recomendado:** VirtIO-GPU 2D o VirGL. La opción «Automático» elige lo mejor según el host.

**⚠️ VirtioFS** necesita `virtiofsd` en el host. La app puede instalarlo desde Carpetas compartidas → Dependencias.
