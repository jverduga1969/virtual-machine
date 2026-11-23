import html
import logging
import platform
import re
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QSplitter, QTextBrowser, QPushButton,
)

from core.plugin_base import PluginBase
from core.i18n import translate_html, tr

log = logging.getLogger(__name__)

APP_NAME = "Virtual Machine"
APP_VERSION = "1.0.0"

CSS = """
<style>
  body { font-family: sans-serif; }
  h1 { font-size: 20px; margin-bottom: 4px; }
  h2 { font-size: 16px; margin-top: 18px; margin-bottom: 6px; }
  h3 { font-size: 14px; margin-top: 14px; margin-bottom: 4px; }
  p, li { font-size: 13px; line-height: 1.5; }
  ul, ol { margin-left: 18px; }
  code { font-family: monospace; background-color: rgba(127,127,127,0.18); padding: 1px 4px; border-radius: 3px; }
  table { border-collapse: collapse; margin-top: 6px; }
  th, td { border: 1px solid rgba(127,127,127,0.5); padding: 4px 8px; font-size: 13px; text-align: left; }
  .muted { color: rgba(127,127,127,0.95); }
  .ok { color: #4caf50; font-weight: bold; }
  .warn { color: #ff9800; font-weight: bold; }
  .err { color: #f44336; font-weight: bold; }
</style>
"""


def _page(title: str, body: str) -> str:
    return f"{CSS}<h1>{title}</h1>{body}"


# ======================================================================
# TEMAS DE AYUDA
# ======================================================================
TOPICS: list[tuple[str, str, str]] = []


def _register(key: str, title: str, body: str):
    TOPICS.append((key, title, _page(title, body)))


_register(
    "inicio", "Inicio rápido",
    """
<p>Flujo básico para crear y arrancar tu primera máquina virtual:</p>
<ol>
  <li>Pulsa <b>➕ Nueva VM</b> en el panel izquierdo (o <b>➕ Crear una VM nueva</b> en la pantalla de bienvenida) y elige nombre y sistema operativo.</li>
  <li>Revisa la <b>Configuración VM</b>: perfiles predefinidos, CPU, memoria, disco y red. Pulsa <b>💾 Guardar configuración</b>.</li>
  <li>Si el sistema lo permite, la ISO se descarga automáticamente al arrancar; también puedes elegir una imagen desde <b>Medios</b>.</li>
  <li>Con la VM seleccionada, pulsa <b>▶ Iniciar</b>.</li>
  <li>En la pestaña <b>Consola Gráfica</b> verás la pantalla de la máquina.</li>
</ol>
<p class="muted">Consejo: la pestaña <b>Resumen</b> muestra el estado y las acciones rápidas (clonar, importar, exportar, notas), y el panel derecho muestra el uso de recursos en vivo.</p>
""",
)

_register(
    "pestanas", "Pestañas del sistema",
    """
<p>La ventana principal organiza el trabajo en pestañas, en este orden:</p>
<table>
  <tr><th>Pestaña</th><th>Qué encontrarás</th></tr>
  <tr><td><b>Resumen</b></td><td>Ficha de la VM seleccionada y datos del host; acciones clonar, importar, exportar, notas y eliminar.</td></tr>
  <tr><td><b>Configuración VM</b></td><td>Editor de la VM: sistema, procesador, memoria, pantalla, almacenamiento, red, dispositivos, passthrough y compartición.</td></tr>
  <tr><td><b>Configuración Host</b></td><td>Apariencia, API REST, soporte macOS, OVMF, USB (Windows), rutas de almacenamiento y diagnóstico/reparación del anfitrión.</td></tr>
  <tr><td><b>Snapshots</b></td><td>Puntos de restauración: crear, restaurar, eliminar y snapshots automáticos programados.</td></tr>
  <tr><td><b>Medios</b></td><td>Biblioteca de ISOs y discos: añadir, crear, verificar, compactar y ver qué VM los usa.</td></tr>
  <tr><td><b>Consola Gráfica</b></td><td>Visor de la pantalla de la VM (VNC embebido), con zoom y pantalla completa.</td></tr>
  <tr><td><b>Consola de Progreso</b></td><td>Registro en vivo de la aplicación y de QEMU, con filtros y exportación.</td></tr>
  <tr><td><b>Ayuda</b></td><td>Esta documentación, el diagnóstico del sistema y el reporte de soporte.</td></tr>
</table>
<p class="muted">Las pestañas <b>Configuración VM</b>, <b>Snapshots</b> y <b>Consola Gráfica</b> se deshabilitan mientras no haya una VM seleccionada en la lista de la izquierda.</p>
""",
)

_register(
    "controles", "Panel izquierdo y controles de la VM",
    """
<p>El panel de la izquierda (<b>MÁQUINAS VIRTUALES</b>) contiene:</p>
<ul>
  <li><b>🔍 Buscar máquinas...</b> — filtra la lista por nombre.</li>
  <li><b>🔘 Vista</b> — alterna entre vista de lista y tarjetas (rejilla con iconos).</li>
  <li><b>Ordenar</b> — por nombre (A-Z) o por estado.</li>
  <li><b>Grupos</b> — muestra solo las VMs de un grupo concreto.</li>
  <li><b>➕ Nueva VM</b> — abre el asistente rápido para crear una máquina.</li>
  <li><b>📌</b> — pliega el panel; al acercar el cursor se despliega de nuevo.</li>
</ul>
<p>Botón derecho sobre una VM para abrir su menú contextual (<b>▶ Iniciar</b>, <b>🗑 Eliminar VM</b>).</p>
<h3>Controles de estado</h3>
<ul>
  <li><b>▶ Iniciar</b> — arranca la VM. Su menú añade <i>🖥️ Iniciar en pantalla completa</i> (en desarrollo).</li>
  <li><b>⏸ Pausar</b> — pausa la VM; el botón cambia a <i>▶ Reanudar</i> cuando está en pausa. Menú: <i>Pausar</i> / <i>Reanudar</i>.</li>
  <li><b>⏹ Apagar</b> — apagado ACPI. Menú: <i>Apagar (ACPI)</i>, <i>⏻ Forzar apagado</i>, <i>🔄 Reiniciar</i>, <i>⟲ Forzar reinicio</i>.</li>
</ul>
<p>Los botones se habilitan o deshabilitan según el estado de la VM seleccionada.</p>
<h3>Pantalla de bienvenida</h3>
<p>Si todavía no hay máquinas, el centro muestra el mensaje <i>"Bienvenido a Virtual.Machine"</i> con el botón <b>➕ Crear una VM nueva</b>.</p>
<h3>Panel derecho: Uso de recursos</h3>
<p>Muestra en vivo de la VM seleccionada: <b>Estado</b>, <b>Tiempo activo</b>, <b>Procesos</b>, <b>Dirección IP</b>, <b>Dirección MAC</b> y <b>Guest Agent</b>. También se pliega con 📌.</p>
""",
)

