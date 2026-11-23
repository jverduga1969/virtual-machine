#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga
#
# scripts/postinstall.sh - Instalador y reparador del host.
# Marcador: postinstall_v2
#
# Hace TODO lo que requiere root, en un solo paso idempotente:
#   1) Instala los paquetes del sistema que la app necesita.
#   2) Anade al usuario a los grupos kvm, video, render, tty, audio.
#   3) Reglas udev: udmabuf (VirGL) y USB (passthrough), como las que
#      comprueba Configuracion Host -> "Comprobar de nuevo".
#   4) Los binarios que "Configuracion Host -> Comprobar de nuevo" evalua
#      (pkexec, udevadm, audio, visores, virtiofsd, samba, setxkbmap...).
#
# El antiguo Modo kiosco (Xorg en VT + wrapper sudo) se elimino del programa;
# por eso este script ya no instala Xwrapper.config, /etc/sudoers.d/ ni
# /usr/local/bin/virtual-machine-desktop.
#
# Uso:
#   sudo bash scripts/postinstall.sh
#   pkexec bash scripts/postinstall.sh            # desde Configuracion Host
#   sudo bash scripts/postinstall.sh --enable-iommu   # ademas, IOMMU en GRUB
#
# Pensado para ser invocado por:
#   * El instalador del paquete (.deb / .rpm / PKGBUILD) — en su postinstall.
#   * El boton "Reparar lo que falte" de Configuracion Host (via pkexec).

set -u
set -o pipefail

REPO_DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
MARKER="postinstall_v2"

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
            sed -n '3,27p' "$0"
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

# Los fallos de pasos imprescindibles (paquetes, grupos) cuentan: al final el
# script devuelve 1 si hubo alguno, para que Configuración Host no finja éxito.
ERRORES=0
fallo() {
    err "$*"
    ERRORES=$((ERRORES + 1))
}

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
    # dnf5 coincide con dnf en Fedora 41+: comprobarlo primero.
    if command -v dnf5    >/dev/null 2>&1; then echo dnf5;   return; fi
    if command -v dnf     >/dev/null 2>&1; then echo dnf;    return; fi
    if command -v yum     >/dev/null 2>&1; then echo yum;    return; fi
    if command -v pacman  >/dev/null 2>&1; then echo pacman; return; fi
    if command -v zypper  >/dev/null 2>&1; then echo zypper; return; fi
    if command -v apk     >/dev/null 2>&1; then echo apk;    return; fi
    echo unknown
}
PM="$(detect_pm)"
DNF_BIN=dnf
[ "$PM" = "dnf5" ] && DNF_BIN=dnf5
log "Gestor de paquetes detectado: $PM"
[ "$PM" = "unknown" ] && warn "Gestor desconocido. Se omitira la instalacion de paquetes."

# ----------------------------------------------------------------------
# Paquetes por gestor. Cada linea: "grupo:paq1,paq2,...".
# Cada grupo es independiente: si un grupo falla, se avisa y se sigue.
# ----------------------------------------------------------------------

