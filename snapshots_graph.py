# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Jimmy Verduga

"""snapshots_graph.py — Widget de organigrama para snapshots.

Renderiza el árbol de snapshots como un organigrama con QGraphicsView.
Cada nodo muestra: miniatura, nombre, fecha. Las conexiones padre-hijo
se dibujan como líneas. Soporta:
  • Zoom con Ctrl+rueda.
  • Pan arrastrando con botón izquierdo en zona vacía.
  • Click en nodo → selección.
  • Doble click → restaurar.
  • Menú contextual → restaurar, renombrar, eliminar, cambiar padre.
"""
import os

from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPixmap, QFont,
    QPainterPath, QAction,
)
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsProxyWidget,
    QGraphicsPathItem, QMenu, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QMessageBox,
)


ROOT_NODE_HEIGHT = 60
NODE_WIDTH = 220
NODE_HEIGHT = 190
H_SPACING = 30
V_SPACING = 20


class SnapshotNode(QGraphicsProxyWidget):
    """Nodo del organigrama: miniatura + nombre + fecha + botones."""
    # Señales para que la escena las propague.
    # (No podemos emitir señales desde un QGraphicsItem no-QObject, pero
    # QGraphicsProxyWidget SÍ es QObject, así que podemos usarlas.)

    request_restore = pyqtSignal(str)      # tag
    request_delete = pyqtSignal(str)       # tag
    request_rename = pyqtSignal(str)       # tag
    request_set_parent = pyqtSignal(str)   # tag
    request_clear_parent = pyqtSignal(str) # tag
    request_create_child = pyqtSignal(str) # tag
    selection_changed = pyqtSignal(str)    # tag

    def __init__(self, tag, snapshot_info, screenshot_path=None):
        super().__init__()
        self.tag = tag
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        # Widget interno con toda la info.
        self._w = QWidget()
        self._w.setFixedSize(NODE_WIDTH, NODE_HEIGHT)
        self._w.setStyleSheet(
            "QWidget#snapNode { background: #1e1e1e; border: 2px solid #3a3a3a;"
            " border-radius: 8px; }"
            " QWidget#snapNode[selected='true'] { border-color: #2e6fd6; }"
        )
        self._w.setObjectName("snapNode")
        # Evita que los tooltips aparezcan mal posicionados
        # dentro de un QGraphicsView.
        self._w.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
        lay = QVBoxLayout(self._w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        # Miniatura.
        thumb = QLabel()
        thumb.setFixedHeight(120)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet(
            "background: #0a0a0a; border: 1px solid #333; border-radius: 4px;"
        )
        if screenshot_path and os.path.isfile(screenshot_path):
            pix = QPixmap(screenshot_path)
            if not pix.isNull():
                thumb.setPixmap(pix.scaled(
                    200, 116,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        else:
            thumb.setText(self.tr("(sin miniatura)"))
            thumb.setStyleSheet(
                thumb.styleSheet() + " color: #666;"
            )
        lay.addWidget(thumb)

        # Nombre.
        name = QLabel(snapshot_info.get("tag", tag))
        name.setWordWrap(False)
        name.setStyleSheet(
            "color: #eee; font-weight: bold; font-size: 11px;"
        )
        name.setToolTip(snapshot_info.get("tag", tag))
        lay.addWidget(name)

        # Fecha + tamaño VM.
        date_txt = snapshot_info.get("date", "")
        size_txt = snapshot_info.get("vm_size", "")
        info = QLabel(f"{date_txt}  ·  {size_txt}" if size_txt else date_txt)
        info.setStyleSheet("color: #999; font-size: 10px;")
        lay.addWidget(info)

        # Botones compactos.
        btns = QHBoxLayout()
        btns.setSpacing(4)
        for label, tip, sig in (
            ("↩", self.tr("Restaurar este snapshot"), self.request_restore),
            ("✏", self.tr("Renombrar"), self.request_rename),
            ("🗑", self.tr("Eliminar"), self.request_delete),
        ):
            b = QPushButton(label)
            b.setFixedSize(28, 22)
            b.setToolTip(tip)
            b.setStyleSheet(
                "QPushButton { background: #2a2a2a; color: #ddd;"
                " border: 1px solid #444; border-radius: 4px; }"
                " QPushButton:hover { background: #3a3a3a; }"
            )
            b.clicked.connect(lambda _, s=sig: s.emit(self.tag))
            btns.addWidget(b)
        btns.addStretch()
        lay.addLayout(btns)

        self.setWidget(self._w)

    def mouseDoubleClickEvent(self, event):
        self.request_restore.emit(self.tag)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        a_restore = menu.addAction(self.tr("↩ Restaurar"))
        a_rename = menu.addAction(self.tr("✏ Renombrar"))
        a_delete = menu.addAction(self.tr("🗑 Eliminar"))
        menu.addSeparator()
        a_child = menu.addAction(self.tr("➕ Crear snapshot hijo"))
        a_set_parent = menu.addAction(self.tr("🔗 Establecer padre…"))
        a_clear = menu.addAction(self.tr("⬆ Mover a la raíz"))
        chosen = menu.exec(event.screenPos())
        if chosen == a_restore:
            self.request_restore.emit(self.tag)
        elif chosen == a_rename:
            self.request_rename.emit(self.tag)
        elif chosen == a_delete:
            self.request_delete.emit(self.tag)
        elif chosen == a_child:
            self.request_create_child.emit(self.tag)
        elif chosen == a_set_parent:
            self.request_set_parent.emit(self.tag)
        elif chosen == a_clear:
            self.request_clear_parent.emit(self.tag)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            # Actualizar estilo visual según selección.
            self._w.setProperty("selected", "true" if value else "false")
            self._w.setStyleSheet(self._w.styleSheet())  # forzar refresco
            if value:
                self.selection_changed.emit(self.tag)
        return super().itemChange(change, value)


class SnapshotsGraphView(QGraphicsView):
    """QGraphicsView con zoom y pan para el organigrama.

    Reenvía las señales de los nodos (restore/delete/rename/etc.)
    como una única señal `node_action(action, tag)` para que el
    mixin las pueda conectar sin conocer cada nodo individual.
    """
    # (action, tag) — action ∈ restore|delete|rename|set_parent|
    #                          clear_parent|create_child
    node_action = pyqtSignal(str, str)
    selection_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor("#101010")))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._zoom = 1.0
        self._nodes_by_tag = {}
        self._edges = []

    # --------------------------------------------------------------- zoom

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 1/1.15
            new_zoom = self._zoom * factor
            if 0.2 <= new_zoom <= 3.0:
                self._zoom = new_zoom
                self.scale(factor, factor)
            event.accept()
            return
        super().wheelEvent(event)

    def reset_zoom(self):
        self.resetTransform()
        self._zoom = 1.0

    def fit_all(self):
        rect = self._scene.itemsBoundingRect()
        if rect.isNull() or rect.isEmpty():
            return
        margin = 40
        rect = rect.adjusted(-margin, -margin, margin, margin)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = self.transform().m11()

    # ------------------------------------------------------------- rebuild

    def rebuild(self, snapshots_list, edges, screenshot_dir, root_label="VM original"):
        """Reconstruye el organigrama completo.

        snapshots_list: lista de dicts con keys: tag, date, vm_size.
        edges: dict {tag: [hijos...]} para los hijos de cada nodo.
               Los snapshots sin padre se agrupan bajo root_label.
        screenshot_dir: carpeta con los PNG.
        """
        self._scene.clear()
        self._nodes_by_tag.clear()
        self._edges.clear()

        # Calcular posiciones usando layout Reingold-Tilford simple.
        positions = self._layout(edges, root_label)

        # Nodo raíz virtual (VM original).
        root_node = self._make_root_node(root_label)
        self._scene.addItem(root_node)
        rx, ry = positions.get(root_label, (0.0, 0.0))
        root_node.setPos(rx, ry)

        # Nodos de snapshot.
        for snap in snapshots_list:
            tag = snap["tag"]
            shot = os.path.join(screenshot_dir, f"{tag}.png") if screenshot_dir else None
            node = SnapshotNode(tag, snap, screenshot_path=shot)
            self._scene.addItem(node)
            self._connect_node(node)
            x, y = positions.get(tag, (0.0, 0.0))
            node.setPos(x, y)
            self._nodes_by_tag[tag] = node

        # Aristas (líneas).
        for parent, children in edges.items():
            parent_pos = positions.get(parent)
            if parent_pos is None:
                continue
            parent_h = (ROOT_NODE_HEIGHT if parent == root_label
                        else NODE_HEIGHT)
            for child in children:
                child_pos = positions.get(child)
                if child_pos is None:
                    continue
                self._add_edge(parent_pos, child_pos, parent_h)

        # Extender el scene rect para que el scroll funcione.
        rect = self._scene.itemsBoundingRect()
        rect = rect.adjusted(-100, -100, 100, 100)
        self._scene.setSceneRect(rect)

    def _connect_node(self, node):
        """Conecta las señales de un SnapshotNode con las de la escena.

        Se llama desde rebuild() por cada nodo creado. Los botones del
        nodo emiten sus propias señales, y aquí las reenviamos como
        node_action(action, tag) para que el mixin pueda manejarlas.
        """
        node.request_restore.connect(
            lambda tag: self.node_action.emit("restore", tag))
        node.request_delete.connect(
            lambda tag: self.node_action.emit("delete", tag))
        node.request_rename.connect(
            lambda tag: self.node_action.emit("rename", tag))
        node.request_set_parent.connect(
            lambda tag: self.node_action.emit("set_parent", tag))
        node.request_clear_parent.connect(
            lambda tag: self.node_action.emit("clear_parent", tag))
        node.request_create_child.connect(
            lambda tag: self.node_action.emit("create_child", tag))
        node.selection_changed.connect(self.selection_changed.emit)

    def _make_root_node(self, label):
        w = QWidget()
        w.setFixedSize(NODE_WIDTH, 60)
        w.setStyleSheet(
            "background: #14233a; border: 2px dashed #3a6a9a;"
            " border-radius: 8px;"
        )
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10)
        lbl = QLabel(f"🖥️ {label}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #aaccee; font-weight: bold; font-size: 12px;")
        lay.addWidget(lbl)
        proxy = QGraphicsProxyWidget()
        proxy.setWidget(w)
        proxy.setZValue(-1)
        return proxy

    def _add_edge(self, parent_pos, child_pos, parent_height=None):
        """Dibuja una línea del padre al hijo.

        parent_height: altura REAL del nodo padre (60 root, 190 normal).
        Antes se usaba NODE_HEIGHT siempre, lo que dejaba un hueco visual
        entre la raíz y la línea.
        """
        if parent_height is None:
            parent_height = NODE_HEIGHT
        px = parent_pos[0] + NODE_WIDTH / 2
        py = parent_pos[1] + parent_height
        cx = child_pos[0] + NODE_WIDTH / 2
        cy = child_pos[1]

        path = QPainterPath(QPointF(px, py))
        mid_y = (py + cy) / 2
        path.cubicTo(
            QPointF(px, mid_y),
            QPointF(cx, mid_y),
            QPointF(cx, cy),
        )
        item = QGraphicsPathItem(path)
        pen = QPen(QColor("#4a6a8a"), 2)
        item.setPen(pen)
        item.setZValue(-2)
        self._scene.addItem(item)
        self._edges.append(item)


    def _layout(self, edges, root_label):
        """Layout Reingold-Tilford simplificado.

        Devuelve {tag: (x, y)} con x acumulando columnas y y = profundidad
        por nivel. Los padres se centran sobre sus hijos.
        """
        positions = {}
        col = [0]

        def dfs(node, depth):
            children = edges.get(node, [])
            if not children:
                x = col[0] * (NODE_WIDTH + H_SPACING)
                col[0] += 1
            else:
                child_xs = []
                for c in children:
                    dfs(c, depth + 1)
                    child_xs.append(positions[c][0])
                x = sum(child_xs) / len(child_xs)
            if depth == 0:
                y = 0
            elif depth == 1:
                y = ROOT_NODE_HEIGHT + V_SPACING
            else:
                y = ROOT_NODE_HEIGHT + V_SPACING
                for _ in range(depth - 1):
                    y += NODE_HEIGHT + V_SPACING
            positions[node] = (x, y)

        # El root_label es la raíz del árbol. Todas las claves del dict
        # edges sin padre son hijas del root. Si root_label ya está en
        # edges como clave, usar directamente.
        if root_label in edges:
            dfs(root_label, 0)
        else:
            dfs(root_label, 0)
        return positions

# i18n_tanda2f_snapshots_graph_v1

# i18n_tanda2f2_snapshots_graph_v1
