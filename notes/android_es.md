**ℹ️ Notas sobre Android en QEMU/KVM**

**✅ Funciona:** crear la VM, arrancar, consola VNC/SPICE, snapshots de disco y passthrough USB.

**❌ No disponible en Android:** carpetas compartidas (9p / VirtioFS), QEMU Guest Agent, clipboard bidireccional y automontaje. Los kernels de Android-x86 / Bliss OS no incluyen esos módulos. Para pasar archivos, usa ADB o la red.

**✅ ISO recomendada:** [Android-x86 9.0](https://www.android-x86.org/download.html) — probada, usa QXL automáticamente.

**⚠️ Bliss OS:** más moderno (Android 12/13) pero exige ≥8 GB RAM, 4 núcleos y chipset Q35. La variante «Bliss-Surface» no arranca bajo QEMU. Si se queda colgado en «Have A Truly Blissful Experience», sube RAM/núcleos o usa Android-x86. Descarga: [blissos.org](https://blissos.org/)
