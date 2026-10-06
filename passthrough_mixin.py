# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""Mixin: passthrough de hardware — IOMMU/VFIO (Intel VT-d, grupos IOMMU,
diagnóstico), dispositivos PCI, y dispositivos USB (detección, hotplug,
permisos/udev). Todo lo necesario para pasar hardware real a la VM.
"""
import os
import re
import glob
import json
import shutil
import subprocess
import time
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QApplication, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTreeWidgetItem, QFileDialog,
)


class PassthroughMixin:
    def _kernel_cmdline(self):
        try:
            with open("/proc/cmdline", "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        except Exception:
            return ""

    def _detect_boot_manager(self):
        """Detecta de forma conservadora el gestor de arranque y su configuración."""
        checks=[]
        # GRUB: en CachyOS puede existir /etc/default/grub aunque la regeneración
        # se realice con update-grub o grub-mkconfig.
        if os.path.exists("/etc/default/grub") and (shutil.which("grub-mkconfig") or shutil.which("update-grub") or os.path.exists("/boot/grub")):
            checks.append(("GRUB", "/etc/default/grub"))
        if os.path.exists("/etc/sdboot-manage.conf"):
            checks.append(("systemd-boot (sdboot-manage)", "/etc/sdboot-manage.conf"))
        if os.path.exists("/boot/loader/entries") or os.path.exists("/boot/loader/loader.conf"):
            checks.append(("systemd-boot", "/boot/loader"))
        if os.path.exists("/boot/refind_linux.conf"):
            checks.append(("rEFInd", "/boot/refind_linux.conf"))
        for path in ("/etc/limine.conf", "/boot/limine.conf"):
            if os.path.exists(path):
                checks.append(("Limine", path)); break
        return checks[0] if checks else ("Desconocido", "")

    def _read_text_file(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    def _prepare_intel_iommu(self):
        """Añade intel_iommu=on al gestor de arranque, con copia de seguridad."""
        diag=self._intel_vtd_diagnostic()
        if not diag.get("intel_cpu"):
            raise RuntimeError(self.tr(
                "El procesador no se identificó como Intel; no se aplicará intel_iommu=on."))
        manager,path=self._detect_boot_manager()
        if not path:
            raise RuntimeError(self.tr(
                "No pude identificar de forma segura el gestor de arranque."))
        if manager != "GRUB":
            raise RuntimeError(self.tr(
                "La preparación automática está implementada actualmente para GRUB. "
                "Gestor detectado: {0}."
            ).format(manager))
        old=self._read_text_file(path)
        if not old:
            raise RuntimeError(self.tr("No se pudo leer {0}.").format(path))
        m=re.search(r"(?m)^\s*GRUB_CMDLINE_LINUX_DEFAULT\s*=\s*([\"\'])(.*?)\1\s*$", old)
        if not m:
            raise RuntimeError(self.tr(
                "No se encontró GRUB_CMDLINE_LINUX_DEFAULT en /etc/default/grub."))
        opts=m.group(2).strip()
        if "intel_iommu=on" in opts:
            return {"manager":"GRUB","path":path,"changed":False,
                    "message": self.tr("intel_iommu=on ya está presente en /etc/default/grub.")}
        opts=(opts+" intel_iommu=on").strip()
        new_text=old[:m.start(2)]+opts+old[m.end(2):]
        import base64
        data=base64.b64encode(json.dumps({"path":path,"text":new_text},ensure_ascii=False).encode()).decode()
        script=(
            'import base64,json,shutil; '
            f'd=json.loads(base64.b64decode({data!r}).decode()); '
            'p=d["path"]; b=p+".vmmanager-backup-"+__import__("time").strftime("%Y%m%d-%H%M%S"); '
            'shutil.copy2(p,b); open(p,"w",encoding="utf-8").write(d["text"])'
        )
        r=subprocess.run(["pkexec","python3","-c",script],capture_output=True,text=True,timeout=60)
        if r.returncode!=0:
            raise RuntimeError(
                (r.stderr or r.stdout or self.tr("operación cancelada")).strip())
        regen=["update-grub"] if shutil.which("update-grub") else ["grub-mkconfig","-o","/boot/grub/grub.cfg"]
        rr=subprocess.run(["pkexec"]+regen,capture_output=True,text=True,timeout=120)
        if rr.returncode!=0:
            raise RuntimeError(
                self.tr("Se modificó /etc/default/grub, pero no se pudo regenerar grub.cfg: ")
                + (rr.stderr or rr.stdout or self.tr("error desconocido")).strip())
        return {"manager":"GRUB","path":path,"changed":True,
                "message": self.tr("Se añadió intel_iommu=on y se regeneró GRUB.")}

    def prepare_iommu_from_ui(self):
        d=self._intel_vtd_diagnostic()
        if d.get("intel_iommu_on") and d.get("active"):
            QMessageBox.information(self,self.tr("IOMMU / VT-d"),self.tr("El IOMMU ya aparece activo. No es necesario modificar el arranque."))
            return
        if not d.get("intel_cpu"):
            QMessageBox.warning(self,self.tr("IOMMU / VT-d"),self.tr("No se identificó un CPU Intel."))
            return
        manager,path=self._detect_boot_manager()
        ans=QMessageBox.question(
            self, self.tr("Preparar Intel IOMMU"),
            self.tr(
                "Se añadirá intel_iommu=on a la configuración del gestor de arranque.\n\n"
                "Se hará una copia de seguridad antes de modificarla y se solicitará autorización administrativa.\n\n"
                "Esto NO activa VT-d dentro de la BIOS/UEFI; esa parte debes habilitarla en el firmware.\n\n"
                "Gestor detectado: {0}\nArchivo: {1}\n\n¿Continuar?"
            ).format(manager, path or self.tr("no identificado")),
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if ans!=QMessageBox.StandardButton.Yes:
            return
        try:
            result=self._prepare_intel_iommu()
            self.refresh_vfio_diagnostics()
            QMessageBox.information(
                self, self.tr("IOMMU / VT-d"),
                result.get("message", self.tr("Configuración actualizada."))
                + self.tr("\n\nReinicia el equipo para que el parámetro tenga efecto."))
        except Exception as e:
            self._show_selectable_error(self.tr("No se pudo preparar IOMMU"),str(e))

    def open_firmware_setup(self):
        ans=QMessageBox.question(
            self, self.tr("Abrir UEFI/BIOS"),
            self.tr(
                "El equipo se reiniciará directamente a la configuración del firmware si el sistema lo permite.\n\n"
                "Busca una opción llamada Intel VT-d, Intel Virtualization Technology for Directed I/O, VT-d o similar y actívala.\n\n¿Reiniciar ahora?"
            ),
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if ans!=QMessageBox.StandardButton.Yes:
            return
        try:
            r=subprocess.run(["systemctl","reboot","--firmware-setup"],capture_output=True,text=True,timeout=8)
            if r.returncode!=0:
                raise RuntimeError(
                    (r.stderr or r.stdout
                     or self.tr("No se pudo solicitar el reinicio al firmware.")).strip())
        except Exception as e:
            self._show_selectable_error(self.tr("No se pudo abrir UEFI/BIOS"),str(e))

    def _intel_vtd_diagnostic(self):
        """Diagnóstico del VT-d/IOMMU del host. VT-d no suele exponer un "switch BIOS"
        directamente a userspace; se infiere mediante ACPI DMAR + IOMMU sysfs + logs del kernel."""
        arch = ""
        try:
            arch=subprocess.run(["uname","-m"],capture_output=True,text=True,timeout=3).stdout.strip()
        except Exception:
            pass
        cpu_intel=False
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read().lower()
            cpu_intel="genuineintel" in txt or "intel" in txt
        except Exception:
            pass
        cmd=self._kernel_cmdline()
        iommu_on = bool(re.search(r"(?:^|\s)(?:intel_iommu=on|iommu=on)(?:\s|$)", cmd))
        iommu_off = bool(re.search(r"(?:^|\s)(?:intel_iommu=off|iommu=off)(?:\s|$)", cmd))
        groups=sorted(glob.glob("/sys/kernel/iommu_groups/[0-9]*"), key=lambda x:int(os.path.basename(x)))
        dmar=False
        dmar_text=""
        # La tabla ACPI DMAR es una evidencia directa de que el firmware expone Intel VT-d.
        acpi_dmar_candidates=["/sys/firmware/acpi/tables/DMAR", "/sys/firmware/acpi/tables/data/DMAR"]
        if any(os.path.exists(x) for x in acpi_dmar_candidates):
            dmar=True
            dmar_text="ACPI DMAR presente en /sys/firmware/acpi/tables"
        # Complementamos con kernel log; algunas distros no permiten leer dmesg al usuario.
        for cmdline in (["dmesg"], ["journalctl","-k","-b","--no-pager","-n","400"]):
            try:
                r=subprocess.run(cmdline,capture_output=True,text=True,timeout=5)
                text=(r.stdout or "")
                if re.search(r"\bDMAR[: ]|IOMMU.*enabled|Intel-IOMMU", text, re.I):
                    dmar=True; dmar_text=text
                    break
            except Exception:
                continue
        iommu_classes=glob.glob("/sys/class/iommu/*")
        active=bool(groups or iommu_classes or re.search(r"IOMMU.*enabled", dmar_text, re.I))
        if iommu_off:
            state=self.tr("Desactivado por parámetro del kernel")
        elif active and (dmar or iommu_on or iommu_classes):
            state=self.tr("Activo")
        elif dmar:
            state=self.tr("VT-d detectado por firmware/kernel; IOMMU sin grupos visibles")
        else:
            state=self.tr("No detectado")
        # Reportes de BIOS: DMAR ACPI es la mejor evidencia disponible desde Linux.
        firmware = self.tr("Detectado") if dmar else self.tr("No confirmado")
        manager,manager_path=self._detect_boot_manager()
        return {
            "arch": arch, "intel_cpu": cpu_intel, "cmdline": cmd, "intel_iommu_on": iommu_on,
            "intel_iommu_off": iommu_off, "groups": groups, "iommu_classes": iommu_classes,
            "active": active, "dmar": dmar, "state": state, "firmware": firmware,
            "boot_manager": manager, "boot_path": manager_path
        }

    def _pci_iommu_group(self, address):
        link=f"/sys/bus/pci/devices/{address}/iommu_group"
        try:
            if os.path.islink(link):
                target=os.path.realpath(link)
                return int(os.path.basename(target))
        except Exception:
            pass
        return None

    def _pci_group_members(self, group):
        if group is None:
            return []
        base=f"/sys/kernel/iommu_groups/{int(group)}/devices"
        out=[]
        for path in sorted(glob.glob(os.path.join(base,"*"))):
            out.append(os.path.basename(path))
        return out

    def _detect_pci_devices(self):
        out=[]
        if shutil.which("lspci"):
            try:
                r=subprocess.run(["lspci","-Dnn"],capture_output=True,text=True,timeout=5)
                for line in r.stdout.splitlines():
                    m=re.match(r"(?P<addr>[0-9a-fA-F:.]+)\s+(?P<desc>.+)",line)
                    if not m: continue
                    addr=m.group("addr"); desc=m.group("desc"); driver=""
                    drv=os.path.join("/sys/bus/pci/devices",addr,"driver")
                    if os.path.islink(drv): driver=os.path.basename(os.path.realpath(drv))
                    group=self._pci_iommu_group(addr)
                    members=self._pci_group_members(group)
                    group_ok=group is not None
                    vfio_ready=(driver=="vfio-pci" and group_ok)
                    shared=[x for x in members if x != addr]
                    status=(self.tr("✓ Listo para VFIO") if vfio_ready else
                            (self.tr("⚠ Sin grupo IOMMU") if not group_ok else
                             (self.tr("⚠ Comparte grupo IOMMU") if shared
                              else self.tr("⚠ Requiere preparación VFIO"))))
                    out.append({
                        "kind":"pci","address":addr,"name":desc,"driver":driver,
                        "iommu_group":group,"iommu_members":members,"iommu_shared":shared,
                        "vfio_ready":vfio_ready,"status":status
                    })
            except Exception: pass
        return out

    def refresh_vfio_diagnostics(self):
        if not hasattr(self, "vfio_diag_label"):
            return
        d=self._intel_vtd_diagnostic()
        if d["state"]==self.tr("Activo"):
            status=self.tr("✅ Intel VT-d / IOMMU activo")
        elif d["dmar"]:
            status=self.tr("⚠ VT-d detectado por firmware, pero no hay grupos IOMMU utilizables")
        else:
            status=self.tr("❌ Intel VT-d / IOMMU no detectado")
        cmd=d["cmdline"] or self.tr("(sin datos)")
        ready=len([x for x in self._detect_pci_devices() if x.get("vfio_ready")])
        text=self.tr(
            "<b>{0}</b><br>"
            "Firmware/ACPI DMAR: {1}<br>"
            "Grupos IOMMU: {2} &nbsp;|&nbsp; PCI listos para VFIO: {3}<br>"
            "Gestor de arranque: {4}<br>"
            "Parámetros kernel: <code>{5}</code>"
        ).format(
            status, d['firmware'], len(d['groups']), ready,
            d.get('boot_manager', self.tr('Desconocido')),
            cmd,
        )
        if not d["intel_cpu"]:
            text += self.tr("<br>⚠ El CPU no se identificó como Intel; comprobar diagnóstico AMD/IOMMU.")
        elif d.get("dmar") and not d.get("intel_iommu_on"):
            text += self.tr("<br>Recomendación: usar <b>Preparar intel_iommu=on</b> y reiniciar. Si tras reiniciar no hay grupos, revisar VT-d en BIOS/UEFI.")
        elif not d["active"]:
            text += self.tr("<br>Recomendación: habilitar Intel VT-d en BIOS/UEFI y después activar <code>intel_iommu=on</code> en el arranque.")
        self.vfio_diag_label.setText(text)

    def _vfio_diagnostic_text(self):
        d=self._intel_vtd_diagnostic()
        devices=self._detect_pci_devices()
        _yn = lambda b: self.tr("sí") if b else self.tr("no")
        lines=[
            self.tr("=== DIAGNÓSTICO INTEL VT-d / IOMMU / VFIO ==="),
            self.tr("Estado: {0}").format(d['state']),
            self.tr("Arquitectura: {0}").format(d['arch'] or self.tr("desconocida")),
            self.tr("CPU Intel detectado: {0}").format(_yn(d['intel_cpu'])),
            self.tr("Firmware/ACPI DMAR: {0}").format(d['firmware']),
            self.tr("intel_iommu=on en kernel actual: {0}").format(_yn(d['intel_iommu_on'])),
            self.tr("IOMMU desactivado por parámetro: {0}").format(_yn(d['intel_iommu_off'])),
            self.tr("Grupos IOMMU: {0}").format(len(d['groups'])),
            self.tr("Clases IOMMU: {0}").format(len(d['iommu_classes'])),
            self.tr("Gestor de arranque: {0}").format(
                d.get('boot_manager') or self.tr("desconocido")),
            self.tr("Configuración: {0}").format(
                d.get('boot_path') or self.tr("no identificada")),
            self.tr("Parámetros kernel: {0}").format(
                d['cmdline'] or self.tr("(sin datos)")),
            "", self.tr("=== DISPOSITIVOS PCI ===")
        ]
        for x in devices:
            lines.append(self.tr(
                "{0} | {1} | driver={2} | grupo={3} | estado={4}"
            ).format(
                x['address'], x['name'],
                x.get('driver') or self.tr("sin driver"),
                x.get('iommu_group') if x.get('iommu_group') is not None else "—",
                x.get('status',''),
            ))
        return "\n".join(lines)

    def copy_vfio_diagnostic(self):
        try:
            QApplication.clipboard().setText(self._vfio_diagnostic_text())
            QMessageBox.information(
                self, self.tr('Diagnóstico VFIO'),
                self.tr('Diagnóstico copiado al portapapeles.'))
        except Exception as e:
            self._show_selectable_error(
                self.tr('No se pudo copiar el diagnóstico'), str(e))

    def vfio_diagnostic_details(self):
        from PyQt6.QtWidgets import QPlainTextEdit
        dlg=QDialog(self)
        dlg.setWindowTitle(self.tr("Diagnóstico Intel VT-d / IOMMU / VFIO"))
        dlg.resize(900,620)
        lay=QVBoxLayout(dlg)
        edit=QPlainTextEdit()
        edit.setReadOnly(True)
        edit.setPlainText(self._vfio_diagnostic_text())
        edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        lay.addWidget(edit,1)
        row=QHBoxLayout()
        copy=QPushButton(self.tr("📋 Copiar"))
        copy.clicked.connect(lambda: QApplication.clipboard().setText(edit.toPlainText()))
        close=QPushButton(self.tr("Cerrar"))
        close.clicked.connect(dlg.accept)
        row.addWidget(copy); row.addStretch(); row.addWidget(close)
        lay.addLayout(row)
        dlg.exec()

    def _detect_usb_devices(self):
        out=[]
        if shutil.which("lsusb"):
            try:
                r=subprocess.run(["lsusb"],capture_output=True,text=True,timeout=5)
                for line in r.stdout.splitlines():
                    m=re.search(r"Bus (\d+) Device (\d+): ID ([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(.*)",line)
                    if not m:
                        m2=re.search(r"Bus (\d+) Device (\d+): (.*)",line)
                        if m2:
                            # No identificador USB legible: conservar para diagnóstico, pero sin inventar VID/PID.
                            out.append({"kind":"usb","bus":m2.group(1),"addr":m2.group(2),"name":m2.group(3)})
                        continue
                    bus, addr, vid, pid, name = m.groups()
                    # Los root hubs/hubs no deben pasarse a la VM: QEMU indica explícitamente que no se utilicen hubs.
                    low=name.lower()
                    if "root hub" in low or "hub" in low and "usb" in low and ("linux foundation" in low or "hub" == low.strip()):
                        continue
                    item={"kind":"usb","bus":bus,"addr":addr,"vendorid":vid.lower(),"productid":pid.lower(),"name":name}
                    # lsusb -t puede ser necesario para conocer el puerto físico; se deja opcional.
                    out.append(item)
            except Exception:
                pass
        return out

    def _usb_device_node(self, d):
        """Ruta del nodo USB físico en /dev/bus/usb para el dispositivo detectado."""
        bus=str(d.get("bus") or "").strip()
        addr=str(d.get("addr") or "").strip()
        if not bus or not addr:
            return ""
        try:
            return f"/dev/bus/usb/{int(bus):03d}/{int(addr):03d}"
        except ValueError:
            return ""

    def _usb_access_status(self, d):
        """Comprueba si el usuario actual puede abrir el nodo USB."""
        node=self._usb_device_node(d)
        if not node:
            return False, "No se pudo determinar el nodo /dev/bus/usb."
        if not os.path.exists(node):
            return False, self.tr(
                "No existe {0}. El número Device puede haber cambiado; "
                "vuelve a detectar USB.").format(node)
        if os.access(node, os.R_OK | os.W_OK):
            return True, node
        return False, self.tr(
            "Sin acceso de lectura/escritura a {0}.").format(node)

    # ==================================================================
    # Aviso de policy kit para pkexec
    # ==================================================================
    # pkexec necesita un agente de autenticación (polkit-agent) para
    # mostrar el prompt gráfico. Si el agente no está corriendo (KDE con
    # polkit-kde-agent roto, sesiones sin display, etc.), pkexec puede
    # quedarse esperando sin mostrar nada.
    #
    # Este helper se llama UNA VEZ por sesión, antes del primer pkexec,
    # para avisar al usuario. No hace nada si:
    #   • El usuario es root (no hace falta pkexec).
    #   • Ya se avisó en esta sesión.
    #   • El usuario tiene DISPLAY o WAYLAND_DISPLAY (asumimos agente OK).

    _pkexec_hint_shown = False

    def _maybe_warn_pkexec(self, operation_label=""):
        """Avisa si pkexec podría no mostrar prompt en este entorno."""
        if getattr(self, "_pkexec_hint_shown", False):
            return
        import os as _os
        if _os.geteuid() == 0:
            self._pkexec_hint_shown = True
            return
        # Con DISPLAY/WAYLAND_DISPLAY asumimos que polkit-agent está OK.
        if _os.environ.get("DISPLAY") or _os.environ.get("WAYLAND_DISPLAY"):
            self._pkexec_hint_shown = True
            return
        # Sin display: avisamos.
        self._pkexec_hint_shown = True
        try:
            label = f" ({operation_label})" if operation_label else ""
            self.log_message(
                f"[AVISO] Se va a invocar pkexec{label}, pero esta sesión no "
                "tiene DISPLAY ni WAYLAND_DISPLAY. En terminales puras pkexec "
                "necesita un agente polkit corriendo o puede quedarse esperando "
                "sin mostrar el prompt. Si no ves el diálogo de contraseña en "
                "3-5 s, cancela con Ctrl+C y ejecuta el comando con 'sudo' en "
                "una terminal con entorno gráfico."
            )
        except Exception:
            pass

    def _run_privileged(self, argv, purpose):
        """Ejecuta una acción administrativa con pkexec, solicitando autorización al usuario."""
        pkexec=shutil.which("pkexec")
        if not pkexec:
            raise RuntimeError(self.tr(
                "No se encontró 'pkexec'. No puedo solicitar permisos "
                "administrativos automáticamente."))
        # Aviso proactivo si el prompt de pkexec podría no aparecer.
        self._maybe_warn_pkexec(purpose)
        try:
            r=subprocess.run([pkexec] + argv, capture_output=True, text=True, timeout=30)
        except Exception as e:
            raise RuntimeError(self.tr(
                "No se pudo ejecutar la acción administrativa ({0}): {1}"
            ).format(purpose, e))
        if r.returncode != 0:
            detail=(r.stderr or r.stdout or "operación cancelada").strip()
            raise RuntimeError(self.tr(
                "No se pudo realizar la acción administrativa ({0}). {1}"
            ).format(purpose, detail))
        return True

    def _usb_block_devices_for(self, d):
        """Encuentra particiones/discos USB de este VID/PID para poder desmontarlos sin tocar otros USB."""
        matches=[]
        vid=str(d.get("vendorid") or "").lower()
        pid=str(d.get("productid") or "").lower()
        try:
            r=subprocess.run(["lsblk","-J","-o","PATH,TYPE,MOUNTPOINTS,TRAN"],capture_output=True,text=True,timeout=5)
            if r.returncode!=0:
                return []
            data=json.loads(r.stdout or "{}")
        except Exception:
            return []
        for dev in data.get("blockdevices",[]):
            path=dev.get("path") or ""
            tran=str(dev.get("tran") or "").lower()
            if tran != "usb" or not path or dev.get("type") not in ("disk","part"):
                continue
            try:
                pr=subprocess.run(["udevadm","info","--query=property","--name",path],capture_output=True,text=True,timeout=3)
                props={}
                for line in pr.stdout.splitlines():
                    if "=" in line:
                        k,v=line.split("=",1); props[k]=v.lower()
                pvid=props.get("ID_VENDOR_ID","").lower()
                ppid=props.get("ID_MODEL_ID","").lower()
                if vid and pid and pvid==vid and ppid==pid:
                    mounts=dev.get("mountpoints") or []
                    if isinstance(mounts,str): mounts=[mounts]
                    matches.append((path,[m for m in mounts if m]))
            except Exception:
                continue
        return matches

    def _refresh_usb_descriptor(self, d):
        """Actualiza bus/device del USB a partir de VID:PID después de desmontarlo.
        Los números Device de /dev/bus/usb pueden cambiar durante el desmontaje/reset."""
        if not isinstance(d, dict) or d.get("kind") != "usb":
            return d
        vid=str(d.get("vendorid") or "").strip().lower()
        pid=str(d.get("productid") or "").strip().lower()
        if not (vid and pid):
            return d
        try:
            fresh=self._detect_usb_devices()
        except Exception:
            return d
        for item in fresh:
            if (str(item.get("vendorid") or "").lower()==vid and
                str(item.get("productid") or "").lower()==pid):
                # Conservamos la identidad/configuración, pero reemplazamos bus/addr actuales.
                d["bus"]=item.get("bus", d.get("bus"))
                d["addr"]=item.get("addr", d.get("addr"))
                d["name"]=item.get("name", d.get("name"))
                if item.get("port"):
                    d["port"]=item.get("port")
                break
        return d

    def _set_usb_acl_with_retry(self, d, retries=3):
        """Aplica ACL al nodo USB actual, refrescando Bus/Device si el nodo cambió."""
        uid=str(os.getuid())
        last=None
        for attempt in range(max(1,retries)):
            self._refresh_usb_descriptor(d)
            node=self._usb_device_node(d)
            if not node or not os.path.exists(node):
                last=self.tr(
                    "No existe el nodo USB actual {0}; el dispositivo "
                    "pudo cambiar de dirección."
                ).format(node or self.tr("(desconocido)"))
            else:
                ok,detail=self._usb_access_status(d)
                if ok:
                    return node
                try:
                    self._run_privileged(
                        ["/usr/bin/setfacl","-m",f"u:{uid}:rw",node],
                        self.tr("dar acceso temporal al dispositivo USB"))
                    ok2,detail2=self._usb_access_status(d)
                    if ok2:
                        return node
                    last=detail2
                except Exception as e:
                    last=str(e)
            if attempt < retries-1:
                time.sleep(0.4)
        raise RuntimeError(last or "No se pudo conceder acceso al dispositivo USB.")

    def _prepare_usb_passthrough(self, devices, interactive=True):
        """Prepara USB passthrough: desmonta el almacenamiento y concede ACL temporal.
        Importante: primero desmonta y luego vuelve a detectar el USB, porque el nodo
        /dev/bus/usb/BBB/DDD puede cambiar durante el proceso."""
        usb_devices=[d for d in (devices or []) if d.get("kind")=="usb"]
        if not usb_devices:
            return True

        # 1) Desmontar los sistemas de archivos del USB seleccionado.
        unmount_fail=[]
        for d in usb_devices:
            for path,mounts in self._usb_block_devices_for(d):
                for mnt in mounts:
                    udisks=shutil.which("udisksctl")
                    done=False
                    if udisks:
                        try:
                            r=subprocess.run([udisks,"unmount","-b",path],capture_output=True,text=True,timeout=30)
                            done=(r.returncode==0)
                        except Exception:
                            done=False
                    if not done:
                        unmount_fail.append((path,mnt))
        if unmount_fail:
            lines="\n".join(f"• {path} ({mnt})" for path,mnt in unmount_fail)
            try:
                self._run_privileged(["/bin/umount"]+[x[0] for x in unmount_fail], "desmontar el almacenamiento USB")
            except Exception as e:
                raise RuntimeError(self.tr(
                    "No pude desmontar automáticamente el almacenamiento USB:\n"
                    "{0}\n\n{1}"
                ).format(lines, e))

        # 2) Después del desmontaje, refrescar siempre la dirección del dispositivo.
        #    Así evitamos setfacl sobre un /dev/bus/usb/XXX/YYY que dejó de existir.
        for d in usb_devices:
            self._refresh_usb_descriptor(d)

        # 3) Comprobar/otorgar acceso al usuario actual.
        for d in usb_devices:
            ok,detail=self._usb_access_status(d)
            if not ok:
                self._set_usb_acl_with_retry(d, retries=4)
            ok2,detail2=self._usb_access_status(d)
            if not ok2:
                raise RuntimeError(self.tr(
                    "El USB sigue sin acceso después de preparar el dispositivo: {0}"
                ).format(detail2))
        return True

    def _usb_runtime_diagnostics(self, d):
        ok, detail=self._usb_access_status(d)
        node=self._usb_device_node(d)
        return self.tr(
            "USB {0} | nodo: {1} | acceso usuario: {2} | {3}"
        ).format(
            d.get('name',''),
            node or self.tr("desconocido"),
            self.tr("OK") if ok else self.tr("NO"),
            detail,
        )

    # ==================================================================
    # Permisos USB del host
    # ==================================================================
    # La regla udev que instalamos usa TAG+="uaccess" (systemd-logind):
    # concede acceso al usuario de la sesión activa sin necesidad de
    # añadirlo a ningún grupo ni cerrar sesión. Es el mecanismo estándar
    # que ya usan pulse/pipewire para tarjetas de sonido, webcams, etc.

    _USB_UDEV_RULE_PATH = "/etc/udev/rules.d/50-vm-manager-usb.rules"
    _USB_UDEV_RULE_CONTENT = (
        "# Virtual.Machine — permite passthrough USB al usuario activo.\n"
        "# Instalado automáticamente desde la pestaña Passthrough.\n"
        "# Solo se aplica a dispositivos USB; el resto de reglas no se toca.\n"
        "SUBSYSTEM==\"usb\", ACTION==\"add\", TAG+=\"uaccess\"\n"
    )

    def _usb_perm_state(self):
        """Devuelve (instalada: bool, detalle: str).

        instalada=True si:
          - Existe el archivo de reglas en /etc/udev/rules.d/
          - Y su contenido contiene la regla TAG+="uaccess" para USB.
        """
        path = self._USB_UDEV_RULE_PATH
        if not os.path.isfile(path):
            return False, "no instalada"
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError as e:
            return False, self.tr("no se pudo leer ({0})").format(e)
        if 'SUBSYSTEM=="usb"' in content and 'uaccess' in content:
            return True, "instalada"
        return False, "archivo presente pero sin la regla esperada"

    def refresh_usb_permissions_status(self):
        """Actualiza el estado visible del panel 'Permisos USB del host'."""
        if not hasattr(self, "usb_perm_status_label"):
            return
        try:
            installed, detail = self._usb_perm_state()
        except Exception as e:
            installed, detail = False, self.tr(
                "error al comprobar: {0}").format(e)
        if installed:
            self.usb_perm_status_label.setText(
                self.tr(
                    "✅ Permisos USB: OK ({0}). El passthrough en caliente "
                    "no pedirá contraseña."
                ).format(detail)
            )
            self.usb_perm_status_label.setStyleSheet(
                "font-weight: bold; color: #2e7d32;"
            )
            if hasattr(self, "btn_usb_perm_install"):
                self.btn_usb_perm_install.setEnabled(False)
                self.btn_usb_perm_install.setToolTip(
                    self.tr(
                        "Los permisos USB ya están configurados.\n"
                        "Si quieres desinstalarlos, borra:\n"
                        "{0}"
                    ).format(self._USB_UDEV_RULE_PATH)
                )
        else:
            self.usb_perm_status_label.setText(
                self.tr(
                    "⚠ Permisos USB: {0}. El passthrough en caliente "
                    "pedirá contraseña cada vez."
                ).format(detail)
            )
            self.usb_perm_status_label.setStyleSheet(
                "font-weight: bold; color: #c62828;"
            )
            if hasattr(self, "btn_usb_perm_install"):
                self.btn_usb_perm_install.setEnabled(True)

    def install_usb_permissions(self):
        """Instala la regla udev con pkexec. Idempotente."""
        if shutil.which("pkexec") is None:
            QMessageBox.critical(
                self, self.tr("Permisos USB"),
                self.tr(
                    "No se encontró 'pkexec'. Instálalo (paquete 'polkit') para "
                    "que la aplicación pueda solicitar permisos administrativos "
                    "de forma gráfica."
                ),
            )
            return
        if shutil.which("udevadm") is None:
            QMessageBox.critical(
                self, self.tr("Permisos USB"),
                self.tr(
                    "No se encontró 'udevadm'. Este sistema parece no usar udev "
                    "para gestionar dispositivos USB. Aplica los permisos "
                    "manualmente según tu distribución."
                ),
            )
            return

        resp = QMessageBox.question(
            self, self.tr("Configurar permisos USB"),
            "Se creará (o actualizará) el archivo:\n\n"
            f"    {self._USB_UDEV_RULE_PATH}\n\n"
            "con la regla que concede acceso a los dispositivos USB al "
            "usuario activo (TAG+=\"uaccess\"). Esta regla:\n\n"
            "  • Solo afecta a dispositivos USB.\n"
            "  • No cambia permisos de discos, red ni otros subsistemas.\n"
            "  • No requiere añadir al usuario a ningún grupo ni cerrar sesión.\n\n"
            "Se pedirá autorización administrativa con pkexec.\n\n¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        # El script que se ejecuta con pkexec: escribe la regla, la marca
        # con permisos 644 (lectura para todos, escritura solo root) y
        # recarga udev para que se aplique sin reiniciar.
        script = (
            "set -e\n"
            "mkdir -p /etc/udev/rules.d\n"
            f"cat > {self._USB_UDEV_RULE_PATH} <<'VM_MANAGER_USB_EOF'\n"
            + self._USB_UDEV_RULE_CONTENT
            + "VM_MANAGER_USB_EOF\n"
            f"chmod 644 {self._USB_UDEV_RULE_PATH}\n"
            "udevadm control --reload-rules\n"
            "udevadm trigger --subsystem-match=usb\n"
        )

        self.log_message("==> Instalando permisos USB del host (regla udev)…")
        try:
            result = subprocess.run(
                ["pkexec", "sh", "-c", script],
                capture_output=True, text=True, timeout=30,
            )
        except subprocess.TimeoutExpired:
            QMessageBox.warning(self, self.tr("Permisos USB"),
                                self.tr("La operación tardó demasiado. Vuelve a intentarlo."))
            return
        except Exception as e:
            QMessageBox.critical(self, self.tr("Permisos USB"),
                                 f"No se pudo ejecutar pkexec:\n\n{e}")
            return

        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip() or "cancelado"
            QMessageBox.warning(
                self, self.tr("Permisos USB"),
                f"No se pudo instalar la regla udev.\n\n{detail}",
            )
            self.log_message(f"[AVISO] Permisos USB: {detail}")
            self.refresh_usb_permissions_status()
            return

        self.log_message("==> Permisos USB instalados correctamente.")
        self.refresh_usb_permissions_status()
        QMessageBox.information(
            self, self.tr("Permisos USB"),
            "Regla udev instalada correctamente.\n\n"
            "Los USB que ya estén conectados al host pueden necesitar "
            "desenchufarse y volver a enchufarse para recibir el nuevo ACL.\n\n"
            "A partir de ahora, el passthrough USB en caliente no pedirá "
            "contraseña.",
        )

    # ==================================================================
    # Menú rápido de USB (botón "🔌 USB" en la fila de acciones)
    # ==================================================================
    # Reutiliza la lógica existente de passthrough_usb_hotplug/unplug:
    # selecciona el dispositivo en el árbol de Passthrough y delega en
    # esos métodos, para no duplicar el código de permisos, desmontaje
    # y setfacl.

    def _goto_passthrough_tab(self):
        """Navega a la seccion Passthrough (Config VM -> sidebar).

        split_vm_host_config_v1: Passthrough ya no es una pestana propia;
        vive como seccion del sidebar de Configuracion VM. Este metodo
        ahora va a la pestana "Configuracion VM" y selecciona su fila.
        """
        try:
            self.main_tabs.setCurrentIndex(
                getattr(self, "_passthrough_tab_index", 1)
            )
            row = getattr(self, "_passthrough_sidebar_row", None)
            if row is not None and hasattr(self, "config_sidebar"):
                self.config_sidebar.setCurrentRow(int(row))
        except Exception:
            pass

    @staticmethod
    def _usb_device_key(d):
        """Clave estable para comparar dos referencias al mismo USB.

        Dos llamadas distintas a _detect_usb_devices() devuelven dicts
        diferentes para el mismo dispositivo físico. La clave debe ser
        algo que no cambie entre llamadas (evitamos la dirección /dev/bus
        que puede variar tras desmontar y volver a montar).
        """
        return (
            str(d.get("vendorid") or "").lower(),
            str(d.get("productid") or "").lower(),
            str(d.get("bus") or ""),
            str(d.get("addr") or ""),
        )

    def _usb_device_id(self, d):
        """Mismo device_id que calcula passthrough_usb_hotplug/unplug.

        Debe replicarse exactamente para que podamos comprobar si el
        dispositivo YA está conectado mirando la salida de 'info usb'.
        """
        hostport = str(d.get("port") or "").strip()
        vid = str(d.get("vendorid") or "").strip().lower()
        pid = str(d.get("productid") or "").strip().lower()
        bus = str(d.get("bus") or "").strip()
        addr = str(d.get("addr") or "").strip()
        if hostport:
            stable_id = f"port_{hostport}"
        elif vid and pid:
            stable_id = f"{vid}_{pid}_{bus}_{addr}"
        else:
            stable_id = f"{bus}_{addr}"
        return "usbpt_" + re.sub(r"[^A-Za-z0-9_.-]", "_", stable_id)

    def _connected_usb_ids(self):
        """Set de device_ids de USB actualmente conectados a la VM.

        Usa la salida de 'info usb' vía QMP (mismo comando que ya usa
        passthrough_usb_unplug). Si el QMP falla, devuelve un set vacío
        (la UI mostrará todos los USB como disponibles, y al pulsar
        sobre uno conectado QEMU devolverá el error correspondiente).
        """
        connected = set()
        if not self.current_vm_dir:
            return connected
        try:
            vm_name = os.path.basename(self.current_vm_dir)
            if self._runtime_state(vm_name) not in ("running", "paused"):
                return connected
        except Exception:
            return connected
        try:
            result = self._qmp_command(
                self.current_vm_dir,
                {"execute": "human-monitor-command",
                 "arguments": {"command-line": "info usb"}},
            )
            text = str(result.get("return") or "")
        except Exception:
            return connected
        for m in re.finditer(r"usbpt_[A-Za-z0-9_.-]+", text):
            connected.add(m.group(0))
        return connected

    def _usb_input_class_for(self, d):
        """Devuelve 'teclado', 'ratón' o None según las interfaces del USB.

        Consulta /sys/bus/usb/devices/ buscando el dispositivo por su
        idVendor + idProduct y leyendo bInterfaceClass/bInterfaceProtocol
        de cada interfaz. Es la fuente canónica en Linux, no depende de
        lsusb ni de udevadm.

        HID (bInterfaceClass=0x03):
          • protocolo 0x01 → teclado
          • protocolo 0x02 → ratón
          • otros protocolos (0x00, tableta, gamepad, etc.) → None
        """
        vid = str(d.get("vendorid") or "").lower()
        pid = str(d.get("productid") or "").lower()
        if not (vid and pid):
            return None
        base = "/sys/bus/usb/devices"
        try:
            entries = os.listdir(base)
        except OSError:
            return None
        for entry in entries:
            if ":" in entry:
                continue  # es una interfaz, no el dispositivo
            devdir = os.path.join(base, entry)
            try:
                with open(os.path.join(devdir, "idVendor")) as f:
                    if f.read().strip().lower() != vid:
                        continue
                with open(os.path.join(devdir, "idProduct")) as f:
                    if f.read().strip().lower() != pid:
                        continue
            except OSError:
                continue
            # Encontrado: recorrer las interfaces buscando HID teclado/ratón.
            try:
                for sub in os.listdir(devdir):
                    if ":" not in sub:
                        continue
                    idir = os.path.join(devdir, sub)
                    try:
                        with open(os.path.join(idir, "bInterfaceClass")) as f:
                            cls = f.read().strip().lower()
                        with open(os.path.join(idir, "bInterfaceProtocol")) as f:
                            proto = f.read().strip().lower()
                    except OSError:
                        continue
                    if cls == "03":
                        if proto == "01":
                            return "teclado"
                        if proto == "02":
                            return "ratón"
            except OSError:
                pass
        return None

    def _warn_if_usb_input_device(self, d):
        """Avisa si `d` parece el teclado o el ratón del host.

        NO bloquea: devuelve True si el usuario acepta continuar, False si
        prefiere cancelar. Si el dispositivo no es teclado ni ratón,
        devuelve True sin mostrar nada.
        """
        kind = self._usb_input_class_for(d)
        if not kind:
            return True
        name = d.get("name", "dispositivo USB")
        resp = QMessageBox.warning(
            self, f"Posible {kind} del host",
            f"El dispositivo seleccionado parece ser un {kind} de este "
            f"equipo:\n\n"
            f"    {name}\n\n"
            f"Si se pasa a la VM, este {kind} dejará de controlar el host "
            f"hasta que se desconecte de la VM.\n\n"
            "Ten a mano la combinación Ctrl+Alt+F2 para abrir una consola "
            "de texto si algo va mal (con ella puedes matar el proceso "
            "QEMU: pkill -f qemu-system-x86_64).\n\n"
            f"¿Conectar este {kind} a la VM de todos modos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return resp == QMessageBox.StandardButton.Yes

    def _quick_usb_action(self, d, connect):
        """Conecta o desconecta `d` de la VM.

        Estrategia: refrescar el árbol de Passthrough, localizar el item
        correspondiente por clave estable, seleccionarlo, y llamar al
        método existente. Así reutilizamos TODA la lógica actual:
        permisos con pkexec, desmontaje del host, comprobación de acceso
        al nodo /dev/bus/usb, mensajes de error específicos, etc.
        """
        if not isinstance(d, dict) or d.get("kind") != "usb":
            QMessageBox.information(
                self, "USB", self.tr("Dispositivo USB inválido.")
            )
            return

        # Aviso si el dispositivo es el teclado o el ratón del host.
        if connect and not self._warn_if_usb_input_device(d):
            return

        # 1) Refrescar el árbol para tener las referencias actuales.
        try:
            self.refresh_passthrough_tree()
        except Exception:
            pass

        # 2) Localizar el item correspondiente.
        target_key = self._usb_device_key(d)
        target_item = None
        if hasattr(self, "passthrough_tree"):
            for i in range(self.passthrough_tree.topLevelItemCount()):
                it = self.passthrough_tree.topLevelItem(i)
                stored = it.data(0, Qt.ItemDataRole.UserRole) or {}
                if stored.get("kind") != "usb":
                    continue
                if self._usb_device_key(stored) == target_key:
                    target_item = it
                    break

        if target_item is None:
            QMessageBox.information(
                self, "USB",
                "No se encontró el dispositivo en la lista de Passthrough.\n\n"
                "Puede que se haya desconectado del host, o que su dirección "
                "de bus haya cambiado. Abre la pestaña Passthrough y pulsa "
                "'🔄 Detectar dispositivos' para refrescar.",
            )
            return

        # 3) Seleccionarlo y delegar en el método existente.
        try:
            self.passthrough_tree.setCurrentItem(target_item)
        except Exception:
            pass
        try:
            if connect:
                self.passthrough_usb_hotplug()
            else:
                self.passthrough_usb_unplug()
        except Exception as e:
            QMessageBox.warning(
                self, "USB",
                f"No se pudo {'conectar' if connect else 'desconectar'} el USB.\n\n{e}",
            )

    def _show_media_menu_at_cursor(self, button=None, pos_global=None):
        """Despliega el menú de Medios (CD/DVD + USB).

        Se llama desde cuatro sitios:
          • El atajo Ctrl+M (sin argumento: elige el primer botón
            disponible y habilitado).
          • El botón "💿 Medios" de la pestaña Resumen.
          • El botón "💿 Medios" de la barra superior de la Consola
            Gráfica.
          • El menú contextual de la lista de VMs (con pos_global
            apuntando al cursor; no requiere botón).

        Si el botón no está habilitado (VM apagada o sin VM), no hace
        nada.
        """
        menu = getattr(self, "menu_vm_usb", None)
        if menu is None:
            return
        # vm_context_menu_v1: si nos pasan una posición global
        # (clic derecho en la lista), la usamos directamente. Si no,
        # el comportamiento es el de siempre: calcularla desde el
        # botón.
        if pos_global is not None:
            try:
                menu.popup(pos_global)
            except Exception:
                pass
            return
        btn = button
        if btn is None:
            for attr in ("btn_vm_usb", "btn_vm_usb_console"):
                cand = getattr(self, attr, None)
                if cand is not None and cand.isEnabled():
                    btn = cand
                    break
        if btn is None or not btn.isEnabled():
            return
        try:
            from PyQt6.QtCore import QPoint
            pos = btn.mapToGlobal(QPoint(0, btn.height()))
            menu.popup(pos)
        except Exception:
            pass

    # ==================================================================
    # Menú unificado de Medios (CD/DVD + USB)
    # ==================================================================
    # Un solo menú que agrupa ambos tipos de medios extraíbles. La sección
    # CD/DVD es nueva (cambio de ISO en caliente, expulsar); la sección
    # USB reutiliza exactamente el mismo código que ya existía en
    # _refresh_usb_menu. La cabecera y el pie son comunes.

    def _media_menu_cdrom_section(self, menu):
        """Añade al menú las unidades CD/DVD con sus acciones por unidad."""
        try:
            if not self.current_vm_dir:
                cds = []
            else:
                cds = [d for d in self._storage_devices_all(self.current_vm_dir)
                       if d.get("device") == "cdrom"]
        except Exception:
            cds = []

        header = menu.addAction(self.tr("📀 Unidades ópticas"))
        header.setEnabled(False)

        if not cds:
            act = menu.addAction(self.tr("      (Sin unidades CD/DVD)"))
            act.setEnabled(False)
            return

        for idx, cd in enumerate(cds):
            name = cd.get("name") or f"CD/DVD {idx+1}"
            path = cd.get("path") or ""
            source = str(cd.get("source") or "")
            if source == "installer":
                media_label = self.tr("🌐 descargar instalador al iniciar")
            elif source == "recovery":
                media_label = self.tr("🌐 descargar Recovery al iniciar")
            elif path:
                media_label = os.path.basename(path)
            else:
                media_label = self.tr("vacío")

            sub = menu.addMenu(self.tr("   📀 {0} — {1}").format(name, media_label))

            change = sub.addAction(self.tr("📂 Cambiar medio…"))
            change.setToolTip(
                "Selecciona un ISO/IMG/DMG y cámbialo en caliente si la VM "
                "está corriendo, o guárdalo para el próximo arranque si está "
                "apagada."
            )
            change.triggered.connect(
                lambda checked=False, c=cd: self._hot_swap_cdrom(c)
            )

            eject = sub.addAction(self.tr("⏏ Expulsar medio"))
            eject.setToolTip("Expulsa el medio actual (deja la unidad vacía).")
            eject.setEnabled(bool(path))
            eject.triggered.connect(
                lambda checked=False, c=cd: self._hot_eject_cdrom(c)
            )

    def _media_menu_usb_section(self, menu):
        """Añade al menú la sección USB (misma lógica que el menú antiguo)."""
        try:
            state = self._runtime_state(os.path.basename(self.current_vm_dir))
        except Exception:
            state = "stopped"

        header = menu.addAction(self.tr("🔌 Dispositivos USB"))
        header.setEnabled(False)

        if state not in ("running", "paused"):
            act = menu.addAction(self.tr("      (La VM debe estar encendida para conectarlos)"))
            act.setEnabled(False)
            return

        try:
            usb_devices = self._detect_usb_devices()
        except Exception as e:
            act = menu.addAction(self.tr("      Error al detectar USB: {0}").format(e))
            act.setEnabled(False)
            return

        if not usb_devices:
            act = menu.addAction(self.tr("      (No hay dispositivos USB detectados)"))
            act.setEnabled(False)
            return

        connected_ids = self._connected_usb_ids()
        from PyQt6.QtGui import QAction as _QA

        for d in usb_devices:
            name = (d.get("name") or "").strip() or "(USB sin nombre)"
            device_id = self._usb_device_id(d)
            is_connected = device_id in connected_ids
            label = (("   ✓ " if is_connected else "     ") + name)

            act = _QA(label, menu)
            act.setCheckable(True)
            act.setChecked(is_connected)

            vid = str(d.get("vendorid") or "?").upper()
            pid = str(d.get("productid") or "?").upper()
            bus = str(d.get("bus") or "?")
            addr = str(d.get("addr") or "?")
            estado = (self.tr("conectado a la VM") if is_connected
                      else self.tr("disponible en el host"))
            act.setToolTip(
                self.tr(
                    "{0}\n"
                    "VID:PID = {1}:{2}\n"
                    "Bus {3} · Device {4}\n"
                    "Estado: {5}\n\n"
                    "{6}"
                ).format(
                    name, vid, pid, bus, addr, estado,
                    (self.tr("Clic para DESCONECTAR de la VM")
                     if is_connected
                     else self.tr("Clic para CONECTAR a la VM")),
                )
            )

            if is_connected:
                act.triggered.connect(
                    lambda checked=False, dev=d: self._quick_usb_action(dev, False)
                )
            else:
                act.triggered.connect(
                    lambda checked=False, dev=d: self._quick_usb_action(dev, True)
                )
            menu.addAction(act)

    def _refresh_media_menu(self):
        """Reconstruye el menú unificado de Medios antes de mostrarlo."""
        menu = getattr(self, "menu_vm_usb", None)
        if menu is None:
            return
        try:
            menu.clear()
        except Exception:
            pass

        if not self._vm_is_selected():
            act = menu.addAction(self.tr("(Selecciona una VM primero)"))
            act.setEnabled(False)
            return

        vm_name = os.path.basename(self.current_vm_dir)
        header = menu.addAction(self.tr("💿 Medios de '{0}'").format(vm_name))
        header.setEnabled(False)
        menu.addSeparator()

        # CD/DVD
        self._media_menu_cdrom_section(menu)
        menu.addSeparator()

        # USB
        self._media_menu_usb_section(menu)
        menu.addSeparator()

        # Footer
        refresh = menu.addAction(self.tr("🔄 Refrescar"))
        refresh.triggered.connect(lambda: self._refresh_media_menu())
        manage = menu.addAction(self.tr("⚙ Gestionar USB en Passthrough…"))
        manage.triggered.connect(self._goto_passthrough_tab)

    # ------------------------------------------------------------------
    # Cambio de medio CD/DVD en caliente
    # ------------------------------------------------------------------
    # Reutiliza el mismo camino que manage_cdrom(): QMP eject + change
    # para la VM encendida, o solo actualización del vm_config.ini para
    # la VM apagada. No duplicamos la lógica de actualización porque
    # _update_cdrom_device() ya la implementa.

    def _hot_swap_cdrom(self, cd):
        """Abre un QFileDialog para elegir nuevo medio y lo cambia."""
        if not isinstance(cd, dict):
            return
        iso, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar medio óptico", "",
            "Imágenes (*.iso *.img *.dmg);;Todos los archivos (*)",
        )
        if not iso:
            return
        self._cdrom_hot_change(cd, iso)

    def _hot_eject_cdrom(self, cd):
        """Expulsa el medio actual de la unidad."""
        if not isinstance(cd, dict):
            return
        self._cdrom_hot_change(cd, "")

    def _cdrom_hot_change(self, cd, new_path):
        """Cambia el medio de una unidad CD/DVD, en caliente si hace falta.

        IMPORTANTE: QEMU conoce la unidad por el id sanitizado del
        dispositivo (guardado en vm_config.ini como "id"), NO por un
        nombre secuencial tipo "cd0". Ese id es el que workers.py pasa a
        -device scsi-cd,...,id=<safe_id>. Por eso usamos
        _qemu_safe_identifier() — la misma función que workers.py — para
        obtener el nombre real que QEMU espera en eject/change.
        """
        if not self.current_vm_dir:
            return
        ident = cd.get("id")
        if not ident:
            QMessageBox.warning(
                self, "CD/DVD",
                "La unidad no tiene id interno; no se puede identificar en QEMU.",
            )
            return

        # El nombre del device tal y como lo conoce QEMU.
        from workers import _qemu_safe_identifier
        # QEMU HMP conoce la unidad por el id del -drive (cdrom_0, cdrom_1, ...),
        # no por el id del -device (dev_xxx). El índice idx debe ser el
        # mismo que usa workers.py al construir la línea de QEMU.
        try:
            _cds = [d for d in self._storage_devices_all(self.current_vm_dir)
                    if d.get("device") == "cdrom"]
            _idx = next((i for i, d in enumerate(_cds) if d.get("id") == ident), None)
        except Exception:
            _idx = None
        if _idx is None:
            QMessageBox.warning(
                self, "CD/DVD",
                "No se encontró la unidad seleccionada en la configuración.")
            return
        device_id = "cdrom_" + str(_idx)
        try:
            state = self._runtime_state(os.path.basename(self.current_vm_dir))
        except Exception:
            state = "stopped"

        try:
            if state in ("running", "paused"):
                # Comprobar que QEMU conoce el device. Si no, dar un error
                # claro en vez del críptico "Device 'X' not found".
                known = self._qmp_known_cdrom_devices()
                if known and device_id not in known:
                    # Diagnóstico: el device no está entre los que QEMU
                    # expone. Puede ser un bug de la app o que la VM se
                    # arrancó antes de añadir la unidad.
                    detail = "\n".join(f"  • {d}" for d in sorted(known))
                    QMessageBox.warning(
                        self, "CD/DVD",
                        f"QEMU no reconoce la unidad '{device_id}'.\n\n"
                        "Dispositivos de bloque que QEMU sí conoce:\n"
                        f"{detail or '  (ninguno)'}\n\n"
                        "Si acabas de añadir la unidad, cierra la VM y vuélvela "
                        "a arrancar para que QEMU la vea.",
                    )
                    return

                # 1) Expulsar lo que hubiera (no falla si está vacío).
                try:
                    self._qmp_hmp(self.current_vm_dir, f"eject -f {device_id}")
                except Exception as e:
                    # Algunos QEMU no aceptan -f; reintento sin él.
                    try:
                        self._qmp_hmp(self.current_vm_dir, f"eject {device_id}")
                    except Exception:
                        # Si falla por estar vacío, no es un error real.
                        pass

                # 2) Insertar el nuevo medio, si lo hay.
                if new_path:
                    self._qmp_hmp(
                        self.current_vm_dir,
                        f"change {device_id} \"{new_path}\"",
                    )
                    self.log_message(
                        f"==> CD/DVD {device_id}: medio cambiado a "
                        f"{os.path.basename(new_path)}."
                    )
                else:
                    self.log_message(f"==> CD/DVD {device_id}: medio expulsado.")

                self._update_cdrom_device(ident, new_path, source="")
            else:
                # VM apagada: solo actualizamos la config.
                self._update_cdrom_device(ident, new_path, source="")
                self.log_message(
                    f"==> CD/DVD configurado: {new_path or 'vacío'} "
                    "(se aplicará al arrancar la VM)."
                )

            try:
                self.refresh_storage_ui()
                self.refresh_boot_order_choices()
                self._update_manager_details()
            except Exception:
                pass

            if state in ("running", "paused"):
                QMessageBox.information(
                    self, "CD/DVD",
                    f"Medio {'cambiado a ' + os.path.basename(new_path) if new_path else 'expulsado'}."
                )
        except Exception as e:
            QMessageBox.warning(
                self, "CD/DVD",
                f"No se pudo cambiar el medio.\n\n{e}"
            )

    def _qmp_known_cdrom_devices(self):
        """Devuelve el set de device-ids de CD/DVD que QEMU conoce.

        Usa query-block para listar los dispositivos de bloque y filtra
        los que son unidades ópticas (removable=True, o drv=raw/host_cdrom).
        Los nombres devueltos son los que acepta eject/change.
        """
        known = set()
        try:
            result = self._qmp_command(
                self.current_vm_dir, {"execute": "query-block"}
            )
            rows = result.get("return") or []
        except Exception:
            return known
        for row in rows:
            ins = row.get("inserted") or {}
            device_name = str(row.get("device") or "").strip()
            removable = bool(row.get("removable", False))
            drv = str(ins.get("drv") or "").lower()
            # Consideramos CD/DVD: removable=True o con drv host_cdrom/raw
            # y sin capacidad de escritura.
            is_cd = (
                removable
                or drv in ("host_cdrom", "host_device")
                or "cd" in device_name.lower()
            )
            if device_name and is_cd:
                known.add(device_name)
        return known


    def refresh_passthrough_tree(self):
        if not hasattr(self,"passthrough_tree"): return
        saved=set()
        for d in getattr(self,"_passthrough_saved",[]):
            saved.add((d.get("kind"),d.get("address"),d.get("bus"),d.get("addr")))
        self.passthrough_tree.clear()
        all_devices=self._detect_pci_devices()+self._detect_usb_devices()
        for d in all_devices:
            if d["kind"]=="pci":
                group=d.get("iommu_group")
                group_text=(self.tr("Grupo {0}").format(group)
                            if group is not None
                            else self.tr("Sin grupo IOMMU"))
                if d.get("driver"):
                    group_text += self.tr(" • {0}").format(d.get('driver'))
                status=(d.get("status")
                        or (self.tr("✓ Listo para VFIO") if d.get("vfio_ready")
                            else self.tr("⚠ Revisar")))
            else:
                group_text=((d.get("vendorid","").upper()+":"+d.get("productid","").upper())
                            if d.get("vendorid") and d.get("productid")
                            else "USB")
                status=(self.tr("✓ Acceso OK")
                        if self._usb_access_status(d)[0]
                        else self.tr("⚠ Revisar acceso"))
            root=QTreeWidgetItem(["", "PCI" if d["kind"]=="pci" else "USB", d.get("name",d.get("address","")), group_text, status])
            root.setFlags(root.flags()|Qt.ItemFlag.ItemIsUserCheckable)
            key=(d.get("kind"),d.get("address"),d.get("bus"),d.get("addr")); checked=key in saved
            root.setCheckState(0,Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked); root.setData(0,Qt.ItemDataRole.UserRole,d)
            self.passthrough_tree.addTopLevelItem(root)
        self.refresh_vfio_diagnostics()

    def save_passthrough_selection(self):
        selected=[]
        for i in range(self.passthrough_tree.topLevelItemCount()):
            it=self.passthrough_tree.topLevelItem(i)
            if it.checkState(0)==Qt.CheckState.Checked: selected.append(it.data(0,Qt.ItemDataRole.UserRole))

        # Aviso si entre los seleccionados hay teclado/ratón del host.
        # Al arrancar la VM, esos dispositivos dejarán de controlar el
        # host. No bloqueamos: el usuario decide.
        _hid_inputs = []
        for d in selected:
            if not isinstance(d, dict) or d.get("kind") != "usb":
                continue
            _kind = self._usb_input_class_for(d)
            if _kind:
                _hid_inputs.append((_kind, d.get("name", "USB")))
        if _hid_inputs:
            _lines = "\n".join(f"  • {k}: {n}" for k, n in _hid_inputs)
            _resp = QMessageBox.warning(
                self, self.tr("Passthrough: teclado o ratón del host"),
                "Has seleccionado uno o más dispositivos que parecen ser\n"
                "el teclado o el ratón de este equipo:\n\n"
                f"{_lines}\n\n"
                "Al arrancar la VM, esos dispositivos dejarán de\n"
                "controlar este host. Si teclado y ratón comparten un\n"
                "mismo receptor USB inalámbrico, podrías quedarte sin\n"
                "control total del equipo.\n\n"
                "Ten a mano Ctrl+Alt+F2 para abrir una consola de texto\n"
                "si algo va mal.\n\n"
                "¿Guardar de todos modos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if _resp != QMessageBox.StandardButton.Yes:
                return

        self._passthrough_saved=selected
        if self.current_vm_dir:
            self._on_config_dirty()
        QMessageBox.information(self,"Passthrough",f"Se guardaron {len(selected)} dispositivos.")

    def passthrough_usb_hotplug(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, self.tr("Passthrough USB"), "Selecciona una máquina virtual."); return
        item=self.passthrough_tree.currentItem() if hasattr(self,'passthrough_tree') else None
        d=item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not isinstance(d, dict) or d.get('kind')!='usb':
            QMessageBox.information(self, self.tr("Passthrough USB"), self.tr("Selecciona un dispositivo USB.")); return
        state=self._runtime_state(os.path.basename(self.current_vm_dir))
        if state not in ('running','paused'):
            QMessageBox.information(self,self.tr("Passthrough USB"),self.tr("La VM no está encendida; usa Guardar selección para conectarlo al próximo arranque.")); return
        # Aviso si el dispositivo es el teclado o el ratón del host.
        if not self._warn_if_usb_input_device(d):
            return
        bus=str(d.get('bus') or '').strip(); addr=str(d.get('addr') or '').strip()
        vid=str(d.get('vendorid') or '').strip().lower(); pid=str(d.get('productid') or '').strip().lower()
        if not ((bus and addr) or (vid and pid)):
            QMessageBox.information(self,self.tr("Passthrough USB"),"No se pudo identificar el USB (bus/dispositivo o fabricante/producto)."); return
        # El controlador USB para hotplug se crea al arrancar la VM cuando existe un USB passthrough.
        # Como hay un único controlador XHCI, QEMU puede elegir automáticamente su bus USB.
        hostport=str(d.get('port') or '').strip()
        stable_id = f"port_{hostport}" if hostport else (f"{vid}_{pid}_{bus}_{addr}" if vid and pid else f"{bus}_{addr}")
        device_id='usbpt_' + re.sub(r'[^A-Za-z0-9_.-]','_',stable_id)
        # Con un solo controlador XHCI, QEMU asigna automáticamente el usb-host al único bus USB.
        # No usamos bus=usbpass.0 aquí: así también funciona con builds que exponen un nombre de bus distinto.
        args={"driver":"usb-host","id":device_id}
        if vid and pid:
            args.update({"vendorid":int(vid,16),"productid":int(pid,16)})
        else:
            args.update({"hostbus":int(bus),"hostaddr":int(addr)})
        try:
            self._prepare_usb_passthrough([d])
            # La preparación puede haber cambiado Bus/Device: para hotplug preferimos VID/PID,
            # y si el QEMU no aceptara VID/PID tenemos los valores actuales de respaldo.
            vid=str(d.get('vendorid') or '').strip().lower(); pid=str(d.get('productid') or '').strip().lower()
            bus=str(d.get('bus') or '').strip(); addr=str(d.get('addr') or '').strip()
            args={"driver":"usb-host","id":device_id}
            if vid and pid:
                args.update({"vendorid":int(vid,16),"productid":int(pid,16)})
            elif bus and addr:
                args.update({"hostbus":int(bus),"hostaddr":int(addr)})
            self._snapshot_log(f"[PASSTHROUGH] Preparando {d.get('name','USB')}: desmontaje/acceso USB... Nodo actual: {self._usb_device_node(d)}")
            self._qmp_command(self.current_vm_dir,{"execute":"device_add","arguments":args})
            label = f"{d.get('name','USB')}"
            self._snapshot_log(f"[PASSTHROUGH] ✓ USB conectado en caliente: {label}.")
            QMessageBox.information(
                self, self.tr("Passthrough USB"),
                self.tr(
                    "Dispositivo USB conectado en caliente a la VM.\n\n"
                    "Nota: el host debe permitir acceso a /dev/bus/usb y el "
                    "dispositivo no debería estar siendo usado por el sistema "
                    "anfitrión."
                ))
        except Exception as e:
            self._show_selectable_error(self.tr("Error al conectar USB"),f"No se pudo conectar el USB en caliente.\n\n{e}\n\nSi el error menciona que no puede abrir el dispositivo, comprueba los permisos de /dev/bus/usb o desmonta la memoria USB del anfitrión. Si menciona el bus USB, la VM debe haberse iniciado con el controlador XHCI de passthrough.")

    def passthrough_usb_unplug(self):
        if not self._vm_is_selected():
            QMessageBox.information(self, self.tr("Passthrough USB"), "Selecciona una máquina virtual."); return
        item=self.passthrough_tree.currentItem() if hasattr(self,'passthrough_tree') else None
        d=item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not isinstance(d, dict) or d.get('kind')!='usb':
            QMessageBox.information(self, self.tr("Passthrough USB"), self.tr("Selecciona un dispositivo USB.")); return
        state=self._runtime_state(os.path.basename(self.current_vm_dir))
        if state not in ('running','paused'):
            QMessageBox.information(self,self.tr("Passthrough USB"),self.tr("La VM no está encendida.")); return
        bus=str(d.get('bus') or '').strip(); addr=str(d.get('addr') or '').strip()
        vid=str(d.get('vendorid') or '').strip().lower(); pid=str(d.get('productid') or '').strip().lower()
        hostport=str(d.get('port') or '').strip()
        stable_id = f"port_{hostport}" if hostport else (f"{vid}_{pid}_{bus}_{addr}" if vid and pid else f"{bus}_{addr}")
        device_id='usbpt_' + re.sub(r'[^A-Za-z0-9_.-]','_',stable_id)
        try:
            # Evita el falso error "Device ... not found" cuando el USB nunca llegó a conectarse.
            info=self._qmp_command(self.current_vm_dir,{"execute":"human-monitor-command","arguments":{"command-line":"info usb"}})
            text=json.dumps(info, ensure_ascii=False)
            if device_id not in text:
                raise RuntimeError(f"El dispositivo {device_id} no está conectado actualmente a QEMU.")
            self._qmp_command(self.current_vm_dir,{"execute":"device_del","arguments":{"id":device_id}})
            self._snapshot_log(f"[PASSTHROUGH] USB desconectado en caliente: {d.get('name','USB')}.")
            QMessageBox.information(self,self.tr("Passthrough USB"),self.tr("Solicitud de desconexión USB enviada a QEMU."))
        except Exception as e:
            self._show_selectable_error(self.tr("Error al desconectar USB"),f"No se pudo desconectar el USB en caliente.\n\n{e}")


# i18n_tanda3_passthrough_v1a

# i18n_tanda3_passthrough_v2a

# i18n_tanda3_passthrough_v2b

# vm_config_save_cancel_v1_dirty_2b1
