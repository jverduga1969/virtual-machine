**ℹ️ Notes about macOS on QEMU/KVM**

**✅ Works:** installation with System Recovery, automatic OpenCore, boot, disk-only snapshots and shared folders (SMB).

**❌ Not supported:** full snapshots (RAM + devices), VirGL / Venus, Secure Boot or TPM 2.0.

**⚠️ AVX2:** required for Sonoma, Sequoia and Tahoe. The app warns you when creating the VM if your CPU does not have it.

**💡 Minimum RAM:** 8 GB; 16 GB and 4 cores recommended.
