#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga
#
# packaging/postinstall.sh - Instalador y reparador del host.
# Marcador: postinstall_v1
#
# Hace TODO lo que requiere root, en un solo paso idempotente:
#   1) Instala los paquetes del sistema que la app necesita.
#   2) Anade al usuario a los grupos kvm, video, render, tty, audio.
#   3) Reglas udev: udmabuf (VirGL) y USB (passthrough).
#   4) /etc/X11/Xwrapper.config (Modo kiosco).
#   5) Wrapper sudo de Modo kiosco + /etc/sudoers.d/ + /etc/virtual-machine.conf.
#
# Uso:
#   sudo bash packaging/postinstall.sh
#   pkexec bash packaging/postinstall.sh           # desde la app
#   sudo bash packaging/postinstall.sh --enable-iommu   # ademas, IOMMU en GRUB
#
# Pensado para ser invocado por:
#   * El instalador del paquete (.deb / .rpm / PKGBUILD) — en su postinstall.
#   * El boton "Reparar lo que falte" de Configuracion Host (via pkexec).

set -u

REPO_DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
MARKER="postinstall_v1"

# Usuario objetivo: el que invoco el script, no root.
#   pkexec -> PKEXEC_UID
#   sudo   -> SUDO_USER
#   directo como root -> fallback a la sesion activa
detect_user() {
    if [ -n "${PKEXEC_UID:-}" ]; then
        id -un "$PKEXEC_UID" 2>/dev/null && return
    fi
    if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
        echo "$SUDO_USER"; return
    fi
    logname 2>/dev/null && return
    echo ""
}
TARGET_USER="$(detect_user)"

ENABLE_IOMMU=0
for arg in "$@"; do
    case "$arg" in
        --enable-iommu) ENABLE_IOMMU=1 ;;
        --help|-h)
            sed -n '3,25p' "$0"
            exit 0
            ;;
    esac
done

# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------

log()   { printf '==> %s\n'  "$*"; }
warn()  { printf '[AVISO] %s\n' "$*"; }
ok()    { printf '✓ %s\n'    "$*"; }
err()   { printf '[ERROR] %s\n' "$*" >&2; }

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        err "Este script necesita ejecutarse como root."
        err "Usa: sudo bash $0  (o  pkexec bash $0)"
        exit 1
    fi
}

# ----------------------------------------------------------------------
# Deteccion de distro / gestor de paquetes
# ----------------------------------------------------------------------

detect_pm() {
    if command -v apt-get >/dev/null 2>&1; then echo apt;    return; fi
    if command -v dnf     >/dev/null 2>&1; then echo dnf;    return; fi
    if command -v pacman  >/dev/null 2>&1; then echo pacman; return; fi
    if command -v zypper  >/dev/null 2>&1; then echo zypper; return; fi
    echo unknown
}
PM="$(detect_pm)"
log "Gestor de paquetes detectado: $PM"
[ "$PM" = "unknown" ] && warn "Gestor desconocido. Se omitira la instalacion de paquetes."

# ----------------------------------------------------------------------
# Paquetes por gestor. Cada linea: "grupo:paq1,paq2,...".
# Cada grupo es independiente: si un grupo falla, se avisa y se sigue.
# ----------------------------------------------------------------------

