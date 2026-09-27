# Consola Gráfica — VNC y SPICE

Guía de uso y referencia de la consola remota de **Virtual.Machine**:
qué modos existen, cuál elegir según tu entorno, y cómo resolver los
problemas más frecuentes.

## 1. Los dos protocolos

| Protocolo | Pros | Contras |
|---|---|---|
| **VNC** | Compatible con cualquier gráfico virtual. Se puede embeber incluso en Wayland. Muchos visores externos. Sin dependencias en el guest. | Sin aceleración 3D ni streaming de video. Clipboard limitado. Sin audio remoto. |
| **SPICE** | Mejor rendimiento en local. Clipboard bidireccional avanzado (con spice-vdagent). Audio remoto integrado. Varios monitores, redirección USB. | No se puede embeber en Wayland. Requiere visor externo si no se puede embeber. Requiere spice-vdagent en el guest. Incompatible con VirGL/Venus. |

## 2. Los cuatro modos

| Modo | Qué hace | Cuándo usarlo |
|---|---|---|
| **Embebida** | La pantalla vive dentro de la app. | Uso habitual. |
| **Ventana externa** | Se lanza el visor del sistema. | Cuando embebida no funciona (SPICE en Wayland). |
| **Ventana nativa de QEMU** | QEMU abre su propia ventana GTK/SDL. | Único modo compatible con VirGL y Venus. |
| **Híbrida** | VNC embebido + SPICE externo a la vez. | Ver dentro de la app Y tener SPICE en paralelo. |

## 3. Diagrama de decisión

    ¿Qué gráficos usas?
    ├── VirtIO-GPU 2D / QXL / std
    │   ├── ¿X11 con spice-gtk Python?
    │   │   ├── Sí → SPICE + Embebida
    │   │   └── No → VNC + Embebida
    │   └── ¿Quieres además ventana externa?
    │       └── Sí → Híbrida
    └── VirGL / Venus → Ventana nativa de QEMU

## 4. Dónde se configura

**Configuración → Pantalla → Consola remota**.

El toolbar de la pestaña *Consola Gráfica* contiene las acciones:
- **↗ Abrir en ventana externa**
- **☐ Pantalla completa** (para el visor externo)
- **Salir con:** combinación para salir de la pantalla completa del widget VNC
- **☐ Tamaño real (con scroll)**
- **🔄 Reconectar**

## 5. Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl+M` | Abrir el menú de Medios (CD/DVD + USB). |
| `Ctrl+R` | Reconectar el widget VNC/SPICE. |
| `Ctrl+Alt+C` | Alternar entre Consola Gráfica y la pestaña anterior. |

## 6. Dependencias por sistema

**VNC ventana externa:**

    # Arch / CachyOS
    sudo pacman -S gtk-vnc tigervnc

    # Debian / Ubuntu
    sudo apt install gvncviewer tigervnc-viewer

**SPICE embebida (X11):**

    # Debian / Ubuntu
    sudo apt install python3-gi gir1.2-spiceclientgtk-3.0

    # Arch / CachyOS
    sudo pacman -S python-gobject spice-gtk

**SPICE ventana externa:**

    # Arch / CachyOS
    sudo pacman -S spice-gtk virt-viewer

    # Debian / Ubuntu
    sudo apt install spice-client-gtk virt-viewer

## 7. Troubleshooting

### SPICE embebida cae a visor externo

Esperado en Wayland: XEmbed no existe. Opciones: usar VNC embebido, iniciar en X11, o aceptar el visor externo para SPICE.

### No se ve ninguna ventana al pulsar ↗

No hay visor externo instalado. Instala uno de la sección 6.

### El visor externo no se abre a pantalla completa

Algunos visores no soportan la bandera por CLI (gvncviewer). Prueba con spicy o remote-viewer.

### Al cambiar de VM en la lista, la consola sigue mostrando la anterior

Bug corregido. Al cambiar de VM, el widget embebido se destruye y se crea uno nuevo. Los visores externos son persistentes por VM.

### El clipboard no funciona entre host y guest

Para SPICE:
1. Activar Guest Agent en *Carpetas compartidas → Guest Tools*.
2. Instalar `spice-vdagent` en el guest.
3. Reiniciar el guest.
4. En *Información general* debe aparecer `spice-vdagent: activo`.

Para VNC: solo texto, requiere `vncconfig` en el guest.

### La combinación para salir de pantalla completa no funciona

En Wayland, el compositor se reserva Meta/Super y Ctrl+Alt+F* por diseño. Cambia la combinación en el combo *Salir con:* o inicia sesión en X11.

### La ventana del visor externo no sube al frente al clic en la lista

Requiere `wmctrl`:

    sudo pacman -S wmctrl      # Arch / CachyOS
    sudo apt install wmctrl    # Debian / Ubuntu

## 8. Archivos implicados

| Archivo | Rol |
|---|---|
| `console_backend.py` | Constantes, sockets, argumentos QEMU, localizadores de visores. |
| `console_ui_mixin.py` | Lógica de configuración (combos, ayuda, guardado). |
| `vnc_widget_centered.py` | Widget Qt con centrado y modo "tamaño real". |
| `spice_widget.py` | Widget GTK embebido vía XEmbed, con fallback a externo. |
| `vnc_focus_filter.py` | Captura de foco + XGrabKeyboard. |
| `x11_keyboard_grab.py` | Wrapper de XGrabKeyboard (solo X11). |