# Los nombres estan elegidos para que "Configuracion Host -> Comprobar de
# nuevo" pueda marcar en verde: qemu-system-x86_64, swtpm, pkexec, udevadm,
# spicy, vncviewer, remote-viewer, virtiofsd, smbd y pactl/pipewire.
PKGS_APT=(
    "qemu:qemu-system-x86,qemu-utils,qemu-system-gui"  # -display sdl/gtk
    "ovmf:ovmf"
    "swtpm:swtpm,swtpm-tools"
    "virtiofsd:virtiofsd,uidmap"
    "polkit:policykit-1"  # incluye /usr/bin/pkexec en versiones antiguas
    "polkit-nuevo:pkexec"  # Debian trixie / Ubuntu 24.10 lo separan
    "sudo:sudo"
    "system:udev,util-linux"  # lsblk/losetup
    "xkb:x11-xkb-utils"  # setxkbmap, usado por vm_runner
    "spice-python:python3-gi,gir1.2-spiceclientgtk-3.0"
    "spice-client:spice-client-gtk"  # da /usr/bin/spicy
    "vncviewer:tigervnc-viewer"
    "remote-viewer:virt-viewer"
    "samba:samba"
    "dnsmasq:dnsmasq"
    "python-xlib:python3-xlib"
    "python-psutil:python3-psutil"
    "pyqt6:python3-pyqt6"
    "requests:python3-requests"
    "packaging:python3-packaging"
    "audio-pulse:pulseaudio-utils"
    "audio-pipewire:pipewire-pulse"
)
PKGS_DNF=(
    "qemu:qemu-kvm,qemu-img"
    "ovmf:edk2-ovmf"
    "swtpm:swtpm,swtpm-tools"
    "virtiofsd:virtiofsd,uidmap"
    "polkit:polkit"
    "system:sudo,util-linux"
    "xkb:xorg-x11-xkb-utils"
    "spice-python:python3-gobject,spice-gtk"
    "spice-client:spice-gtk-tools"  # da /usr/bin/spicy
    "vncviewer:tigervnc"
    "remote-viewer:virt-viewer"
    "samba:samba"
    "dnsmasq:dnsmasq"
    "python-xlib:python3-xlib"
    "python-psutil:python3-psutil"
    "pyqt6:python3-pyqt6"
    "requests:python3-requests"
    "packaging:python3-packaging"
    "audio-pipewire:pipewire-pulse"
    "audio-pulse:pulseaudio-utils"
)
PKGS_PACMAN=(
    "qemu:qemu-full"
    "ovmf:edk2-ovmf"
    "swtpm:swtpm"
    "virtiofsd:virtiofsd,shadow"  # newuidmap viene en shadow
    "polkit:polkit"
    "system:sudo,util-linux"
    "xkb:xorg-setxkbmap"
    "spice-gtk:python-gobject,spice-gtk"  # spice-gtk incluye spicy
    "vncviewer:tigervnc"
    "remote-viewer:virt-viewer"
    "samba:samba"
    "dnsmasq:dnsmasq"
    "python-xlib:python-xlib"
    "python-psutil:python-psutil"
    "pyqt6:python-pyqt6"
    "requests:python-requests"
    "packaging:python-packaging"
    "audio-pulse:pulseaudio"
    "audio-pipewire:pipewire-pulse"
)
PKGS_ZYPPER=(
    "qemu:qemu-x86,qemu-tools"
    "ovmf:qemu-ovmf-x86_64"
    "swtpm:swtpm"
    "virtiofsd:virtiofsd,uidmap"
    "polkit:polkit"
    "system:sudo,util-linux"
    "xkb:setxkbmap,xorg-x11-xkb-utils"
    "spice-python:python3-gobject,typelib-1_0-SpiceClientGtk-3_0"
    "spice-client:spice-gtk"  # da /usr/bin/spicy
    "vncviewer:tigervnc"
    "remote-viewer:virt-viewer"
    "samba:samba"
    "dnsmasq:dnsmasq"
    "python-xlib:python3-xlib"
    "python-psutil:python3-psutil"
    "pyqt6:python3-PyQt6"
    "requests:python3-requests"
    "packaging:python3-packaging"
    "audio-pipewire:pipewire-pulse"
    "audio-pulse:pulseaudio-utils"
)
# RHEL 7/8 y derivados: yum sigue presente como alias en RHEL 8.
PKGS_YUM=(
    "qemu:qemu-kvm,qemu-img"
    "ovmf:edk2-ovmf"
    "ovmf-legacy:OVMF"
    "swtpm:swtpm,swtpm-tools"
    "virtiofsd:virtiofsd,uidmap"
    "polkit:polkit"
    "system:sudo,util-linux"
    "xkb:xorg-x11-xkb-utils"
    "spice-gtk:spice-gtk,spice-gtk-tools"
    "vncviewer:tigervnc"
    "remote-viewer:virt-viewer"
    "samba:samba"
    "dnsmasq:dnsmasq"
    "python-xlib:python3-xlib"
    "python-psutil:python3-psutil"
    "pyqt6:python3-pyqt6"
    "requests:python3-requests"
    "packaging:python3-packaging"
    "audio-pipewire:pipewire-pulse"
    "audio-pulse:pulseaudio-utils"
)
# Alpine: algunos nombres pueden no existir; cada grupo falla por separado.
PKGS_APK=(
    "qemu:qemu-system-x86,qemu-img"
    "ovmf:ovmf"
    "swtpm:swtpm"
    "virtiofsd:virtiofsd,shadow"
    "polkit:polkit"
    "system:sudo,util-linux"
    "xkb:setxkbmap"
    "spice-gtk:spice-gtk,py3-gobject3"
    "vncviewer:tigervnc"
    "remote-viewer:virt-viewer"
    "samba:samba"
    "dnsmasq:dnsmasq"
    "python-xlib:py3-xlib"
    "python-psutil:py3-psutil"
    "pyqt6:py3-pyqt6"
    "requests:py3-requests"
    "packaging:py3-packaging"
    "audio:pulseaudio-utils"
)

