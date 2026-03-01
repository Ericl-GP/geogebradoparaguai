import sys
import math
import copy

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QInputDialog,
    QGraphicsView, QGraphicsScene,
    QGraphicsPolygonItem
)

from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF
from PySide6.QtCore import Qt, QPointF


# =========================
# PROJEÇÃO E ROTAÇÃO 3D
# =========================

def project_point(x, y, z, d):
    factor = d / (d + z) if (d + z) != 0 else 1
    return x * factor, y * factor


def rotate_point(x, y, z, ax, ay, az):
    cosx = math.cos(ax)
    sinx = math.sin(ax)
    y, z = y * cosx - z * sinx, y * sinx + z * cosx

    cosy = math.cos(ay)
    siny = math.sin(ay)
    x, z = x * cosy + z * siny, -x * siny + z * cosy

    cosz = math.cos(az)
    sinz = math.sin(az)
    x, y = x * cosz - y * sinz, x * sinz + y * cosz

    return x, y, z


# =========================
# MAIN WINDOW
# =========================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()



        self.setWindowTitle("Mini Modelador 3D - Avançado")
        self.light_direction = self.normalize((1, -1, -1))
        self.show_gizmo = True
        self.scene = QGraphicsScene(-10000, -10000, 20000, 20000)
        self.scene.setBackgroundBrush(QColor(200, 200, 200))

        self.view = GraphicsView(self)
        self.view.setScene(self.scene)

        self.groups_data = {}
        self.current_letter_index = 0

        self.ax = 0
        self.ay = 0
        self.az = 0
        self.camera_distance = 500

        main_layout = QHBoxLayout()
        side_layout = QVBoxLayout()

        self.new_figure_button = QPushButton("Nova Figura")
        self.new_figure_button.clicked.connect(self.create_new_figure)

        self.reset_camera_button = QPushButton("Reset Camera")
        self.reset_camera_button.clicked.connect(self.reset_camera)

        side_layout.addWidget(self.new_figure_button)
        side_layout.addWidget(self.reset_camera_button)

        self.groups_layout = QVBoxLayout()
        side_layout.addLayout(self.groups_layout)

        main_layout.addLayout(side_layout)
        main_layout.addWidget(self.view)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.light_ax = 0
        self.light_ay = 0


        self.update_scene()



    # =========================
    # SISTEMA DE GRUPOS
    # =========================

    def center_group(self, letter):
        pts = self.groups_data[letter]["points"]

        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        cz = sum(p[2] for p in pts) / len(pts)

        self.groups_data[letter]["points"] = [
            (x - cx, y - cy, z - cz)
            for x, y, z in pts
        ]

        self.refresh_groups_ui()
        self.update_scene()

    def draw_axes(self):
        grid_size = 1000
        step = 100

        pen_grid = QPen(QColor(220, 220, 220))
        pen_grid.setWidth(1)

        # Grade XY
        for i in range(-grid_size, grid_size + 1, step):
            # linhas verticais
            x1, y1 = project_point(i, -grid_size, 0, self.camera_distance)
            x2, y2 = project_point(i, grid_size, 0, self.camera_distance)
            self.scene.addLine(x1, -y1, x2, -y2, pen_grid)

            # linhas horizontais
            x1, y1 = project_point(-grid_size, i, 0, self.camera_distance)
            x2, y2 = project_point(grid_size, i, 0, self.camera_distance)
            self.scene.addLine(x1, -y1, x2, -y2, pen_grid)

        # Eixos principais
        axes = [
            ((-grid_size, 0, 0), (grid_size, 0, 0), QColor(255, 0, 0)),
            ((0, -grid_size, 0), (0, grid_size, 0), QColor(0, 200, 0)),
            ((0, 0, -grid_size), (0, 0, grid_size), QColor(0, 0, 255)),
        ]

        for p1, p2, color in axes:
            x1, y1, _ = rotate_point(*p1, self.ax, self.ay, self.az)
            x2, y2, _ = rotate_point(*p2, self.ax, self.ay, self.az)

            px1, py1 = project_point(x1, y1, 0, self.camera_distance)
            px2, py2 = project_point(x2, y2, 0, self.camera_distance)

            self.scene.addLine(px1, -py1, px2, -py2, QPen(color, 2))

    def update_light_direction(self):
        # Luz gira como se fosse uma esfera
        lx = math.cos(self.light_ay) * math.cos(self.light_ax)
        ly = math.sin(self.light_ax)
        lz = math.sin(self.light_ay) * math.cos(self.light_ax)

        self.light_direction = self.normalize((lx, ly, lz))

    def create_new_figure(self):
        letter = chr(65 + self.current_letter_index)
        self.current_letter_index += 1

        default_points = [
            (100, 0, 0),
            (0, 100, 0),
            (-100, 0, 0),
            (0, -100, 0)
        ]

        self.groups_data[letter] = {
            "points": copy.deepcopy(default_points),
            "original": copy.deepcopy(default_points),
            "visible": True
        }

        self.refresh_groups_ui()
        self.update_scene()

    def refresh_groups_ui(self):
        while self.groups_layout.count():
            item = self.groups_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for letter in self.groups_data:
            self.create_group_widget(letter)

    def create_group_widget(self, letter):
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        header_layout = QHBoxLayout()

        label = QLabel(f"Grupo {letter}")

        edit_btn = QPushButton("✏")
        edit_btn.clicked.connect(lambda: self.edit_group(letter))

        delete_btn = QPushButton("🗑")
        delete_btn.clicked.connect(lambda: self.delete_group(letter))

        visibility_btn = QPushButton("👁")
        visibility_btn.clicked.connect(lambda: self.toggle_group(letter))

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(lambda: self.reset_group(letter))

        transform_btn = QPushButton("Transformações")
        transform_btn.clicked.connect(lambda: self.transform_menu(letter))

        center_btn = QPushButton("🎯")
        center_btn.clicked.connect(lambda: self.center_group(letter))

        header_layout.addWidget(center_btn)

        header_layout.addWidget(label)
        header_layout.addWidget(edit_btn)
        header_layout.addWidget(delete_btn)
        header_layout.addWidget(visibility_btn)
        header_layout.addWidget(reset_btn)
        header_layout.addWidget(transform_btn)

        layout.addLayout(header_layout)

        # Lista de pontos
        for i, p in enumerate(self.groups_data[letter]["points"]):
            point_label = QLabel(f"P{i+1}: {p}")
            layout.addWidget(point_label)

        self.groups_layout.addWidget(container)

    def delete_group(self, letter):
        del self.groups_data[letter]
        self.refresh_groups_ui()
        self.update_scene()

    def toggle_group(self, letter):
        self.groups_data[letter]["visible"] = not self.groups_data[letter]["visible"]
        self.update_scene()

    def reset_group(self, letter):
        self.groups_data[letter]["points"] = copy.deepcopy(self.groups_data[letter]["original"])
        self.refresh_groups_ui()
        self.update_scene()

    # =========================
    # EDIÇÃO MANUAL
    # =========================

    def edit_group(self, letter):
        current = self.groups_data[letter]["points"]
        text = "; ".join([f"{x},{y},{z}" for x, y, z in current])

        dialog = QInputDialog(self)
        dialog.setWindowTitle(f"Editar Grupo {letter}")
        dialog.setLabelText("Formato: x,y,z ; x,y,z")
        dialog.setTextValue(text)

        if dialog.exec():
            new_text = dialog.textValue()
            new_points = []

            for item in new_text.split(";"):
                try:
                    x, y, z = map(float, item.strip().split(","))
                    new_points.append((x, y, z))
                except:
                    continue

            if len(new_points) >= 3:
                self.groups_data[letter]["points"] = new_points
                self.refresh_groups_ui()
                self.update_scene()

    # =========================
    # TRANSFORMAÇÕES
    # =========================

    def transform_menu(self, letter):
        options = [
            "Reflexão X", "Reflexão Y", "Reflexão Z",
            "Plano XY", "Plano XZ", "Plano YZ",
            "Translação",
            "Cisalhamento",
            "Rotação Origem",
            "Rotação em Ponto"
        ]

        item, ok = QInputDialog.getItem(self, "Transformação", "Escolha:", options, 0, False)

        if ok:
            if "Reflexão X" == item:
                self.reflect(letter, "x")
            elif "Reflexão Y" == item:
                self.reflect(letter, "y")
            elif "Reflexão Z" == item:
                self.reflect(letter, "z")
            elif item == "Plano XY":
                self.reflect(letter, "xy")
            elif item == "Plano XZ":
                self.reflect(letter, "xz")
            elif item == "Plano YZ":
                self.reflect(letter, "yz")
            elif item == "Translação":
                self.translate(letter)
            elif item == "Cisalhamento":
                self.shear(letter)
            elif item == "Rotação Origem":
                self.rotate_group(letter)
            elif item == "Rotação em Ponto":
                self.rotate_group(letter, custom_point=True)

    def reflect(self, letter, mode):
        pts = self.groups_data[letter]["points"]
        new_pts = []

        for x, y, z in pts:
            if mode == "x":
                new_pts.append((-x, y, z))
            elif mode == "y":
                new_pts.append((x, -y, z))
            elif mode == "z":
                new_pts.append((x, y, -z))
            elif mode == "xy":
                new_pts.append((x, y, -z))
            elif mode == "xz":
                new_pts.append((x, -y, z))
            elif mode == "yz":
                new_pts.append((-x, y, z))

        self.groups_data[letter]["points"] = new_pts
        self.refresh_groups_ui()
        self.update_scene()

    def translate(self, letter):
        dx, ok1 = QInputDialog.getDouble(self, "Translação", "dx:")
        dy, ok2 = QInputDialog.getDouble(self, "Translação", "dy:")
        dz, ok3 = QInputDialog.getDouble(self, "Translação", "dz:")

        if ok1 and ok2 and ok3:
            pts = self.groups_data[letter]["points"]
            self.groups_data[letter]["points"] = [(x+dx, y+dy, z+dz) for x,y,z in pts]
            self.refresh_groups_ui()
            self.update_scene()

    def shear(self, letter):
        shx, ok = QInputDialog.getDouble(self, "Cisalhamento", "Fator X sobre Y:")
        if ok:
            pts = self.groups_data[letter]["points"]
            self.groups_data[letter]["points"] = [(x + shx*y, y, z) for x,y,z in pts]
            self.refresh_groups_ui()
            self.update_scene()

    def rotate_group(self, letter, custom_point=False):
        angle, ok = QInputDialog.getDouble(self, "Rotação", "Ângulo (graus):")
        if not ok:
            return

        angle = math.radians(angle)

        cx, cy, cz = 0,0,0

        if custom_point:
            cx, ok1 = QInputDialog.getDouble(self, "Centro", "cx:")
            cy, ok2 = QInputDialog.getDouble(self, "Centro", "cy:")
            cz, ok3 = QInputDialog.getDouble(self, "Centro", "cz:")
            if not (ok1 and ok2 and ok3):
                return

        new_pts = []
        for x,y,z in self.groups_data[letter]["points"]:
            x -= cx
            y -= cy

            xr = x*math.cos(angle) - y*math.sin(angle)
            yr = x*math.sin(angle) + y*math.cos(angle)

            new_pts.append((xr+cx, yr+cy, z))

        self.groups_data[letter]["points"] = new_pts
        self.refresh_groups_ui()
        self.update_scene()

    # =========================
    # RENDER
    # =========================

    def reset_camera(self):
        self.ax = self.ay = self.az = 0
        self.camera_distance = 500
        self.update_scene()

    def update_scene(self):
        self.scene.clear()

        faces = []

        for letter, data in self.groups_data.items():
            if not data["visible"]:
                continue
            if len(data["points"]) < 3:
                continue

            base_color = QColor.fromHsv(hash(letter) % 360, 255, 200)

            rotated_3d = []
            projected = []

            for x, y, z in data["points"]:
                x, y, z = rotate_point(x, y, z, self.ax, self.ay, self.az)
                rotated_3d.append((x, y, z))

                px, py = project_point(x, y, z, self.camera_distance)
                projected.append((px, py, z))

            polygon = QPolygonF([QPointF(px, -py) for px, py, _ in projected])
            avg_z = sum(p[2] for p in projected) / len(projected)

            faces.append((avg_z, polygon, base_color))

        faces.sort(key=lambda x: x[0], reverse=True)

        for _, polygon, color in faces:
            item = QGraphicsPolygonItem(polygon)
            item.setBrush(QBrush(color))
            item.setPen(QPen(Qt.black, 1))
            self.scene.addItem(item)

        self.draw_axes()
        if self.show_gizmo:
            self.draw_orientation_gizmo()

    def draw_orientation_gizmo(self):
        size = 60
        offset_x = -350
        offset_y = -250

        axes = [
            (size, 0, 0, QColor(255, 0, 0), "X"),
            (0, size, 0, QColor(0, 200, 0), "Y"),
            (0, 0, size, QColor(0, 0, 255), "Z"),
        ]

        for x, y, z, color, label in axes:
            x, y, z = rotate_point(x, y, z, self.ax, self.ay, self.az)
            px, py = project_point(x, y, z, 300)

            self.scene.addLine(
                offset_x, offset_y,
                offset_x + px * 0.4,
                offset_y - py * 0.4,
                QPen(color, 3)
            )

            text = self.scene.addText(label)
            text.setDefaultTextColor(color)
            text.setPos(
                offset_x + px * 0.45,
                offset_y - py * 0.45
            )

    def normalize(self, v):
        length = math.sqrt(sum(i*i for i in v))
        if length == 0:
            return (0,0,0)
        return tuple(i/length for i in v)

    def dot(self, v1, v2):
        return sum(a*b for a,b in zip(v1,v2))

