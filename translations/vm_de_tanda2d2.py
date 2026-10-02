# -*- coding: utf-8 -*-
"""Traducciones al aleman - Tanda 2d-2: Pantalla + Consola remota + graficos.

Cubre: seccion Pantalla (graficos/GPU, VRAM, VNC embebido, consola
remota), bloque grande de console_backend.py (pros/contras de VNC/
SPICE/Hibrida, avisos de sesion X11/Wayland, deps spice-gtk),
console_ui_mixin.py (hints y errores de visor externo) y labels
dinamicos de graficos (_refresh_auto_graphics_label,
update_graphics_options, avisos Android-UEFI, VGA OSX-KVM).

Se fusiona con las tandas anteriores.
"""

TRANSLATIONS = {

    # ================================================================
    # Pantalla
    # ================================================================
    "Pantalla": "Anzeige",
    "Controlador gráfico virtual y memoria de video.":
        "Virtueller Grafikcontroller und Videospeicher.",
    "<b>Gráficos / GPU</b>": "<b>Grafik / GPU</b>",
    "VirtIO-GPU 2D (compatible • snap. discos ✓ • snap. completo ✗)":
        "VirtIO-GPU 2D (kompatibel • Disk-Snap. ✓ • Voll-Snap. ✗)",
    "VirtIO-GPU + VirGL 3D (OpenGL • snapshots ✗)":
        "VirtIO-GPU + VirGL 3D (OpenGL • Snapshots ✗)",
    "VirtIO-GPU + Venus/Vulkan 3D (experimental • snapshots ✗)":
        "VirtIO-GPU + Venus/Vulkan 3D (experimentell • Snapshots ✗)",
    "Red Hat QXL 2D (3D ✗ • snap. completo ✓ • macOS ⚠)":
        "Red Hat QXL 2D (3D ✗ • Voll-Snap. ✓ • macOS ⚠)",
    "VMware SVGA II (3D acelerado ✗ • snap. completo ✓ • macOS ⚠)":
        "VMware SVGA II (beschleunigtes 3D ✗ • Voll-Snap. ✓ • macOS ⚠)",
    "Sin video / Headless": "Kein Video / Headless",
    "Automático detecta las capacidades del host y usa aceleración 3D cuando es segura; si no, vuelve a VirtIO-GPU 2D.\n\n"
    "Snapshots:\n"
    "  • VirtIO-GPU 2D → solo snap. de discos.\n"
    "  • QXL y VMware SVGA → snap. completo (RAM + dispositivos).\n"
    "  • VirGL / Venus → no soportan ningún tipo de snapshot.":
        "Automatisch erkennt die Host-Fähigkeiten und nutzt 3D-Beschleunigung, wenn sie sicher ist; andernfalls wird auf VirtIO-GPU 2D zurückgegriffen.\n\n"
        "Snapshots:\n"
        "  • VirtIO-GPU 2D → nur Disk-Snapshots.\n"
        "  • QXL und VMware SVGA → Voll-Snapshot (RAM + Geräte).\n"
        "  • VirGL / Venus → unterstützen keinerlei Snapshots.",
    "<b>Memoria de video (VRAM)</b>": "<b>Videospeicher (VRAM)</b>",
    "Host GPU: detectando…": "Host-GPU: wird erkannt…",
    "🖼 Mostrar la VM dentro de la app (consola VNC embebida)":
        "🖼 Die VM in der Anwendung anzeigen (eingebettete VNC-Konsole)",
    "🖼️ Mostrar la VM dentro de la app (consola VNC embebida)":
        "🖼️ Die VM in der Anwendung anzeigen (eingebettete VNC-Konsole)",
    "Cuando está activo, la VM se muestra dentro de la app.\n"
    "Fuerza gráficos sin aceleración OpenGL (VNC no soporta GL).\n"
    "Si lo desactivas, la VM se abre en una ventana externa y puedes\n"
    "elegir modos con aceleración 3D (VirGL, Venus).":
        "Wenn aktiv, wird die VM in der Anwendung angezeigt.\n"
        "Erzwingt Grafik ohne OpenGL-Beschleunigung (VNC unterstützt kein GL).\n"
        "Bei Deaktivierung öffnet sich die VM in einem externen Fenster und du kannst\n"
        "Modi mit 3D-Beschleunigung wählen (VirGL, Venus).",
    "Consola remota": "Remote-Konsole",
    "VNC (compatible con cualquier gráfico)": "VNC (mit jeder Grafik kompatibel)",
    "SPICE (mejor rendimiento en local)": "SPICE (bessere Leistung lokal)",
    "VNC: cliente ligero, funciona con cualquier dispositivo de video.\n"
    "SPICE: mejor rendimiento en local, requiere un visor spice-gtk.\n"
    "Con cualquiera de los dos, QEMU no abre ventana local: solo el socket.":
        "VNC: schlanker Client, funktioniert mit jedem Videogerät.\n"
        "SPICE: bessere Leistung lokal, erfordert einen spice-gtk-Viewer.\n"
        "Bei beiden öffnet QEMU kein lokales Fenster: nur den Socket.",
    "Protocolo:": "Protokoll:",
    "Embebida en la app": "In der Anwendung eingebettet",
    "Ventana externa (visor del sistema)": "Externes Fenster (System-Viewer)",
    "Ventana nativa de QEMU": "QEMU-natives Fenster",
    "Híbrida (VNC embebido + SPICE externo)": "Hybrid (eingebettetes VNC + externes SPICE)",
    "Embebida: la pantalla vive dentro de esta app (pestaña Consola Gráfica).\n"
    "Ventana externa: se lanza el visor del sistema (vncviewer / spicy).\n"
    "Nativa QEMU: QEMU abre su propia ventana (comportamiento clásico).":
        "Eingebettet: der Bildschirm lebt in dieser Anwendung (Reiter Grafische Konsole).\n"
        "Externes Fenster: startet den System-Viewer (vncviewer / spicy).\n"
        "QEMU-nativ: QEMU öffnet ein eigenes Fenster (klassisches Verhalten).",
    "Modo:": "Modus:",
    "Log VNC detallado (DEBUG)": "Ausführliches VNC-Log (DEBUG)",
    "Activa el nivel DEBUG del cliente VNC embebido.\n\n"
    "Por defecto INFO: el widget VNC no llena launch.log con\n"
    "una línea por cada frame. Actívalo solo para diagnosticar\n"
    "problemas concretos del cliente VNC; escribe miles de\n"
    "líneas por segundo y puede afectar al rendimiento.":
        "Aktiviert die DEBUG-Stufe des eingebetteten VNC-Clients.\n\n"
        "Standardmäßig INFO: Das VNC-Widget füllt launch.log nicht mit\n"
        "einer Zeile pro Frame. Nur zur Diagnose konkreter Probleme\n"
        "des VNC-Clients aktivieren; schreibt Tausende Zeilen pro\n"
        "Sekunde und kann die Leistung beeinträchtigen.",

    # ================================================================
    # Tanda 2d-2b: console_backend.py + console_ui_mixin.py
    # ================================================================
    "QEMU abre su propia ventana (GTK/SDL). No hace falta visor externo ni cliente; a cambio, la VM no aparece dentro de la app.":
        "QEMU öffnet ein eigenes Fenster (GTK/SDL). Kein externer Viewer oder Client erforderlich; dafür erscheint die VM nicht in der Anwendung.",
    "Híbrida: VNC se muestra dentro de la app (funciona en Wayland y X11) y SPICE se abre en una ventana externa con spicy o remote-viewer. Lo mejor de ambos: embebido para tenerlo a mano, SPICE para rendimiento y clipboard avanzado.":
        "Hybrid: VNC wird in der Anwendung angezeigt (funktioniert unter Wayland und X11), SPICE öffnet sich in einem externen Fenster mit spicy oder remote-viewer. Das Beste aus beiden: eingebettet für den schnellen Zugriff, SPICE für Leistung und erweiterte Zwischenablage.",
    "VNC embebido en la app. Sin dependencias adicionales.":
        "VNC in der Anwendung eingebettet. Keine zusätzlichen Abhängigkeiten.",
    "VNC en ventana externa. Necesitas vncviewer (tigervnc), gvncviewer o remmina instalado.":
        "VNC in externem Fenster. vncviewer (tigervnc), gvncviewer oder remmina muss installiert sein.",
    "SPICE embebido en la app (Gtk.SpiceDisplay vía XEmbed). Requiere sesión X11; en Wayland cae a visor externo.":
        "SPICE in der Anwendung eingebettet (Gtk.SpiceDisplay über XEmbed). Erfordert X11-Sitzung; unter Wayland wird auf externen Viewer zurückgegriffen.",
    "SPICE embebido solicitado, pero spice-gtk no tiene binding Python. Se usará visor externo como respaldo. Instala python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) o python-gobject + spice-gtk (Arch).":
        "Eingebettetes SPICE angefordert, aber spice-gtk hat kein Python-Binding. Als Ausweichlösung wird ein externer Viewer verwendet. Installiere python3-gi + gir1.2-spiceclientgtk-3.0 (Debian/Ubuntu) oder python-gobject + spice-gtk (Arch).",
    "SPICE en ventana externa. Necesitas spicy (spice-gtk) o remote-viewer (virt-viewer).":
        "SPICE in externem Fenster. spicy (spice-gtk) oder remote-viewer (virt-viewer) muss installiert sein.",
    "<b>Sesión actual: X11.</b> Tanto VNC como SPICE se pueden embeber dentro de la app.":
        "<b>Aktuelle Sitzung: X11.</b> Sowohl VNC als auch SPICE können in die Anwendung eingebettet werden.",
    "<b>Sesión actual: Wayland.</b> Solo VNC se puede embeber dentro de la app. SPICE embebido requeriría X11 (XEmbed no existe en Wayland); si eliges SPICE con modo embebido, caerá automáticamente a visor externo.":
        "<b>Aktuelle Sitzung: Wayland.</b> Nur VNC kann in die Anwendung eingebettet werden. Eingebettetes SPICE würde X11 erfordern (XEmbed existiert unter Wayland nicht); wenn du SPICE mit eingebettetem Modus wählst, wird automatisch auf externen Viewer zurückgegriffen.",
    "<b>spice-gtk con binding Python: sí.</b> El embed de SPICE funcionará cuando estés en X11.":
        "<b>spice-gtk mit Python-Binding: ja.</b> Das SPICE-Embedding funktioniert, wenn du dich unter X11 befindest.",
    "<b>spice-gtk con binding Python: no.</b> Aunque estés en X11, SPICE no podrá incrustarse; siempre caerá a visor externo. Instálalo con:<br>&nbsp;&nbsp;<code>Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0</code><br>&nbsp;&nbsp;<code>Arch: python-gobject spice-gtk</code>":
        "<b>spice-gtk mit Python-Binding: nein.</b> Auch unter X11 kann SPICE nicht eingebettet werden; es wird immer auf einen externen Viewer zurückgegriffen. Installiere es mit:<br>&nbsp;&nbsp;<code>Debian/Ubuntu: python3-gi gir1.2-spiceclientgtk-3.0</code><br>&nbsp;&nbsp;<code>Arch: python-gobject spice-gtk</code>",
    "<b>VNC</b><br><span style='color:#2e7d32;'>✓</span> Compatible con cualquier gráfico virtual (VirtIO-GPU 2D, QXL, std).<br><span style='color:#2e7d32;'>✓</span> Se puede embeber dentro de la app, incluso en Wayland.<br><span style='color:#2e7d32;'>✓</span> Muchos visores externos disponibles (gvncviewer, vncviewer, remmina).<br><span style='color:#2e7d32;'>✓</span> Sin dependencias adicionales en el guest para funcionar.<br><span style='color:#c62828;'>✗</span> Sin aceleración 3D ni streaming de video (redibuja por regiones).<br><span style='color:#c62828;'>✗</span> Clipboard limitado: solo texto, y el guest necesita <code>vncconfig</code> corriendo.<br><span style='color:#c62828;'>✗</span> Sin audio remoto.<br><span style='color:#c62828;'>✗</span> Menos fluido en uso intensivo (vídeo, animaciones, 3D).":
        "<b>VNC</b><br><span style='color:#2e7d32;'>✓</span> Kompatibel mit jeder virtuellen Grafik (VirtIO-GPU 2D, QXL, std).<br><span style='color:#2e7d32;'>✓</span> Kann in die Anwendung eingebettet werden, auch unter Wayland.<br><span style='color:#2e7d32;'>✓</span> Viele externe Viewer verfügbar (gvncviewer, vncviewer, remmina).<br><span style='color:#2e7d32;'>✓</span> Keine zusätzlichen Abhängigkeiten im Gast erforderlich.<br><span style='color:#c62828;'>✗</span> Keine 3D-Beschleunigung und kein Video-Streaming (Neuzeichnung nach Regionen).<br><span style='color:#c62828;'>✗</span> Eingeschränkte Zwischenablage: nur Text, und der Gast benötigt ein laufendes <code>vncconfig</code>.<br><span style='color:#c62828;'>✗</span> Kein Remote-Audio.<br><span style='color:#c62828;'>✗</span> Weniger flüssig bei intensiver Nutzung (Video, Animationen, 3D).",
    "<b>SPICE</b><br><span style='color:#2e7d32;'>✓</span> Mejor rendimiento y fluidez en local (compresión + streaming de video).<br><span style='color:#2e7d32;'>✓</span> Clipboard bidireccional avanzado (con <code>spice-vdagent</code> en el guest).<br><span style='color:#2e7d32;'>✓</span> Audio remoto integrado.<br><span style='color:#2e7d32;'>✓</span> Varios monitores, redirección USB y carpetas compartidas nativas.<br><span style='color:#c62828;'>✗</span> No se puede embeber en Wayland (solo X11 con spice-gtk Python).<br><span style='color:#c62828;'>✗</span> Requiere un visor externo (spicy o remote-viewer) si no se puede embeber.<br><span style='color:#c62828;'>✗</span> Para aprovecharlo hay que instalar <code>spice-vdagent</code> en el guest.<br><span style='color:#c62828;'>✗</span> Incompatible con VirGL y Venus (usan OpenGL y obligan a la ventana nativa de QEMU).":
        "<b>SPICE</b><br><span style='color:#2e7d32;'>✓</span> Bessere lokale Leistung und Flüssigkeit (Kompression + Video-Streaming).<br><span style='color:#2e7d32;'>✓</span> Erweiterte bidirektionale Zwischenablage (mit <code>spice-vdagent</code> im Gast).<br><span style='color:#2e7d32;'>✓</span> Integriertes Remote-Audio.<br><span style='color:#2e7d32;'>✓</span> Mehrere Monitore, USB-Redirection und native gemeinsame Ordner.<br><span style='color:#c62828;'>✗</span> Kann unter Wayland nicht eingebettet werden (nur X11 mit spice-gtk Python).<br><span style='color:#c62828;'>✗</span> Erfordert einen externen Viewer (spicy oder remote-viewer), wenn kein Embedding möglich ist.<br><span style='color:#c62828;'>✗</span> Um es zu nutzen, muss <code>spice-vdagent</code> im Gast installiert werden.<br><span style='color:#c62828;'>✗</span> Inkompatibel mit VirGL und Venus (sie verwenden OpenGL und erzwingen das QEMU-native Fenster).",
    "<b>Híbrida (VNC embebido + SPICE externo)</b><br><span style='color:#2e7d32;'>✓</span> Lo mejor de ambos: VNC siempre visible dentro de la app, SPICE para rendimiento y clipboard.<br><span style='color:#2e7d32;'>✓</span> Funciona en cualquier sesión: Wayland o X11.<br><span style='color:#2e7d32;'>✓</span> Si spicy falla o lo cierras, el widget VNC sigue funcionando.<br><span style='color:#2e7d32;'>✓</span> Útil para ver la VM en dos monitores o para grabar y controlar a la vez.<br><span style='color:#c62828;'>✗</span> Consume más recursos: QEMU mantiene dos servidores de display en paralelo.<br><span style='color:#c62828;'>✗</span> Verás la misma VM en dos ventanas (dentro de la app y en la de spicy).<br><span style='color:#c62828;'>✗</span> La configuración del guest para sacar partido a SPICE (vdagent, drivers) hay que hacerla igual.<br><span style='color:#c62828;'>✗</span> Como SPICE, incompatible con VirGL y Venus.":
        "<b>Hybrid (eingebettetes VNC + externes SPICE)</b><br><span style='color:#2e7d32;'>✓</span> Das Beste aus beiden: VNC immer in der Anwendung sichtbar, SPICE für Leistung und Zwischenablage.<br><span style='color:#2e7d32;'>✓</span> Funktioniert in jeder Sitzung: Wayland oder X11.<br><span style='color:#2e7d32;'>✓</span> Wenn spicy fehlschlägt oder geschlossen wird, arbeitet das VNC-Widget weiter.<br><span style='color:#2e7d32;'>✓</span> Nützlich, um die VM auf zwei Monitoren zu sehen oder gleichzeitig aufzuzeichnen und zu steuern.<br><span style='color:#c62828;'>✗</span> Verbraucht mehr Ressourcen: QEMU unterhält zwei Display-Server parallel.<br><span style='color:#c62828;'>✗</span> Dieselbe VM erscheint in zwei Fenstern (in der Anwendung und in spicy).<br><span style='color:#c62828;'>✗</span> Die Konfiguration des Gastes für SPICE (vdagent, Treiber) muss trotzdem erfolgen.<br><span style='color:#c62828;'>✗</span> Wie SPICE inkompatibel mit VirGL und Venus.",
    "<b>Gráficos compatibles con VNC / SPICE / Híbrida:</b> <b>Automático</b>, <b>VirtIO-GPU 2D</b> o <b>QXL</b>.<br>Con <b>VirGL</b> o <b>Venus</b> seleccionados, QEMU abre su propia ventana y no expone VNC/SPICE; es el único modo compatible con esos gráficos 3D.":
        "<b>Mit VNC / SPICE / Hybrid kompatible Grafik:</b> <b>Automatisch</b>, <b>VirtIO-GPU 2D</b> oder <b>QXL</b>.<br>Bei ausgewähltem <b>VirGL</b> oder <b>Venus</b> öffnet QEMU ein eigenes Fenster und stellt VNC/SPICE nicht bereit; dies ist der einzige mit dieser 3D-Grafik kompatible Modus.",
    "Consola externa": "Externe Konsole",
    "Selecciona primero una máquina virtual.": "Wähle zuerst eine virtuelle Maschine aus.",
    "No se encontró ningún visor {0} instalado.\n\n":
        "Es wurde kein {0}-Viewer installiert gefunden.\n\n",
    "Instala gvncviewer o tigervnc (vncviewer).":
        "Installiere gvncviewer oder tigervnc (vncviewer).",
    "Instala spicy (spice-gtk) o remote-viewer (virt-viewer).":
        "Installiere spicy (spice-gtk) oder remote-viewer (virt-viewer).",
    "Todavía no puedo determinar el puerto SPICE de esta VM.\n\n"
    "La VM debe estar corriendo para que QEMU haya elegido un\n"
    "puerto.":
        "Der SPICE-Port dieser VM kann noch nicht bestimmt werden.\n\n"
        "Die VM muss laufen, damit QEMU einen Port ausgewählt hat.",
    "El socket {0} todavía no existe.\n\n"
    "La VM debe estar corriendo con ese protocolo seleccionado.":
        "Der Socket {0} existiert noch nicht.\n\n"
        "Die VM muss mit diesem ausgewählten Protokoll laufen.",

    # ================================================================
    # Tanda 2d-2c: labels dinamicos de graficos
    # ================================================================
    "No detectada": "Nicht erkannt",
    "✓ OpenGL": "✓ OpenGL",
    "✗ OpenGL": "✗ OpenGL",
    "✓ VirGL": "✓ VirGL",
    "✓ VirGL instalado": "✓ VirGL installiert",
    "✗ VirGL": "✗ VirGL",
    "✓ Vulkan": "✓ Vulkan",
    "✗ Vulkan": "✗ Vulkan",
    "VGA estándar (QEMU -vga std)": "Standard-VGA (QEMU -vga std)",
    "VGA de OSX-KVM (VGA virtual)": "OSX-KVM-VGA (virtuelle VGA)",
    "gestionada por OpenCore/OSX-KVM": "verwaltet von OpenCore/OSX-KVM",
    "VirtIO-GPU + VirGL 3D": "VirtIO-GPU + VirGL 3D",
    "OpenGL / VirGL": "OpenGL / VirGL",
    "VirtIO-GPU 2D": "VirtIO-GPU 2D",
    "sin aceleración 3D": "ohne 3D-Beschleunigung",
    "VGA estándar de QEMU": "Standard-VGA von QEMU",
    "<b>Automático → {0}</b><br>Aceleración: {1}":
        "<b>Automatisch → {0}</b><br>Beschleunigung: {1}",
    "VirtIO-GPU + Venus/Vulkan 3D": "VirtIO-GPU + Venus/Vulkan 3D",
    "Red Hat QXL 2D": "Red Hat QXL 2D",
    "VMware SVGA II": "VMware SVGA II",
    "<b>Usará: {0}</b>": "<b>Verwendet: {0}</b>",
    "Host GPU: {0}<br>{1}  |  {2}  |  {3}<br>{4}":
        "Host-GPU: {0}<br>{1}  |  {2}  |  {3}<br>{4}",
    "Host GPU: no se pudo determinar automáticamente.<br>Automático: se seleccionará el modo gráfico compatible disponible.":
        "Host-GPU: konnte nicht automatisch ermittelt werden.<br>Automatisch: Der verfügbare kompatible Grafikmodus wird ausgewählt.",
    "⚠ Android-x86 9.0 (kernel 4.9) no incluye driver VirtIO-GPU y cae a un shell de rescate con 'Detecting Android-x86…'. Usa 'Automático' o 'Red Hat QXL 2D'. Las ISOs con kernel 5.10+ o Bliss OS 15+ sí soportan VirtIO-GPU.":
        "⚠ Android-x86 9.0 (Kernel 4.9) enthält keinen VirtIO-GPU-Treiber und fällt in eine Rettungs-Shell mit 'Detecting Android-x86…'. Verwende 'Automatisch' oder 'Red Hat QXL 2D'. ISOs mit Kernel 5.10+ oder Bliss OS 15+ unterstützen VirtIO-GPU.",
    "⚠️ Android-x86 9.0 (kernel 4.9) no incluye driver VirtIO-GPU y cae a un shell de rescate con 'Detecting Android-x86…'. Usa 'Automático' o 'Red Hat QXL 2D'. Las ISOs con kernel 5.10+ o Bliss OS 15+ sí soportan VirtIO-GPU.":
        "⚠️ Android-x86 9.0 (Kernel 4.9) enthält keinen VirtIO-GPU-Treiber und fällt in eine Rettungs-Shell mit 'Detecting Android-x86…'. Verwende 'Automatisch' oder 'Red Hat QXL 2D'. ISOs mit Kernel 5.10+ oder Bliss OS 15+ unterstützen VirtIO-GPU.",
    "⚠ {0} + UEFI: el firmware OVMF puede no mostrar nada (pantalla negra) hasta que el guest cargue su propio driver de video. Si te pasa, prueba 'Automático' o 'VirtIO-GPU 2D'.":
        "⚠ {0} + UEFI: Die OVMF-Firmware zeigt möglicherweise nichts an (schwarzer Bildschirm), bis der Gast seinen eigenen Grafiktreiber lädt. Falls dies auftritt, versuche 'Automatisch' oder 'VirtIO-GPU 2D'.",
    "⚠️ {0} + UEFI: el firmware OVMF puede no mostrar nada (pantalla negra) hasta que el guest cargue su propio driver de video. Si te pasa, prueba 'Automático' o 'VirtIO-GPU 2D'.":
        "⚠️ {0} + UEFI: Die OVMF-Firmware zeigt möglicherweise nichts an (schwarzer Bildschirm), bis der Gast seinen eigenen Grafiktreiber lädt. Falls dies auftritt, versuche 'Automatisch' oder 'VirtIO-GPU 2D'.",
}