PKGS_APT=(
    "qemu:qemu-system-x86,qemu-utils"
    "ovmf:ovmf"
    "swtpm:swtpm,swtpm-tools"
    "virtiofsd:virtiofsd,uidmap"
    "polkit:policykit-1,pkexec"
    "xinit:xinit"
    "matchbox:matchbox-window-manager"
    "xorg:xserver-xorg-core"
    "spice-gtk:python3-gi,gir1.2-spiceclientgtk-3.0"
    "vncviewer:tigervnc-viewer"
    "remote-viewer:virt-viewer"
    "samba:samba"
    "dnsmasq:dnsmasq"
    "python-xlib:python3-xlib"
    "pyqt6:python3-pyqt6"
    "requests:python3-requests"
    "packaging:python3-packaging"
)
PKGS_DNF=(
    "qemu:qemu-kvm-core,qemu-img"
    "ovmf:edk2-ovmf"
    "swtpm:swtpm,swtpm-tools"
    "virtiofsd:virtiofsd,uidmap"
    "polkit:polkit"
    "xinit:xorg-x11-xinit"
    "matchbox:matchbox-window-manager"
    "xorg:xorg-x11-server-Xorg"
    "spice-gtk:python3-gobject,spice-gtk"
    "vncviewer:tigervnc"
    "remote-viewer:virt-viewer"
    "samba:samba"
    "dnsmasq:dnsmasq"
    "python-xlib:python3-xlib"
    "pyqt6:python3-qt6"
    "requests:python3-requests"
    "packaging:python3-packaging"
)
PKGS_PACMAN=(
    "qemu:qemu-full"
    "ovmf:edk2-ovmf"
    "swtpm:swtpm"
    "virtiofsd:virtiofsd"  # newuidmap viene en shadow
    "polkit:polkit"
    "xinit:xorg-xinit"
    "matchbox:matchbox-window-manager"
    "xorg:xorg-server"
    "spice-gtk:python-gobject,spice-gtk"
    "vncviewer:tigervnc"
    "remote-viewer:virt-viewer"
    "samba:samba"
    "dnsmasq:dnsmasq"
    "python-xlib:python-xlib"
    "pyqt6:python-pyqt6"
    "requests:python-requests"
    "packaging:python-packaging"
)
PKGS_ZYPPER=(
    "qemu:qemu-x86,qemu-tools"
    "ovmf:qemu-ovmf-x86_64"
    "swtpm:swtpm"
    "virtiofsd:virtiofsd,uidmap"
    "polkit:polkit"
    "xinit:xinit"
    "matchbox:matchbox-window-manager"
    "xorg:xorg-x11-server"
    "spice-gtk:python3-gobject,typelib-1_0-SpiceClientGtk-3_0"
    "vncviewer:tigervnc"
    "remote-viewer:virt-viewer"
    "samba:samba"
    "dnsmasq:dnsmasq"
    "python-xlib:python3-xlib"
    "pyqt6:python3-PyQt6"
    "requests:python3-requests"
    "packaging:python3-packaging"
)

# ----------------------------------------------------------------------
# Instalacion de paquetes
# ----------------------------------------------------------------------

