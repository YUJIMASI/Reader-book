import fitz  # PyMuPDF

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea
)

from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt


class ReaderView(QMainWindow):

    def __init__(self, book):
        super().__init__()

        self.book = book
        self.file_path = book[3]

        self.setWindowTitle(book[1])
        self.resize(1000, 700)

        # estado do leitor
        self.doc = fitz.open(self.file_path)
        self.page_number = 0
        self.zoom = 1.5
        self.focus_mode = False

        self.setup_ui()
        self.render_page()

    # ================= UI =================
    def setup_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        central.setLayout(layout)

        # ===== TOP BAR =====
        top_bar = QHBoxLayout()

        self.btn_prev = QPushButton("⬅ Página")
        self.btn_next = QPushButton("Página ➡")
        self.btn_zoom_in = QPushButton("+ Zoom")
        self.btn_zoom_out = QPushButton("- Zoom")
        self.btn_focus = QPushButton("Foco")

        top_bar.addWidget(self.btn_prev)
        top_bar.addWidget(self.btn_next)
        top_bar.addWidget(self.btn_zoom_in)
        top_bar.addWidget(self.btn_zoom_out)
        top_bar.addWidget(self.btn_focus)

        layout.addLayout(top_bar)

        # ===== VIEWER =====
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.label)

        layout.addWidget(self.scroll)

        # ===== EVENTS =====
        self.btn_next.clicked.connect(self.next_page)
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        self.btn_focus.clicked.connect(self.toggle_focus)

    # ================= RENDER PAGE =================
    def render_page(self):

        page = self.doc.load_page(self.page_number)

        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)

        img = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format_RGB888
        )

        self.label.setPixmap(QPixmap.fromImage(img))

    # ================= PAGINATION =================
    def next_page(self):

        if self.page_number < len(self.doc) - 1:
            self.page_number += 1
            self.render_page()

    def prev_page(self):

        if self.page_number > 0:
            self.page_number -= 1
            self.render_page()

    # ================= ZOOM =================
    def zoom_in(self):
        self.zoom += 0.2
        self.render_page()

    def zoom_out(self):
        if self.zoom > 0.5:
            self.zoom -= 0.2
            self.render_page()

    # ================= FOCUS MODE =================
    def toggle_focus(self):

        self.focus_mode = not self.focus_mode

        if self.focus_mode:
            self.showFullScreen()
            self.scroll.hide()
        else:
            self.showNormal()
            self.scroll.show()