_register(
    "resumen", "Pestaña Resumen",
    """
<p>Vista general con dos tarjetas y una barra de acciones:</p>
<h3>Barra de acciones</h3>
<ul>
  <li><b>🧬 Clonar</b> — copia el directorio de la VM bajo otro nombre (la VM debe estar apagada).</li>
  <li><b>⇩ Importar</b> — admite <code>.ova</code>, <code>.ovf</code>, <code>.tar.gz</code>, <code>.nvm.tar.gz</code> y <code>.tar</code>.</li>
  <li><b>⇪ Exportar</b> — genera un OVA (compatible con VirtualBox/VMware) o un paquete NVM <code>.tar.gz</code>.</li>
  <li><b>🕘 Historial</b> — lista las versiones guardadas de la configuración y permite restaurar cualquiera (la restauración también se puede deshacer).</li>
  <li><b>💾 Plantilla</b> — guarda el hardware de la VM (CPU, RAM, firmware, red…) como plantilla reutilizable.</li>
  <li><b>📋 Desde plantilla</b> — crea una VM nueva a partir de una plantilla guardada, con disco propio.</li>
  <li><b>📝 Notas</b> — editor de notas libre asociado a la VM.</li>
  <li><b>🗑 Eliminar VM</b> — borra la configuración y los discos (pide confirmación).</li>
</ul>
<h3>Tarjeta de la VM</h3>
<p>Ficha de solo lectura: nombre, estado, plataforma, SO, firmware (UEFI/BIOS), chipset, CPU, RAM, gráficos, VRAM, disco, ISO montada, red, passthrough, carpetas compartidas, portapapeles y notas.</p>
<h3>Tarjeta del host</h3>
<p>Datos del anfitrión con botón <b>🔄</b> para actualizarlos: sistema operativo, entorno de escritorio, versión de Qt, kernel, plataforma gráfica, procesador, memoria RAM, GPU, número de serie, soporte KVM y versión de QEMU. La memoria se refresca automáticamente cada pocos segundos.</p>
""",
)

_register(
    "config_vm", "Pestaña Configuración VM",
    """
<p>Editor completo de la VM seleccionada. Arriba se configuran <b>Nombre</b>, <b>Plataforma</b>, <b>SO</b>, <b>Versión de SO</b> y <b>Perfil</b> (perfiles predefinidos que aplican RAM, núcleos, firmware, chipset, gráficos, Secure Boot y TPM de una vez). Pulsa <b>💾 Guardar configuración</b> para aplicar los cambios.</p>
<p>El menú lateral divide la configuración en nueve páginas:</p>
<table>
  <tr><th>Página</th><th>Contenido</th></tr>
  <tr><td><b>🖥️ Sistema</b></td><td>Firmware (BIOS/UEFI), chipset (i440FX/Q35) y seguridad (Secure Boot, TPM 2.0).</td></tr>
  <tr><td><b>⚙️ Procesador</b></td><td>Tipo de CPU, núcleos lógicos (2-32), topología manual (sockets/cores/threads), virtualización anidada y optimizaciones Hyper-V.</td></tr>
  <tr><td><b>🧠 Memoria</b></td><td>RAM (1-128 GB), hugepages, prealloc y bloqueo de memoria.</td></tr>
  <tr><td><b>🖼️ Pantalla</b></td><td>GPU (VirtIO, QXL, VGA, Headless…), GVT-g, memoria de video, protocolo y modo de consola.</td></tr>
  <tr><td><b>💾 Almacenamiento</b></td><td>Discos, CD/DVD y disquetes; formato (QCOW2, RAW, VDI, VMDK…), bus, orden de arranque arrastrable y compactación.</td></tr>
  <tr><td><b>🌐 Red</b></td><td>Adaptadores (VirtIO, E1000…), backend NAT/Bridge/TAP, MAC y reglas de redirigir puertos.</td></tr>
  <tr><td><b>🎛️ Dispositivos</b></td><td>Audio (Intel HDA, AC97…) y señalización (ratón/teclado USB, PS/2…).</td></tr>
  <tr><td><b>🔌 Passthrough</b></td><td>Dispositivos PCI (VFIO) y USB (usb-host) con detección automática.</td></tr>
  <tr><td><b>📂 Compartición</b></td><td>Carpetas compartidas, QEMU Guest Agent y portapapeles.</td></tr>
</table>
<h3>Detalles útiles</h3>
<ul>
  <li>El diálogo <b>CD/DVD</b> permite <i>Mantener vacío</i>, <i>Usar ISO existente</i> o <i>Descargar</i> la imagen (la descarga se ejecuta al guardar, con diálogo de progreso).</li>
  <li>Los diálogos de discos y medios incluyen un botón <b>📚 Biblioteca...</b> para elegir un archivo ya presente en la biblioteca.</li>
  <li>El texto de la página <b>Pantalla</b> recuerda los atajos del visor: <b>F11</b> pantalla completa, <b>Ctrl+Alt+F</b> salir, <b>Ctrl+Alt+G</b> liberar el teclado.</li>
  <li>Si eliges <b>SPICE</b>, la consola se fuerza a <i>Ventana externa</i>: SPICE no puede mostrarse embebido en la aplicación.</li>
  <li>Para el montaje automático de carpetas en el guest es necesario instalar <b>QEMU Guest Agent</b> dentro del sistema invitado.</li>
</ul>
""",
)