install_group_apt() {
    local group="$1" pkgs="$2" IFS=','
    local to_install=()
    for p in $pkgs; do
        if dpkg -s "$p" >/dev/null 2>&1; then
            ok "$group: $p ya instalado"
        else
            to_install+=("$p")
        fi
    done
    if [ ${#to_install[@]} -eq 0 ]; then return 0; fi
    log "$group: instalando ${to_install[*]}"
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        "${to_install[@]}" 2>&1 | sed 's/^/    /' || \
        warn "$group: algunos paquetes no se pudieron instalar"
}

install_group_dnf() {
    local group="$1" pkgs="$2" IFS=','
    local to_install=()
    for p in $pkgs; do
        if rpm -q "$p" >/dev/null 2>&1; then
            ok "$group: $p ya instalado"
        else
            to_install+=("$p")
        fi
    done
    if [ ${#to_install[@]} -eq 0 ]; then return 0; fi
    log "$group: instalando ${to_install[*]}"
    dnf install -y "${to_install[@]}" 2>&1 | sed 's/^/    /' || \
        warn "$group: algunos paquetes no se pudieron instalar"
}

install_group_pacman() {
    local group="$1" pkgs="$2" IFS=','
    local to_install=()
    for p in $pkgs; do
        if pacman -Qi "$p" >/dev/null 2>&1; then
            ok "$group: $p ya instalado"
        else
            to_install+=("$p")
        fi
    done
    if [ ${#to_install[@]} -eq 0 ]; then return 0; fi
    log "$group: instalando ${to_install[*]}"
    pacman -S --noconfirm --needed "${to_install[@]}" 2>&1 | sed 's/^/    /' || \
        warn "$group: algunos paquetes no se pudieron instalar"
}

install_group_zypper() {
    local group="$1" pkgs="$2" IFS=','
    local to_install=()
    for p in $pkgs; do
        if rpm -q "$p" >/dev/null 2>&1; then
            ok "$group: $p ya instalado"
        else
            to_install+=("$p")
        fi
    done
    if [ ${#to_install[@]} -eq 0 ]; then return 0; fi
    log "$group: instalando ${to_install[*]}"
    zypper --non-interactive install "${to_install[@]}" 2>&1 | sed 's/^/    /' || \
        warn "$group: algunos paquetes no se pudieron instalar"
}

install_packages() {
    case "$PM" in
        apt)
            log "Actualizando indices de paquetes (apt-get update)..."
            apt-get update -qq 2>&1 | sed 's/^/    /' || \
                warn "apt-get update fallo; se intentara instalar con el indice actual"
            for entry in "${PKGS_APT[@]}"; do
                install_group_apt "${entry%%:*}" "${entry#*:}"
            done
            ;;
        dnf)
            for entry in "${PKGS_DNF[@]}"; do
                install_group_dnf "${entry%%:*}" "${entry#*:}"
            done
            ;;
        pacman)
            for entry in "${PKGS_PACMAN[@]}"; do
                install_group_pacman "${entry%%:*}" "${entry#*:}"
            done
            ;;
        zypper)
            for entry in "${PKGS_ZYPPER[@]}"; do
                install_group_zypper "${entry%%:*}" "${entry#*:}"
            done
            ;;
        *)
            warn "Sin gestor conocido; se omite la instalacion de paquetes."
            ;;
    esac
}

# ----------------------------------------------------------------------
# Grupos del usuario
# ----------------------------------------------------------------------

ensure_group_membership() {
    local user="$1" group="$2"
    if ! getent group "$group" >/dev/null 2>&1; then
        warn "grupo '$group' no existe en el sistema; se omite"
        return
    fi
    if id -nG "$user" 2>/dev/null | tr ' ' '\n' | grep -qx "$group"; then
        ok "usuario '$user' ya esta en el grupo '$group'"
        return
    fi
    log "anadiendo '$user' al grupo '$group'"
    usermod -aG "$group" "$user" || warn "no se pudo anadir a '$group'"
}

setup_groups() {
    if [ -z "$TARGET_USER" ]; then
        warn "no pude detectar el usuario objetivo; se omiten los grupos"
        return
    fi
    log "Ajustando grupos del usuario '$TARGET_USER'..."
    for g in kvm video render tty audio; do
        ensure_group_membership "$TARGET_USER" "$g"
    done
}

# ----------------------------------------------------------------------
# Reglas udev
# ----------------------------------------------------------------------

UDEV_UDMABUF=/etc/udev/rules.d/60-virtual-machine-udmabuf.rules
UDEV_USB=/etc/udev/rules.d/50-vm-manager-usb.rules

setup_udev() {
    log "Instalando reglas udev..."
    mkdir -p /etc/udev/rules.d

    local udmabuf_content='# udmabuf_ui_config_v1: acceso a /dev/udmabuf para la sesion
# grafica activa. Sin esta regla, QEMU con VirGL (virtio-vga-gl,
# blob=true) aborta al intentar usar blob resources.
KERNEL=="udmabuf", TAG+="uaccess"'

    local usb_content='# Virtual.Machine - permite passthrough USB al usuario activo.
# Instalado por packaging/postinstall.sh. Solo se aplica a dispositivos USB.
SUBSYSTEM=="usb", ACTION=="add", TAG+="uaccess"'

    if [ -f "$UDEV_UDMABUF" ] && grep -q 'KERNEL=="udmabuf"' "$UDEV_UDMABUF"; then
        ok "regla udev udmabuf ya presente"
    else
        printf '%s\n' "$udmabuf_content" > "$UDEV_UDMABUF"
        chmod 644 "$UDEV_UDMABUF"
        ok "regla udev udmabuf instalada"
    fi

    if [ -f "$UDEV_USB" ] && grep -q 'SUBSYSTEM=="usb"' "$UDEV_USB"; then
        ok "regla udev USB ya presente"
    else
        printf '%s\n' "$usb_content" > "$UDEV_USB"
        chmod 644 "$UDEV_USB"
        ok "regla udev USB instalada"
    fi

    if command -v udevadm >/dev/null 2>&1; then
        udevadm control --reload-rules 2>/dev/null || true
        udevadm trigger --name-match=udmabuf 2>/dev/null || true
        udevadm trigger --subsystem-match=usb 2>/dev/null || true
        ok "udev recargado"
    fi
}

# ----------------------------------------------------------------------
# Xwrapper.config (Modo kiosco)
# ----------------------------------------------------------------------

XWRAPPER=/etc/X11/Xwrapper.config

setup_xwrapper() {
    log "Configurando $XWRAPPER..."
    mkdir -p /etc/X11
    local tmp
    tmp="$(mktemp)"
    if [ -f "$XWRAPPER" ]; then
        # Conservar el resto del archivo; solo forzar las dos claves.
        grep -v -E '^\s*(allowed_users|needs_root_rights)\s*=' \
            "$XWRAPPER" > "$tmp" 2>/dev/null || : > "$tmp"
    else
        : > "$tmp"
    fi
    {
        cat "$tmp"
        echo "allowed_users=anybody"
        echo "needs_root_rights=yes"
    } > "$XWRAPPER"
    rm -f "$tmp"
    chmod 644 "$XWRAPPER"
    ok "$XWRAPPER listo"
}

# ----------------------------------------------------------------------
# Wrapper sudo + /etc/sudoers.d + /etc/virtual-machine.conf
# ----------------------------------------------------------------------

WRAPPER_SRC="$REPO_DIR/packaging/virtual-machine-desktop"
WRAPPER_DST=/usr/local/bin/virtual-machine-desktop
SUDOERS_FILE=/etc/sudoers.d/virtual-machine-desktop
CONF_FILE=/etc/virtual-machine.conf

setup_wrapper() {
    if [ ! -f "$WRAPPER_SRC" ]; then
        warn "no encontre $WRAPPER_SRC; se omite el wrapper sudo"
        return
    fi
    log "Instalando wrapper sudo de Modo kiosco..."
    install -m 0755 -o root -g root "$WRAPPER_SRC" "$WRAPPER_DST"
    ok "wrapper instalado en $WRAPPER_DST"

    # /etc/virtual-machine.conf
    if [ -f "$CONF_FILE" ] && grep -q "^REPO_DIR=" "$CONF_FILE"; then
        # Refrescar REPO_DIR por si el usuario movio el repo.
        sed -i "s|^REPO_DIR=.*|REPO_DIR=$REPO_DIR|" "$CONF_FILE"
        ok "$CONF_FILE actualizado (REPO_DIR=$REPO_DIR)"
    else
        printf 'REPO_DIR=%s\n' "$REPO_DIR" > "$CONF_FILE"
        [ -n "$TARGET_USER" ] && printf 'USER=%s\n' "$TARGET_USER" >> "$CONF_FILE"
        chmod 644 "$CONF_FILE"
        ok "$CONF_FILE creado"
    fi

    # Regla sudoers: solo el wrapper, sin contrasena.
    if [ -z "$TARGET_USER" ]; then
        warn "sin usuario objetivo; se omite la regla sudoers"
        return
    fi
    local tmp
    tmp="$(mktemp)"
    printf '%s ALL=(root) NOPASSWD: %s\n' "$TARGET_USER" "$WRAPPER_DST" > "$tmp"
    chmod 0440 "$tmp"

    if command -v visudo >/dev/null 2>&1; then
        if ! visudo -c -f "$tmp" >/dev/null 2>&1; then
            err "la regla sudoers nueva no pasa visudo -c; se aborta"
            rm -f "$tmp"
            return
        fi
    fi

    # sudoers_perms_v1: 0644 para que la app pueda leer el archivo
    # (sudo lo acepta; rechaza solo los world-writable 0666+).
    install -m 0644 -o root -g root "$tmp" "$SUDOERS_FILE"
    rm -f "$tmp"
    ok "regla sudoers instalada en $SUDOERS_FILE"
}

# ----------------------------------------------------------------------
# IOMMU (opcional, --enable-iommu)
# ----------------------------------------------------------------------
#
# Marcador: postinstall_iommu_multiboot_v1
#
# Soporta GRUB, Limine y systemd-boot. Detecta el vendor de CPU para
# elegir el parametro correcto (intel_iommu=on / amd_iommu=on). Anade
# siempre iommu=pt (passthrough-friendly).

IOMMU_PARAMS=""

detect_cpu_vendor() {
    if grep -q "GenuineIntel" /proc/cpuinfo 2>/dev/null; then
        echo "intel"
    elif grep -q "AuthenticAMD" /proc/cpuinfo 2>/dev/null; then
        echo "amd"
    else
        echo "unknown"
    fi
}

detect_bootloader() {
    if [ -f /boot/limine.conf ] || [ -f /boot/limine.cfg ] \
       || [ -f /etc/default/limine ]; then
        echo "limine"; return
    fi
    if [ -d /boot/loader/entries ] || [ -f /etc/kernel/cmdline ]; then
        echo "systemd-boot"; return
    fi
    if [ -f /boot/grub/grub.cfg ] || [ -f /etc/default/grub ]; then
        echo "grub"; return
    fi
    echo "unknown"
}

build_iommu_params() {
    case "$1" in
        intel) echo "intel_iommu=on iommu=pt" ;;
        amd)   echo "amd_iommu=on iommu=pt"   ;;
        *)     echo ""                         ;;
    esac
}

