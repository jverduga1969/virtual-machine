**ℹ️ Notas sobre macOS en QEMU/KVM**

**✅ Funciona:** instalación con System Recovery, OpenCore automático, arranque, snapshots de disco y carpetas compartidas SMB.

**❌ No soporta:** snapshots completos (RAM + dispositivos), VirGL / Venus, Secure Boot ni TPM 2.0.

**⚠️ AVX2:** requerido para Sonoma, Sequoia y Tahoe. La app avisa al crear la VM si tu CPU no lo tiene.

**💡 RAM mínima:** 8 GB; recomendado 16 GB y 4 núcleos.