_register(
    "host", "Pestaña Configuración Host",
    """
<p>Ajustes globales del anfitrión, con un menú lateral:</p>
<table>
  <tr><th>Sección</th><th>Contenido</th></tr>
  <tr><td><b>🎨 Apariencia</b></td><td>Tema de la aplicación (Sistema, Claro, Oscuro) e idioma (Español, English, Português (BR), Deutsch, Français, Italiano). El cambio se aplica al instante a toda la interfaz, sin reiniciar.</td></tr>
  <tr><td><b>🔌 API REST</b></td><td>Servicio HTTP real enlazado a <code>127.0.0.1</code> (puerto <code>8730</code> por defecto). Muestra el token Bearer, permite arrancarlo y pararlo, y expone <code>/health</code>, <code>/vms</code> y <code>POST /vms/&lt;id&gt;/start|stop</code>. Consulta el tema <b>API REST local</b> para ver ejemplos.</td></tr>
  <tr><td><b>🍎 Soporte macOS</b></td><td>Versión instalada de OSX-KVM y botón <i>🔄 Actualizar OSX-KVM desde GitHub</i>.</td></tr>
  <tr><td><b>🛠️ Reparar OVMF</b></td><td>Copia el firmware UEFI con Secure Boot (<code>OVMF_CODE.secboot*.fd</code>) y sus VARS al directorio de datos, tanto en Linux como en Windows. Es lo que necesita Windows 11.</td></tr>
  <tr><td><b>🔌 USB (Windows)</b></td><td>Explica que <code>usb-host</code> necesita WinUSB o libusbK y ofrece un botón para abrir Zadig. En Linux las reglas udev se instalan con el reparador general.</td></tr>
  <tr><td><b>📁 Rutas de almacenamiento</b></td><td>Define las carpetas para las VMs (discos y configuraciones), las descargas de ISOs y la biblioteca central de medios. Requiere reiniciar la aplicación.</td></tr>
  <tr><td><b>Diagnóstico</b></td><td>Comprobaciones de Virtualización, Python, Consola, Compartición y Passthrough, con botones <i>🔄 Comprobar de nuevo</i> y <i>🛠️ Reparar lo que falte</i> (ejecuta el script de post-instalación con permisos de administrador).</td></tr>
</table>
<h3>Qué comprueba el diagnóstico</h3>
<ul>
  <li><b>QEMU y qemu-img</b>: el motor y la herramienta de discos (imprescindible para snapshots, ISOs y OVF).</li>
  <li><b>Firmware</b>: CODE y VARS de OVMF, con tamaño mínimo de 10 KB para los VARS; distingue Secure Boot.</li>
  <li><b>Aceleración</b>: KVM en Linux y WHPX real en Windows (se activa desde el postinstall; si no, avisa de TCG).</li>
  <li><b>IOMMU</b>: estado real del kernel (<code>intel_iommu</code>/<code>amd_iommu</code>), no solo la BIOS.</li>
  <li><b>TPM 2.0</b>: se pregunta a QEMU si ofrece el backend <code>emulator</code>, además de <code>swtpm</code> en Linux. Un "emulado" supuesto ya no se marca como OK.</li>
  <li><b>Fido</b>: versión v1.71 y marcador multiplataforma de la copia incluida, sin descargar nada de la red.</li>
  <li><b>Utilidades de apoyo</b>: <code>lsof</code>, <code>git</code>, <code>tar</code>, <code>xdg-open</code> y <code>notify-send</code>.</li>
  <li><b>Consola</b>: VNC embebido y visores externos; <b>Compartición</b>: Samba solo con <code>smbd</code> presente.</li>
</ul>
<h3>IOMMU en Linux</h3>
<p>Al reparar, la casilla <b>Habilitar IOMMU en el arranque (Linux)</b> añade <code>intel_iommu=on</code> o <code>amd_iommu=on</code> al gestor de arranque con <code>--enable-iommu</code>. Necesita VT-d/AMD-Vi en la BIOS y <b>reiniciar</b> para que el cambio surta efecto.</p>
<p class="muted">Si algo falta en tu equipo, empieza por este diagnóstico; desde Ayuda también puedes lanzar una comprobación rápida. Los avisos no bloquean la aplicación: indican funciones opcionales no disponibles.</p>
""",
)

_register(
    "api_rest", "API REST local",
    """
<p>La pestaña <b>Configuración Host → 🔌 API REST</b> arranca un servidor HTTP en <code>127.0.0.1</code> (nunca en todas las interfaces). No sustituye a la interfaz: permite listar y controlar VMs desde un script.</p>
<h3>Activación</h3>
<ol>
  <li>Abre <b>Configuración Host → API REST</b>.</li>
  <li>Revisa o cambia el puerto (por defecto <code>8730</code>; debe estar entre 1024 y 65535).</li>
  <li>Marca <b>Activar API REST local</b>. El campo <b>Token</b> muestra el valor que se generó una sola vez y se guarda en los ajustes.</li>
</ol>
<p>Todas las peticiones (salvo que se diga lo contrario) requieren la cabecera <code>Authorization: Bearer &lt;token&gt;</code>. El token se compara en tiempo constante y no se envía en la URL.</p>
<h3>Endpoints</h3>
<table>
  <tr><th>Método</th><th>Ruta</th><th>Respuesta</th></tr>
  <tr><td>GET</td><td><code>/health</code></td><td><code>{"ok": true, "service": "virtual-machine"}</code></td></tr>
  <tr><td>GET</td><td><code>/vms</code></td><td>Lista de VMs con su estado.</td></tr>
  <tr><td>GET</td><td><code>/vms/&lt;id&gt;</code></td><td>Una VM; 404 si no existe.</td></tr>
  <tr><td>POST</td><td><code>/vms/&lt;id&gt;/start</code></td><td>Arranca o reanuda la VM (202).</td></tr>
  <tr><td>POST</td><td><code>/vms/&lt;id&gt;/stop</code></td><td>Apaga la VM (202).</td></tr>
</table>
<h3>Ejemplo con curl</h3>
<p><code>curl -H "Authorization: Bearer TU_TOKEN" http://127.0.0.1:8730/vms</code></p>
<p class="muted">El servicio se detiene al desmarcar la casilla y no deja hilos ni puertos abiertos. Es local: no expongas el puerto a Internet ni compartas el token.</p>
""",
)