iommu_already_active() {
    grep -qE 'intel_iommu=on|amd_iommu=on|iommu=on' /proc/cmdline
}

setup_iommu_grub() {
    local params="$1"
    if [ ! -f /etc/default/grub ]; then
        warn "no existe /etc/default/grub; se omite IOMMU (GRUB)"
        return 1
    fi
    if grep -qE 'intel_iommu=on|amd_iommu=on|iommu=on' /etc/default/grub; then
        ok "IOMMU ya estaba en /etc/default/grub"
    else
        cp -a /etc/default/grub "/etc/default/grub.vm-backup-$(date +%Y%m%d-%H%M%S)"
        GRUB_PARAMS="$params" python3 - << 'PYEDIT'
import os
import re
from pathlib import Path

path = Path("/etc/default/grub")
text = path.read_text(encoding="utf-8")
params = os.environ["GRUB_PARAMS"]

pattern = re.compile(
    r'^(GRUB_CMDLINE_LINUX_DEFAULT\s*=\s*)([\'"])(.*?)(\2)',
    re.MULTILINE,
)

def replace(m):
    prefix, quote, value, _close = m.groups()
    value = value.strip()
    if value:
        value = value + " " + params
    else:
        value = params
    return f"{prefix}{quote}{value}{quote}"

new_text, n = pattern.subn(replace, text)
if n == 0:
    new_text = text.rstrip("\n") + f"\nGRUB_CMDLINE_LINUX_DEFAULT='{params}'\n"

path.write_text(new_text, encoding="utf-8")
print(f"Lineas modificadas: {n}")
PYEDIT
        ok "/etc/default/grub modificado (backup guardado)"
    fi
    if command -v grub-mkconfig >/dev/null 2>&1; then
        grub-mkconfig -o /boot/grub/grub.cfg 2>&1 | sed 's/^/    /' || warn "grub-mkconfig fallo"
    elif command -v update-grub >/dev/null 2>&1; then
        update-grub 2>&1 | sed 's/^/    /' || warn "update-grub fallo"
    else
        warn "ni grub-mkconfig ni update-grub disponibles"
        return 1
    fi
    return 0
}