# Utilidades que el programa invoca directamente (lsof, git, tar, xdg-open y
# notify-send). Van en un grupo aparte: si algun nombre no existe en un
# repositorio concreto se avisa, pero no se marca el postinstall como fallido.
PKGS_SUPPORT=""
case "$PM" in
    apt)         PKGS_SUPPORT="lsof,git,tar,xdg-utils,libnotify-bin" ;;
    dnf|dnf5|yum) PKGS_SUPPORT="lsof,git,tar,xdg-utils,libnotify" ;;
    pacman)      PKGS_SUPPORT="lsof,git,tar,xdg-utils,libnotify" ;;
    zypper)      PKGS_SUPPORT="lsof,git,tar,xdg-utils,libnotify-tools" ;;
    apk)         PKGS_SUPPORT="lsof,git,tar,xdg-utils,libnotify" ;;
esac

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
        fallo "$group: algunos paquetes no se pudieron instalar"
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
    "$DNF_BIN" install -y "${to_install[@]}" 2>&1 | sed 's/^/    /' || \
        fallo "$group: algunos paquetes no se pudieron instalar"
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
        fallo "$group: algunos paquetes no se pudieron instalar"
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
        fallo "$group: algunos paquetes no se pudieron instalar"
}

install_group_yum() {
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
    yum install -y "${to_install[@]}" 2>&1 | sed 's/^/    /' || \
        fallo "$group: algunos paquetes no se pudieron instalar"
}

install_group_apk() {
    local group="$1" pkgs="$2" IFS=','
    local to_install=()
    for p in $pkgs; do
        if apk info -e "$p" >/dev/null 2>&1; then
            ok "$group: $p ya instalado"
        else
            to_install+=("$p")
        fi
    done
    if [ ${#to_install[@]} -eq 0 ]; then return 0; fi
    log "$group: instalando ${to_install[*]}"
    apk add --no-cache "${to_install[@]}" 2>&1 | sed 's/^/    /' || \
        fallo "$group: algunos paquetes no se pudieron instalar"
}

# Un paquete opcional ausente no debe convertir el reparador en un fracaso:
# se instala igual, pero se devuelve el contador de errores a su valor previo.
instalar_opcional() {
    local grupo="$1" pkgs="$2" antes="$ERRORES"
    case "$PM" in
        apt)         install_group_apt "$grupo" "$pkgs" ;;
        dnf|dnf5)    install_group_dnf "$grupo" "$pkgs" ;;
        yum)         install_group_yum "$grupo" "$pkgs" ;;
        pacman)      install_group_pacman "$grupo" "$pkgs" ;;
        zypper)      install_group_zypper "$grupo" "$pkgs" ;;
        apk)         install_group_apk "$grupo" "$pkgs" ;;
    esac
    if [ "$ERRORES" -ne "$antes" ]; then
        ERRORES="$antes"
        warn "Algunas utilidades de apoyo no estan disponibles en este repositorio (no es fatal)."
    fi
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
        dnf|dnf5)
            for entry in "${PKGS_DNF[@]}"; do
                install_group_dnf "${entry%%:*}" "${entry#*:}"
            done
            ;;
        yum)
            for entry in "${PKGS_YUM[@]}"; do
                install_group_yum "${entry%%:*}" "${entry#*:}"
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
        apk)
            for entry in "${PKGS_APK[@]}"; do
                install_group_apk "${entry%%:*}" "${entry#*:}"
            done
            ;;
        *)
            warn "Sin gestor conocido; se omite la instalacion de paquetes."
            ;;
    esac
    if [ -n "$PKGS_SUPPORT" ]; then
        instalar_opcional "soporte" "$PKGS_SUPPORT"
    fi
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
    usermod -aG "$group" "$user" || fallo "no se pudo anadir a '$group'"
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