_register(
    "snapshots", "Pestaña Snapshots",
    """
<p>Los snapshots guardan el estado de la VM para volver a él después.</p>
<div class="muted">"Los snapshots en caliente guardan RAM y estado. Los snapshots en frío solo discos."</div>
<h3>Barra de acciones</h3>
<ul>
  <li><b>🔄 Actualizar</b> — refresca discos y snapshots.</li>
  <li><b>➕ Crear</b> — pide nombre (p. ej. <i>Antes de instalar drivers</i>) y descripción opcional.</li>
  <li><b>↩ Restaurar</b> — vuelve la VM al snapshot elegido (pide confirmación).</li>
  <li><b>🗑 Eliminar</b> — borra el snapshot seleccionado (pide confirmación).</li>
</ul>
<h3>Vistas</h3>
<ul>
  <li><b>📋 Lista</b> — tabla con ID, nombre, tamaño, fecha y reloj de la VM.</li>
  <li><b>🌳 Organigrama</b> — árbol de snapshots con zoom (<b>🔍− / 🔍+ / ⊞ Ajustar / 1:1</b>).</li>
</ul>
<h3>Otras secciones</h3>
<ul>
  <li><b>Tabla de discos</b> — dispositivo, formato, tamaño, espacio libre y modo de escritura.</li>
  <li><b>Previsualización</b> — miniatura de la VM y detalle del snapshot seleccionado.</li>
  <li><b>Snapshots y backups programados</b> — por VM se puede activar la programación, elegir frecuencia (diaria, semanal o mensual), cuántos conservar (1-50) y si se copia además el disco a la carpeta de backups. El programador se ejecuta automáticamente cada minuto; <b>💾 Backup ahora</b> fuerza uno.</li>
</ul>
<p class="muted">El backup de disco solo se copia con la VM apagada. Si está encendida se crea el snapshot, pero el disco no se copia: apágala y usa <b>💾 Backup ahora</b>. No elimines snapshots que aún necesites: liberan espacio pero no se pueden recuperar.</p>
""",
)

_register(
    "medios", "Pestaña Medios",
    """
<p>Biblioteca central de ISOs y discos de todas las VMs.</p>
<h3>Filtros y búsqueda</h3>
<ul>
  <li>Campo <b>Buscar</b> por nombre, distro o etiqueta.</li>
  <li>Filtro por <b>SO</b> (Todos, Linux, Windows, macOS, Android, Other) y por <b>Formato</b> (Todos, ISO, QCOW2, RAW, VDI, VMDK, IMG).</li>
</ul>
<h3>Acciones</h3>
<ul>
  <li><b>Añadir archivo(s)</b> — incorpora imágenes existentes a la biblioteca.</li>
  <li><b>➕ Crear disco</b> — QCOW2 (recomendado), RAW, VDI o VMDK, con tamaño y preasignación (expandible o fijo).</li>
  <li><b>Escanear carpeta</b> / <b>Escanear VMs</b> — detecta imágenes nuevas o discos ya usados por VMs.</li>
  <li><b>🔄 Refrescar</b> — sincroniza la biblioteca con el disco: elimina medios cuyo archivo ya no existe y añade los archivos nuevos de la carpeta de medios y de ISOs.</li>
</ul>
<h3>Tabla y operaciones por archivo</h3>
<p>Cada fila muestra nombre, tipo, SO, versión, arquitectura, tamaño real, tamaño de la VM, qué VM lo usa, estado (aparece en rojo como <i>huérfano</i> si el archivo ya no existe) y último uso. Con un elemento seleccionado puedes: <b>Modificar</b> (nombre, SO, versión, tamaño —solo se puede aumentar—, etiquetas y notas), <b>Compactar</b> (solo QCOW2), <b>Verificar</b>, <b>Calcular SHA256</b>, <b>Eliminar</b> y <b>Abrir carpeta</b>.</p>
""",
)

_register(
    "consolas", "Consolas: gráfica y de progreso",
    """
<h2>Consola Gráfica</h2>
<p>Muestra la pantalla de la VM mediante un visor VNC embebido:</p>
<ul>
  <li><b>⊞ Ajustar</b> — encuadra la imagen al tamaño del panel.</li>
  <li><b>🔍− / 🔍+ / 1:1</b> — zoom en pasos del 10 %, hasta el 400 %.</li>
  <li><b>⛶</b> — pantalla completa (F11 dentro del visor).</li>
</ul>
<p>La consola se conecta sola cuando la VM arranca y se desconecta al apagarla. Los modos de consola definidos en <b>Configuración VM → Pantalla</b> son:</p>
<ul>
  <li><b>Embebida en la app</b> — VNC dentro de esta pestaña.</li>
  <li><b>Ventana externa</b> — visor propio del sistema (<code>xtigervncviewer</code> o <code>remote-viewer</code>).</li>
  <li><b>Híbrida</b> — VNC embebida + SPICE en ventana externa.</li>
  <li><b>Pantalla completa</b> — VNC embebida que entra en pantalla completa al arrancar.</li>
</ul>
<p>Si cierras por error la ventana externa de SPICE/VNC, usa el botón <b>🖥</b> del panel de máquinas, el menú contextual de la VM o <b>F7</b> para volver a abrirla. La VM sigue encendida: no hay que reiniciarla.</p>
<h3>Atajos del visor</h3>
<ul>
  <li><b>F11</b> — alterna pantalla completa.</li>
  <li><b>Ctrl+Alt+F</b> — sale de pantalla completa.</li>
  <li><b>Ctrl+Alt+G</b> — libera el teclado del sistema invitado.</li>
</ul>
<h2>Consola de Progreso</h2>
<p>Registro en vivo de la aplicación:</p>
<ul>
  <li><b>Nivel</b> — Todo, Avisos+ o solo Errores.</li>
  <li><b>🔍 Filtrar</b> — busca texto libre en el registro.</li>
  <li><b>Auto-scroll</b> — sigue la última línea automáticamente.</li>
  <li><b>Limpiar consola</b> / <b>💾 Exportar log</b> — borra o guarda el registro en un archivo .txt.</li>
</ul>
<p class="muted">Si algo falla al iniciar una VM, revisa primero esta pestaña: ahí aparece la salida de QEMU.</p>
""",
)