setup_iommu_limine() {
    local params="$1"
    local conf=""
    for c in /etc/default/limine /boot/limine.conf /boot/limine.cfg; do
        [ -f "$c" ] && { conf="$c"; break; }
    done
    if [ -z "$conf" ]; then
        warn "no encontre configuracion de Limine; se omite IOMMU"
        return 1
    fi
    if grep -qE 'intel_iommu=on|amd_iommu=on|iommu=on' "$conf"; then
        ok "IOMMU ya estaba en $conf"
    else
        cp -a "$conf" "$conf.vm-backup-$(date +%Y%m%d-%H%M%S)"
        if grep -q "^KERNEL_CMDLINE" "$conf"; then
            sed -i "s|^\(KERNEL_CMDLINE=\[[^]]*\)\]|\1 $params]|" "$conf"
            if ! grep -qE 'intel_iommu=on|amd_iommu=on|iommu=on' "$conf"; then
                sed -i "s|^\(KERNEL_CMDLINE=\"[^\"]*\)\"|\1 $params\"|" "$conf"
            fi
        else
            printf 'KERNEL_CMDLINE[default]+="%s"\n' "$params" >> "$conf"
        fi
        ok "$conf modificado (backup guardado)"
    fi
    if command -v limine-update >/dev/null 2>&1; then
        limine-update 2>&1 | sed 's/^/    /' || warn "limine-update fallo"
    elif command -v limine >/dev/null 2>&1; then
        limine 2>&1 | sed 's/^/    /' || true
    else
        warn "no encontre limine-update; edita manualmente"
        return 1
    fi
    return 0
}