class GraphicsView(QGraphicsView):
    def __init__(self, parent):
        super().__init__(parent.scene)
        self.parent = parent
        self.last_mouse_pos = None
        self.dragging_camera = False
        self.dragging_light = False

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        zoom_factor = 0.9 if delta > 0 else 1.1
        self.parent.camera_distance *= zoom_factor
        self.parent.camera_distance = max(50, min(2000, self.parent.camera_distance))
        self.parent.update_scene()

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.position()

        if event.buttons() & Qt.LeftButton:
            self.dragging_camera = True

        if event.buttons() & Qt.RightButton:
            self.dragging_light = True

    def mouseReleaseEvent(self, event):
        self.dragging_camera = False
        self.dragging_light = False
        self.last_mouse_pos = None

    def mouseMoveEvent(self, event):
        if not self.last_mouse_pos:
            return

        current_pos = event.position()
        dx = current_pos.x() - self.last_mouse_pos.x()
        dy = current_pos.y() - self.last_mouse_pos.y()

        # 🔵 Controle da câmera
        if self.dragging_camera:
            self.parent.ay += dx * 0.01
            self.parent.ax += dy * 0.01

        # 🔴 Controle da luz
        if self.dragging_light:
            self.parent.light_ay += dx * 0.01
            self.parent.light_ax += dy * 0.01
            self.parent.update_light_direction()

        self.parent.update_scene()
        self.last_mouse_pos = current_pos


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())