_register(
    "productividad", "Atajos, plantillas e historial",
    """
<h2>Paleta de comandos y atajos</h2>
<ul>
  <li><b>Ctrl+K</b> — abre la paleta de comandos: escribe parte del nombre de una acción y pulsa Enter para ejecutarla.</li>
  <li><b>Ctrl+Shift+K</b> — abre el diálogo <b>Atajos de teclado</b>, donde se puede cambiar cualquier combinación y restaurar los valores originales.</li>
  <li>El menú <b>&Herramientas</b> contiene todas estas acciones. Los atajos se guardan en <code>QSettings</code> (<code>shortcuts/&lt;comando&gt;</code>) y sobreviven al reinicio.</li>
</ul>
<p>Atajos iniciales: <b>Ctrl+N</b> nueva VM, <b>F5</b> encender, <b>F6</b> apagar, <b>Ctrl+H</b> historial, <b>Ctrl+T</b> nueva desde plantilla, <b>Ctrl+Shift+T</b> guardar plantilla, <b>Ctrl+M</b> pestaña Medios y <b>Ctrl+Shift+S</b> pestaña Snapshots.</p>
<h2>Plantillas frente a perfiles y clonación</h2>
<ul>
  <li><b>Perfiles</b> (Ligera, Hogar, Desarrollo, Juegos) son ajustes fijos de la aplicación.</li>
  <li><b>💾 Plantilla</b> guarda <i>tu</i> configuración de hardware de una VM concreta; no incluye nombre, disco ni datos del invitado.</li>
  <li><b>📋 Desde plantilla</b> aplica esa configuración a una VM nueva con un disco recién creado. No sustituye a <b>🧬 Clonar</b>, que copia también el disco y el contenido.</li>
</ul>
<h2>Historial de configuración</h2>
<p>Cada cambio de nombre, CPU, RAM, firmware, red… crea una versión (se conservan las 30 últimas). Los cambios de estado, socket QMP o puerto VNC no generan ruido en el historial. <b>🕘 Historial</b> muestra fecha y motivo de cada versión y permite restaurarla; antes de restaurar se guarda la configuración actual, así que la operación siempre se puede deshacer.</p>
""",
)

_register(
    "requisitos", "Requisitos del sistema",
    """
<p>La aplicación funciona en <b>Linux</b> y en <b>Windows 10/11 de 64 bits</b>. La aceleración por hardware cambia según el sistema:</p>
<table>
  <tr><th>Componente</th><th>Linux</th><th>Windows</th><th>Uso</th></tr>
  <tr><td>Aceleración</td><td>KVM (<code>/dev/kvm</code>)</td><td>WHPX (Plataforma de hipervisor de Windows)</td><td>Obligatoria para ir rápido; sin ella se usa TCG (2–5 % de velocidad).</td></tr>
  <tr><td><code>qemu-system-x86_64</code></td><td>Obligatorio</td><td>Obligatorio (lo instala el postinstall)</td><td>Motor de la VM.</td></tr>
  <tr><td><code>qemu-img</code></td><td>Obligatorio</td><td>Obligatorio (junto al ejecutable)</td><td>Snapshots, conversión de discos, ISOs y OVF.</td></tr>
  <tr><td>Firmware OVMF/UEFI</td><td>Paquetes del sistema</td><td>Lo copia el reparador</td><td>Arranque UEFI y Secure Boot (Windows 11).</td></tr>
  <tr><td>TPM 2.0 (requisito de Windows 11)</td><td><code>swtpm</code> + backend <code>emulator</code></td><td>Backend <code>emulator</code> de QEMU</td><td>Se verifica preguntando al QEMU instalado.</td></tr>
  <tr><td>Visor VNC/SPICE</td><td><code>xtigervncviewer</code> / <code>remote-viewer</code></td><td><code>remote-viewer.exe</code></td><td>Consola externa; la VNC embebida no necesita visor.</td></tr>
  <tr><td>Compartición</td><td><code>virtiofsd</code> o Samba con <code>smbd</code></td><td>Samba con <code>smbd</code></td><td>Carpetas compartidas con el invitado.</td></tr>
  <tr><td>Utilidades de apoyo</td><td><code>lsof</code>, <code>git</code>, <code>tar</code>, <code>xdg-utils</code>, <code>libnotify</code></td><td>Incluidas en el sistema</td><td>Detección de puertos, import/export y notificaciones.</td></tr>
  <tr><td>USB passthrough</td><td>Reglas udev (reparador)</td><td>WinUSB/libusbK con Zadig</td><td>Dispositivos <code>usb-host</code>.</td></tr>
  <tr><td>Fido v1.71</td><td colspan="2">Copia incluida y parcheada en la aplicación</td><td>Resolución de URLs de ISOs de Windows; no se descarga.</td></tr>
</table>
<p class="muted">El instalador de Windows es autocontenido: no necesita Python ni Git para ejecutarse. La pestaña <b>Ayuda → Diagnóstico del sistema</b> comprueba todo esto en tu equipo y señala lo que falta.</p>
""",
)