setup_iommu_systemd_boot() {
    local params="$1"
    local cmdline="/etc/kernel/cmdline"
    if [ ! -f "$cmdline" ]; then
        warn "no existe $cmdline; se omite IOMMU (systemd-boot)"
        return 1
    fi
    if grep -qE 'intel_iommu=on|amd_iommu=on|iommu=on' "$cmdline"; then
        ok "IOMMU ya estaba en $cmdline"
    else
        cp -a "$cmdline" "$cmdline.vm-backup-$(date +%Y%m%d-%H%M%S)"
        printf " %s" "$params" >> "$cmdline"
        ok "$cmdline modificado (backup guardado)"
    fi
    if command -v sdboot-manage >/dev/null 2>&1; then
        sdboot-manage gen 2>&1 | sed 's/^/    /' || warn "sdboot-manage gen fallo"
    elif command -v bootctl >/dev/null 2>&1; then
        if command -v kernel-install >/dev/null 2>&1; then
            kernel-install add "$(uname -r)" "/boot/vmlinuz-$(uname -r)" 2>&1 | sed 's/^/    /' || warn "kernel-install fallo"
        else
            warn "regenera las entradas de systemd-boot manualmente"
            return 1
        fi
    else
        warn "no encontre bootctl ni sdboot-manage"
        return 1
    fi
    return 0
}

setup_iommu() {
    if [ "$ENABLE_IOMMU" -ne 1 ]; then return; fi
    if iommu_already_active; then
        ok "IOMMU ya activo en el arranque actual"
        return
    fi
    local vendor
    vendor="$(detect_cpu_vendor)"
    if [ "$vendor" = "unknown" ]; then
        warn "no pude detectar el vendor de CPU; se omite IOMMU"
        return
    fi
    ok "CPU detectada: $vendor"
    IOMMU_PARAMS="$(build_iommu_params "$vendor")"
    if [ -z "$IOMMU_PARAMS" ]; then
        warn "no pude construir los parametros de IOMMU"
        return
    fi
    log "Parametros a anadir: $IOMMU_PARAMS"
    local bl
    bl="$(detect_bootloader)"
    log "Gestor de arranque detectado: $bl"
    case "$bl" in
        grub)         setup_iommu_grub "$IOMMU_PARAMS" ;;
        limine)       setup_iommu_limine "$IOMMU_PARAMS" ;;
        systemd-boot) setup_iommu_systemd_boot "$IOMMU_PARAMS" ;;
        *)
            warn "no pude detectar el gestor de arranque."
            warn "Anade manualmente a la linea del kernel:"
            warn "  $IOMMU_PARAMS"
            return
            ;;
    esac
    if [ $? -eq 0 ]; then
        warn "IOMMU se aplicara en el proximo reinicio."
        warn "Recuerda tambien habilitar VT-d / AMD-Vi en la BIOS/UEFI."
    fi
}

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

main() {
    require_root
    log "Postinstall $MARKER iniciado (repo: $REPO_DIR, usuario: ${TARGET_USER:-?})"
    install_packages
    setup_groups
    setup_udev
    setup_xwrapper
    setup_wrapper
    setup_iommu
    log "Postinstall $MARKER completado."
    echo ""
    echo "Notas:"
    echo "  - Si acabas de anadir el usuario a un grupo (kvm, tty, etc.)"
    echo "    necesitas CERRAR SESION y volver a entrar para que aplique."
    echo "  - Los cambios en reglas udev ya estan activos; si un USB"
    echo "    estaba conectado, desenchufalo y vuelve a enchufarlo."
    echo "  - Vuelve a Configuracion Host y pulsa 'Comprobar'."
}

main "$@"

# postinstall_uidmap_v1

# postinstall_uidmap_arch_v1

# fix_grub_iommu_quotes_v1
