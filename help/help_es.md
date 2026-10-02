**Virtual.Machine** es un asistente gráfico para crear y administrar máquinas virtuales con QEMU/KVM.

### Primeros pasos

- Pulsa **Nueva VM** en el panel izquierdo para crear una máquina virtual desde cero.
- Selecciona una VM en la lista para ver su estado y configurarla.
- Usa el botón **Iniciar** para arrancarla y el botón **Apagar** para detenerla.

### Panel derecho

- **Uso de recursos**: CPU, RAM, disco y red de la VM en vivo.
- **Información general**: estado, PID, IP, MAC, discos, snapshots y estado de la integración con el guest.
- **Último snapshot**: vista previa del snapshot más reciente.
- **Sugerencias**: avisos y recomendaciones según el estado de la VM.

### Pestañas de la máquina virtual

- **Resumen**: acciones sobre la VM (Clonar, Importar, Exportar, Eliminar).
- **Configuración**: hardware, almacenamiento, red, dispositivos y opciones avanzadas.
- **Passthrough**: pasar hardware físico (PCI/USB) a la VM.
- **Carpetas compartidas**: integrar el guest con el host.
- **Snapshots**: crear, restaurar y eliminar instantáneas.
- **Consola Gráfica**: ver la VM dentro de la app (si está disponible).
- **Consola de Progreso**: log detallado de la aplicación.

### Atajos de teclado

- **Ctrl+M**: abrir el menú de Medios (CD/DVD, USB).
- Dentro del widget VNC: hacer clic dentro para capturar el teclado. Clic fuera para liberarlo.
- En pantalla completa del VNC: la combinación configurada en la barra de la Consola Gráfica (por defecto Ctrl derecho).

### Problemas frecuentes

- **La VM no arranca**: revisa la Consola de Progreso. Pulsa **Salud de la VM** para diagnóstico.
- **Sin salida gráfica**: prueba a cambiar el modo en Configuración → Pantalla.
- **USB no se conecta**: comprueba los permisos en Passthrough → Permisos USB.
- **Teclas especiales no llegan al guest**: en Wayland, Meta/Super y Ctrl+Alt+F* no se pueden capturar por diseño. Inicia sesión en X11 si las necesitas.

---

Virtual.Machine — Asistente Multi-VM QEMU/KVM.