_register(
    "faq", "Problemas frecuentes",
    """
<h2>La VM no arranca</h2>
<ul>
  <li>En Linux comprueba <b>KVM</b>: <code>ls -l /dev/kvm</code> debe existir y ser accesible para tu usuario (grupo <code>kvm</code>).</li>
  <li>En Windows abre <b>Configuración Host → Diagnóstico</b>: si WHPX figures como aviso, ejecuta <b>Reparar lo que falte</b> y reinicia. Mientras tanto la app usa TCG y la pantalla puede tardar bastante en aparecer.</li>
  <li>Revisa la pestaña <b>Consola de Progreso</b>: ahí aparece el error exacto que devuelve QEMU.</li>
  <li>Confirma que la configuración se guardó con <b>💾 Guardar configuración</b>.</li>
</ul>
<h2>Windows 11 exige TPM y Secure Boot</h2>
<p>En <b>Configuración VM → Sistema</b> selecciona firmware <b>UEFI (OVMF)</b> y activa <b>Secure Boot</b> y <b>TPM 2.0</b>. En Linux hace falta <code>swtpm</code>; en Windows QEMU usa su backend <code>emulator</code>. El diagnóstico pregunta al QEMU instalado si ofrece ese backend y solo lo marca como OK cuando responde. Si el VARS de Secure Boot falta, usa <b>Configuración Host → Reparar OVMF</b>.</p>
<h2>No veo la pantalla de la VM</h2>
<ul>
  <li>La VM debe estar <b>encendida</b>; si no, la consola muestra "Esperando que la VM se encienda...".</li>
  <li>Verifica el <b>protocolo</b> y el <b>modo de consola</b> en <b>Configuración VM → Pantalla</b>.</li>
  <li>Si el modo es externo, la imagen aparece en una ventana aparte del sistema.</li>
</ul>
<h2>Quiero la resolución de mi monitor dentro de la VM</h2>
<p>En <b>Configuración VM → Pantalla</b> hay un campo <b>Resolución inicial</b> con las resoluciones reales de tus monitores. Se pasa a QEMU como <code>xres/yres</code> de la GPU virtual. Si además quieres que el guest siga el tamaño de la ventana, elige <b>Red Hat QXL 2D</b>, pon la VRAM en 128/256 MB, usa SPICE externa e instala <code>spice-vdagent</code> dentro del invitado.</p>
<h2>Varias pantallas virtuales</h2>
<p>En <b>Configuración VM → Pantalla</b> puedes elegir entre <b>1 y 4 monitores virtuales</b>. QEMU expone cada monitor como una salida independiente (<code>max_outputs</code>) y abre un servidor VNC/SPICE por cabeza.</p>
<ul>
  <li>Con <b>VNC embebido</b>, aparecen los botones <b>◀ Monitor / Monitor ▶</b> en la barra de la consola para cambiar de pantalla sin reconectar a mano.</li>
  <li>Con <b>VNC en ventana externa</b>, se abre una ventana de <code>remote-viewer</code> por monitor, cada una con su título.</li>
  <li>Con <b>SPICE externa</b>, se abre una ventana de <code>remote-viewer</code> por monitor, cada una con su título. Con varios monitores se desactiva el ratón de agente (<code>agent-mouse=off</code>) y los tablets se convierten en <b>USB Mouse</b>, porque SPICE envía movimientos relativos y un tablet solo entiende coordenadas absolutas.</li>
  <li>Dentro del invitado debes activar los monitores extra en su configurador de pantalla (o <code>xrandr</code>/<code>display</code> en Linux) y aumentar la VRAM si vas a usar resoluciones altas.</li>
</ul>
<h2>La descarga de ISO falla</h2>
<p>Microsoft bloquea la descarga automática de Windows: avisa la aplicación y hay que descargar la ISO manualmente desde su web. Para el resto de sistemas, si la descarga se interrumpe, vuelve a iniciar la VM: se reintentará.</p>
<h2>Una VM queda en estado raro ("Apagando..." eterno)</h2>
<p>La aplicación detecta estados huérfanos (sin proceso real) y los corrige sola. Si persiste, usa <b>⏻ Forzar apagado</b> en el menú de <b>⏹ Apagar</b>.</p>
<h2>No hay sonido</h2>
<p>Elige un dispositivo de audio en <b>Configuración VM → Dispositivos</b> (Intel HDA es el recomendado) y comprueba que el host tenga PulseAudio o PipeWire (<code>pactl</code>).</p>
<h2>Los USB no aparecen en la VM</h2>
<p>En Linux instala las reglas udev (botón <b>🛠️ Reparar lo que falte</b> en <b>Configuración Host</b>) y vuelve a enchufar el dispositivo. En Windows abre <b>Configuración Host → 🔌 USB (Windows)</b> y pulsa <b>Abrir Zadig</b> para instalar <code>WinUSB</code> o <code>libusbK</code> al dispositivo elegido; además necesitas un puntero USB en <b>Configuración VM → Dispositivos</b> para crear el bus XHCI. Luego usa <b>🔌 Conectar Hardware (Hotplug) → Dispositivos USB</b>. En ambos casos el passthrough usa <code>usb-host</code>.</p>
<h2>Las carpetas compartidas no se montan</h2>
<p>Instala <b>QEMU Guest Agent</b> dentro del sistema invitado y activa el canal en <b>Configuración VM → Compartición → Guest Tools</b>.</p>
<h2>WHPX no se activa en Windows</h2>
<p>El postinstall consulta <code>Get-WindowsOptionalFeature -FeatureName HypervisorPlatform</code> y, si está desactivada, ejecuta <code>Enable-WindowsOptionalFeature ... -NoRestart</code>. Si no tiene permisos, avisa y sigue (la app funciona con TCG). Para activarlo a mano: *Activar o desactivar características de Windows* → <b>Plataforma de hipervisor de Windows</b> y reiniciar. WHPX no convive bien con VirtualBox, VMware ni HAXM activos.</p>
<h2>El firewall bloquea la consola</h2>
<p>Las consolas VNC/SPICE escuchan solo en <code>127.0.0.1</code>. El postinstall elimina las reglas antiguas que abrían <code>5900-6000</code> y <code>5930-6000</code> a todos los perfiles y crea una regla por ejecutable: <b>VM-Manager QEMU local</b>, perfil <i>Privado</i> y solo subred local. Si usas una red pública, elige el perfil <i>Privado</i> en Windows o desactiva temporalmente la regla. El desinstalador retira esta regla.</p>
<h2>La API REST no responde</h2>
<p>Comprueba que la casilla <b>Activar API REST local</b> esté marcada y que el mensaje bajo el token diga <i>API activa</i>. Usa siempre <code>Authorization: Bearer &lt;token&gt;</code>; sin esa cabecera la respuesta es <code>401</code>. El puerto debe estar libre y entre 1024 y 65535. El servicio solo escucha en <code>127.0.0.1</code>: intentar acceder desde otro equipo no funcionará.</p>
<h2>Fido no encuentra la ISO de Windows</h2>
<p>El diagnóstico verifica que la copia incluida sea <b>v1.71</b> y conserve el marcador <code># --- patched-for-linux ---</code>. No se descarga nada durante la comprobación. Si el estado es aviso, reinstala la aplicación para recuperar la copia canónica; en Windows se ejecuta tal cual y en Linux se parchea en un archivo temporal, nunca sobre la copia original.</p>
<h2>Algo más falla</h2>
<p>Ejecuta <b>🩺 Ejecutar diagnóstico</b> (parte superior de esta pestaña), corrige lo marcado en rojo y, si el problema continúa, usa <b>📋 Copiar información de soporte</b> para enviar el reporte completo (incluye versión, rutas, número de VMs y el estado de todos los componentes).</p>
""",
)

