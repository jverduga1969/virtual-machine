#!/bin/bash
# run.sh — Arranca Virtual.Machine sin venv.
#
# Todas las dependencias se instalan en ~/.local/ (site-packages del usuario),
# que persiste entre sesiones y no depende de rutas del proyecto.
#
# En Arch/CachyOS se añade --break-system-packages a pip para evitar el
# bloqueo PEP 668 del Python del sistema (que de otro modo prohíbe pip).
#
# Uso: ./run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN="\033[92m"; YELLOW="\033[93m"; RED="\033[91m"; CYAN="\033[96m"; RESET="\033[0m"
info() { echo -e "${CYAN}==>${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠️${RESET}  $*"; }
fail() { echo -e "${RED}❌${RESET} $*"; }

PY="$(command -v python3)"
if [ -z "$PY" ]; then
    fail "python3 no está en PATH. Instálalo con tu gestor de paquetes."
    exit 1
fi

# ---------------------------------------------------------------------
# Función auxiliar: probar un import con el python del sistema.
# ---------------------------------------------------------------------
have() {
    "$PY" -c "import $1" >/dev/null 2>&1
}

# ---------------------------------------------------------------------
# 0. Dependencias de SISTEMA (QEMU, qemu-img, pip, libs xcb de Qt6).
#    Solo librería estándar: funciona antes de tener pip.
#    Omitir con: VM_SKIP_SYSDEPS=1 ./run.sh
# ---------------------------------------------------------------------
if [ -z "${VM_SKIP_SYSDEPS:-}" ] && [ -f "system_deps.py" ]; then
    "$PY" system_deps.py --install || \
        warn "Faltan dependencias de sistema: la app puede no abrir o no poder crear VMs (VM_SKIP_SYSDEPS=1 omite este paso)."
fi

# ---------------------------------------------------------------------
# Detectar si hace falta --break-system-packages (PEP 668: Debian 12+,
# Ubuntu 23.04+, Fedora 38+, Arch…). Solo se añade si el Python está marcado
# como "externally managed" Y este pip conoce la opción: pip antiguos
# (Ubuntu 22.04 trae 22.0.2) no la reconocen y fallarían.
# ---------------------------------------------------------------------
PIP_FLAGS="--user --quiet --disable-pip-version-check --upgrade"
if "$PY" -c "import os,sys,sysconfig; sys.exit(0 if os.path.exists(os.path.join(sysconfig.get_path('stdlib'), 'EXTERNALLY-MANAGED')) else 1)" \
   && "$PY" -m pip install --help 2>/dev/null | grep -q -- "--break-system-packages"; then
    PIP_FLAGS="$PIP_FLAGS --break-system-packages"
fi

# ---------------------------------------------------------------------
# 1. Dependencias base
# ---------------------------------------------------------------------
NEED=0
have "PyQt6"      || NEED=1
have "requests"   || NEED=1
have "packaging"  || NEED=1

if [ "$NEED" -eq 1 ]; then
    info "Instalando dependencias base en ~/.local/ (PyQt6, requests, packaging)…"
    "$PY" -m pip install $PIP_FLAGS PyQt6 requests packaging || {
        fail "Falló la instalación base. Prueba manualmente:"
        fail "  $PY -m pip install --user --break-system-packages PyQt6 requests packaging"
        exit 1
    }
fi

# ---------------------------------------------------------------------
# 2. Consola Gráfica: qvncwidget + python-xlib
# ---------------------------------------------------------------------
if ! have "qvncwidget"; then
    info "Instalando qvncwidget en ~/.local/ …"
    "$PY" -m pip install $PIP_FLAGS qvncwidget || {
        fail "No se pudo instalar qvncwidget."
        fail "  $PY -m pip install --user --break-system-packages qvncwidget"
        exit 1
    }
fi

if ! "$PY" -c "from Xlib import display" >/dev/null 2>&1; then
    info "Instalando python-xlib en ~/.local/ (opcional, teclas especiales X11)…"
    "$PY" -m pip install $PIP_FLAGS python-xlib || \
        warn "python-xlib no se pudo instalar (opcional). Las teclas especiales quedarán sin captura X11."
fi

# ---------------------------------------------------------------------
# 3. Regenerar vnc_widget/ local si falta o no se importa.
# ---------------------------------------------------------------------
if [ ! -f "vnc_widget/__init__.py" ] || \
   ! "$PY" -c "from vnc_widget import QVNCWidget" >/dev/null 2>&1; then
    if [ -f "setup_vnc_widget.py" ]; then
        info "Regenerando vnc_widget/ local…"
        "$PY" setup_vnc_widget.py || \
            warn "setup_vnc_widget.py falló; puede que la Consola Gráfica no aparezca."
    else
        warn "setup_vnc_widget.py no está en el proyecto; no se puede regenerar vnc_widget/."
    fi
fi

# ---------------------------------------------------------------------
# 4. Aviso sobre sesión gráfica (informativo).
# ---------------------------------------------------------------------
case "${XDG_SESSION_TYPE:-}" in
    wayland)
        info "Sesión Wayland: la Consola Gráfica funciona, pero las teclas"
        info "especiales (Meta/Super, Ctrl+Alt+F*) no podrán capturarse."
        info "Inicia sesión en X11 si las necesitas dentro de la VM."
        ;;
esac

# ---------------------------------------------------------------------
# 5. Arrancar
# ---------------------------------------------------------------------
info "Arrancando Virtual.Machine…"
# Forzar el estilo Fusion SOLO para esta app. Kvantum (el plugin de
# estilo de KDE) segfaulta al medir items de QListWidget con emoji
# en el texto (bug en QTextEngine::itemize). Fusion es el estilo
# por defecto de Qt: limpio, neutro, sin bugs conocidos de este tipo.
# El resto del sistema sigue usando Kvantum sin cambios.
export QT_STYLE_OVERRIDE=Fusion
exec "$PY" virtual_machine.py "$@"