# Estos MISMOS nombres son los que comprueba HostDiagnostics.run_all().
UDEV_UDMABUF=/etc/udev/rules.d/60-virtual-machine-udmabuf.rules
UDEV_USB=/etc/udev/rules.d/50-vm-manager-usb.rules
MODULES_UDMABUF=/etc/modules-load.d/udmabuf.conf

setup_udev() {
    log "Instalando reglas udev..."
    mkdir -p /etc/udev/rules.d /etc/modules-load.d

    local udmabuf_content='# udmabuf_ui_config_v2: acceso a /dev/udmabuf para la sesion
# grafica activa. Sin esta regla, QEMU con VirGL (virtio-vga-gl,
# blob=on) aborta al intentar usar blob resources.
# Mismo contenido que services/host_passthrough.py.
KERNEL=="udmabuf", SUBSYSTEM=="misc", TAG+="uaccess"'

    local usb_content='# Virtual.Machine - permite passthrough USB al usuario activo.
# Solo se aplica a dispositivos USB.
SUBSYSTEM=="usb", ACTION=="add", TAG+="uaccess"'

    if [ -f "$UDEV_UDMABUF" ] && grep -q 'KERNEL=="udmabuf"' "$UDEV_UDMABUF" \
       && grep -q 'SUBSYSTEM=="misc"' "$UDEV_UDMABUF"; then
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

    # La regla udev solo da permisos; el modulo debe cargarse ademas.
    # Sin esto /dev/udmabuf no existe y VirGL con blob=on falla.
    if [ ! -f "$MODULES_UDMABUF" ] || ! grep -qx 'udmabuf' "$MODULES_UDMABUF"; then
        printf 'udmabuf\n' > "$MODULES_UDMABUF"
        ok "modulo udmabuf configurado para cargar en el arranque"
    else
        ok "modulo udmabuf ya configurado"
    fi
    if command -v modprobe >/dev/null 2>&1; then
        modprobe udmabuf 2>/dev/null && ok "modulo udmabuf cargado" || \
            warn "no se pudo cargar udmabuf ahora (se cargara en el proximo arranque)"
    fi

    if command -v udevadm >/dev/null 2>&1; then
        udevadm control --reload-rules 2>/dev/null || true
        udevadm trigger --name-match=udmabuf 2>/dev/null || true
        udevadm trigger --subsystem-match=usb 2>/dev/null || true
        ok "udev recargado"
    fi
}

# ----------------------------------------------------------------------
# IOMMU (opcional, --enable-iommu)
# ----------------------------------------------------------------------

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
    setup_iommu
    if [ "$ERRORES" -gt 0 ]; then
        err "Postinstall $MARKER termino con $ERRORES error(es)."
        return 1
    fi
    log "Postinstall $MARKER completado."
    echo ""
    echo "Notas:"
    echo "  - Si acabas de anadir el usuario a un grupo (kvm, tty, etc.)"
    echo "    necesitas CERRAR SESION y volver a entrar para que aplique."
    echo "  - Los cambios en reglas udev ya estan activos; si un USB"
    echo "    estaba conectado, desenchufalo y vuelve a enchufarlo."
    echo "  - Vuelve a Configuracion Host y pulsa 'Comprobar de nuevo'."
}

main "$@"

# postinstall_uidmap_v1

# postinstall_uidmap_arch_v1

# fix_grub_iommu_quotes_v1

# postinstall_v2 (sin Modo kiosco: udev/VirGL + paquetes de diagnostico)
