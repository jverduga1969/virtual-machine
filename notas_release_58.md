## Virtual Machine 58.0

Primer release con el nuevo esquema de versiones: features suben el número grande (57 → 58), fixes suben el pequeño (58.0 → 58.1).

### Novedades

#### Biblioteca de Medios — montar discos en el host

Nuevo botón "🔌 Montar en host" en la pestaña Medios. Monta un disco virtual (QCOW2 / RAW / VMDK / VDI / VHD / VHDX) en el sistema anfitrión para inspeccionar o copiar su contenido sin arrancar la VM. No toca ninguna VM: solo habilita el contenido al host.

- Backend preferido: guestmount (libguestfs, FUSE, sin root, detecta particiones y sistemas de archivos automáticamente).
- Fallback: qemu-nbd + mount con pkexec.
- Auto-desmontaje al cerrar la app + detección de montajes huérfanos al arrancar.
- Modo lectura/escritura con uid/gid correctos.
- Nombre legible del punto de montaje (ej. hd_mint-a1b2c3d4).

#### Biblioteca de Medios — crear discos

Nuevo botón "➕ Crear disco" en la fila superior de la pestaña Medios. Crea discos virtuales de cualquier formato directamente en la biblioteca:

- QCOW2 (recomendado), RAW, VMDK (VirtualBox/VMware), VDI (VirtualBox), VHD (Hyper-V antiguo), VHDX (Hyper-V moderno), IMG (disquete 720K/1.44M/2.88M).
- Preasignación opcional (fijo/dinámico) según formato.
- El archivo se guarda en MediaLibrary/ y se registra en el índice automáticamente.

#### i18n — Biblioteca de Medios en 6 idiomas

75 cadenas nuevas traducidas al inglés, francés, portugués (Brasil), italiano y alemán. Cubren los botones y mensajes de montar/desmontar, crear disco, y el combo de preasignación.

Total del proyecto: 1619 finished, 0 unfinished.

#### Cambio cosmético

El título de la ventana ya no lleva número de versión: pasa de "Virtual Machine 57 - Administrador QEMU/KVM" a "Virtual Machine - Administrador QEMU/KVM".

### Instalación

    wget https://github.com/jverduga1969/virtual-machine/releases/download/v58.0/virtual-machine-58.0-1-any.pkg.tar.zst
    sudo pacman -U virtual-machine-58.0-1-any.pkg.tar.zst

### SHA-256

19d620377b8cadd9222881b90b0904b206cb2faf8173e2cec9a75e9f1d5270dc

### Novedades internas

- media_library_host_mount_v1 — backend de montaje en host.
- media_library_create_disk_v1 — creación de discos.
- i18n_tanda6_media_library_v1 — tanda 6 de traducciones.
- Extensión de VALID_KINDS: vmdk, vdi, vhd, vhdx.