_register(
    "rutas", "Archivos y rutas de datos",
    """
<p>Por defecto, los datos se guardan en tu directorio de usuario:</p>
<table>
  <tr><th>Contenido</th><th>Linux</th><th>Windows</th></tr>
  <tr><td>Datos generales</td><td><code>~/.local/share/virtual-machine</code></td><td><code>%LOCALAPPDATA%\\VirtualMachine</code></td></tr>
  <tr><td>Máquinas virtuales</td><td><code>.../vms</code></td><td><code>...\\vms</code></td></tr>
  <tr><td>ISOs e imágenes</td><td><code>.../isos</code></td><td><code>...\\isos</code></td></tr>
  <tr><td>Biblioteca de medios</td><td><code>.../MediaLibrary</code></td><td><code>...\\MediaLibrary</code></td></tr>
  <tr><td>Historial de PATH (postinstall)</td><td>—</td><td><code>postinstall-paths.txt</code> en la carpeta de datos</td></tr>
  <tr><td>Ajustes de la aplicación</td><td colspan="2"><code>QSettings</code>, organización <code>VirtualMachine</code> (registro en Windows, archivo en Linux)</td></tr>
</table>
<p>Las rutas se pueden cambiar en <b>Configuración Host → 📁 Rutas de almacenamiento</b>; los valores quedan guardados y se reutilizan en el arranque. Las claves son <code>paths/base_dir</code>, <code>paths/vms_dir</code>, <code>paths/isos_dir</code>, <code>paths/media_dir</code> y <code>paths/qemu_dir</code>. La API REST guarda <code>api/port</code> y <code>api/token</code>.</p>
<p class="muted">Para respaldar tu trabajo, copia la carpeta de datos completa. Las VMs detenidas se pueden exportar desde el menú contextual de la lista. El desinstalador de Windows conserva estos datos: solo retira el PATH y las reglas de firewall que añadió el postinstall.</p>
""",
)

_register(
    "acerca", "Acerca de",
    f"""
<p><b>{APP_NAME}</b> — Administrador de máquinas virtuales QEMU con aceleración por hardware.</p>
<table>
  <tr><th>Campo</th><th>Valor</th></tr>
  <tr><td>Versión</td><td>{APP_VERSION}</td></tr>
  <tr><td>Plataforma</td><td>{platform.platform()}</td></tr>
  <tr><td>Python</td><td>{platform.python_version()}</td></tr>
  <tr><td>Motor de virtualización</td><td>QEMU con KVM (Linux) o WHPX (Windows); TCG como respaldo</td></tr>
</table>
<p>La aplicación está construida con <b>PyQt6</b> y una arquitectura de plugins: cada pestaña es un módulo independiente cargado desde la carpeta <code>plugins/</code>.</p>
<p class="muted">Usa <b>Copiar información de soporte</b> (parte superior) para generar un reporte que puedas pegar al solicitar ayuda.</p>
""",
)


# ======================================================================
# DIAGNÓSTICO (contenido dinámico)
# ======================================================================
def _diag_page(checks) -> str:
    rows = []
    labels = {"ok": ("✔ OK", "ok"), "warn": ("⚠ Aviso", "warn"), "err": ("✘ Error", "err")}
    last_cat = None
    for c in checks:
        cat = c.get("cat", "")
        cat_cell = f"<td><b>{html.escape(cat)}</b></td>" if cat != last_cat else "<td></td>"
        last_cat = cat
        text, cls = labels.get(c.get("st", "warn"), ("?", "warn"))
        rows.append(
            f"<tr>{cat_cell}<td>{html.escape(c.get('name', ''))}</td>"
            f"<td class=\"{cls}\">{text}</td><td>{html.escape(str(c.get('desc', '')))}</td></tr>"
        )
    body = (
        "<p>Comprobación de los componentes necesarios para el funcionamiento "
        "de las máquinas virtuales en este equipo.</p>"
        "<table><tr><th>Categoría</th><th>Componente</th><th>Estado</th><th>Detalle</th></tr>"
        + "".join(rows)
        + "</table>"
        "<p class=\"muted\">Los avisos no impiden el uso de la aplicación; solo indican "
        "funciones opcionales que no están disponibles.</p>"
    )
    return _page("Diagnóstico del sistema", body)


# ======================================================================
# INFORMACIÓN DE SOPORTE
# ======================================================================
def _support_report(app) -> str:
    from services.host_diagnostics import HostDiagnostics

    lines = [
        f"{APP_NAME} {APP_VERSION} — {tr('reporte de soporte')}",
        f"{tr('Plataforma:')} {platform.platform()}",
        f"Python: {platform.python_version()} ({sys.executable})",
        f"{tr('Datos:')} {getattr(app, 'data_dir', 'n/d')}",
        f"VMs: {len(app.get_vms())}",
        tr("Componentes:"),
    ]
    try:
        for c in HostDiagnostics().run_all():
            mark = {"ok": "OK", "warn": "AVISO", "err": "ERROR"}.get(c.get("st"), "?")
            lines.append(f"  [{mark}] {c.get('cat')}/{c.get('name')}: {c.get('desc')}")
    except Exception as e:
        lines.append(f"  ({tr('diagnóstico no disponible:')} {e})")
    return "\n".join(lines)


# ======================================================================
# PLUGIN
# ======================================================================
class Plugin(PluginBase):
    name = "Help"
    version = "1.0.0"
    description = "Pestaña de ayuda del sistema"

    def get_tabs(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- Cabecera ---
        header = QHBoxLayout()
        titles = QVBoxLayout()
        lbl_title = QLabel(tr("<h2>{} — Ayuda</h2>").format(APP_NAME))
        lbl_title.setTextFormat(Qt.TextFormat.RichText)
        titles.addWidget(lbl_title)
        titles.addWidget(QLabel(f"<span class='muted'>Versión {APP_VERSION} · documentación del sistema</span>"))
        header.addLayout(titles)
        header.addStretch()

        btn_diag = QPushButton("🩺 Ejecutar diagnóstico")
        btn_diag.setToolTip("Comprobar los componentes del sistema necesarios para las VMs")
        btn_diag.clicked.connect(self._run_diagnostics)
        header.addWidget(btn_diag)

        btn_copy = QPushButton("📋 Copiar información de soporte")
        btn_copy.setToolTip("Generar un reporte con versión, rutas y estado de los componentes")
        btn_copy.clicked.connect(self._copy_support)
        header.addWidget(btn_copy)

        layout.addLayout(header)

        # --- Cuerpo: índice + contenido ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.input_filter = QLineEdit()
        self.input_filter.setPlaceholderText("🔍 Buscar en la ayuda...")
        self.input_filter.setToolTip("Filtrar los temas de ayuda por título o contenido")
        self.input_filter.textChanged.connect(self._filter_topics)
        left_layout.addWidget(self.input_filter)

        self.list_topics = QListWidget()
        self.list_topics.setFixedWidth(230)
        self.list_topics.currentItemChanged.connect(self._on_topic_changed)
        left_layout.addWidget(self.list_topics)

        self.lbl_status = QLabel(" ")
        self.lbl_status.setWordWrap(True)
        left_layout.addWidget(self.lbl_status)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)

        splitter.addWidget(left)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        # --- Poblar índice ---
        self._plain = {}
        self._originals = {}
        for key, title, content in TOPICS:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, key)
            font = item.font()
            font.setPointSize(font.pointSize() + 1)
            item.setFont(font)
            self.list_topics.addItem(item)
            self._plain[key] = _strip_html(content)
            self._originals[key] = content

        # El diagnóstico se genera bajo demanda
        self._diag_content = None

        if self.list_topics.count():
            self.list_topics.setCurrentRow(0)

        return [("Ayuda", widget)]

    # ------------------------------------------------------------------
    def _set_html(self, contenido):
        """Guarda el HTML original y muestra su versión traducida."""
        self.browser._nvm_i18n_html = contenido
        self.browser.setHtml(translate_html(contenido))

    def _on_topic_changed(self, current, _previous=None):
        if current is None:
            return
        key = current.data(Qt.ItemDataRole.UserRole)
        if key == "diagnostico" and self._diag_content is None:
            self._set_html(_page("Diagnóstico del sistema",
                                 "<p>Pulsa <b>🩺 Ejecutar diagnóstico</b> para comprobar los componentes del sistema.</p>"))
            return
        if key == "diagnostico":
            self._set_html(self._diag_content)
            return
        for k, _t, content in TOPICS:
            if k == key:
                self._set_html(content)
                return

    def _filter_topics(self, text: str):
        needle = text.strip().lower()
        first_visible = None
        current_hidden = False
        for i in range(self.list_topics.count()):
            item = self.list_topics.item(i)
            key = item.data(Qt.ItemDataRole.UserRole)
            title = item.text().lower()
            original = self._originals.get(key, self._diag_content or "")
            traducido = _strip_html(translate_html(original))
            match = ((not needle) or needle in title or needle in self._plain.get(key, "")
                     or needle in traducido)
            item.setHidden(not match)
            if match and first_visible is None:
                first_visible = item
            if item is self.list_topics.currentItem() and not match:
                current_hidden = True
        if current_hidden and first_visible is not None:
            self.list_topics.setCurrentItem(first_visible)

    def _run_diagnostics(self):
        try:
            from services.host_diagnostics import HostDiagnostics
            checks = HostDiagnostics().run_all()
        except Exception as e:
            log.exception("Diagnóstico fallido")
            checks = [{"cat": "Sistema", "name": "Diagnóstico", "st": "err", "desc": str(e)}]

        self._diag_content = _diag_page(checks)
        item = self._ensure_diag_topic()
        if item is not None:
            self.list_topics.setCurrentItem(item)
        self._set_html(self._diag_content)
        errors = sum(1 for c in checks if c.get("st") == "err")
        warns = sum(1 for c in checks if c.get("st") == "warn")
        self.lbl_status.setText(
            f"{tr('Diagnóstico:')} {len(checks)} {tr('comprobaciones')} · "
            f"{errors} {tr('error(es)')}, {warns} {tr('aviso(s)')}")

    def _ensure_diag_topic(self):
        for i in range(self.list_topics.count()):
            if self.list_topics.item(i).data(Qt.ItemDataRole.UserRole) == "diagnostico":
                return self.list_topics.item(i)
        item = QListWidgetItem("🩺 Diagnóstico del sistema")
        item.setData(Qt.ItemDataRole.UserRole, "diagnostico")
        self.list_topics.addItem(item)
        self._plain["diagnostico"] = "diagnostico del sistema componentes qemu kvm ovmf swtpm"
        return item

    def _copy_support(self):
        report = _support_report(self.app)
        try:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(report)
            self.lbl_status.setText(tr("📋 Información copiada al portapapeles"))
        except Exception as e:
            self.lbl_status.setText(f"{tr('No se pudo copiar:')} {e}")


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return " ".join(html.unescape(text).split()).lower()
