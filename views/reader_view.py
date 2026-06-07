import fitz
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLabel, QPushButton, QFrame, QProgressBar
)
from PySide6.QtGui import QPixmap, QImage, QKeyEvent, QMouseEvent
from PySide6.QtCore import Qt, QTimer

from database.database_manager import DatabaseManager


class ReaderView(QMainWindow):

    def __init__(self, book):
        super().__init__()

        self.book = book
        self.book_id = book[0]
        self.file_path = book[3]
        self.book_title_str = book[1]

        self.db = DatabaseManager()

        self.doc = fitz.open(self.file_path)
        self.total_pages = len(self.doc)

        self.current_page = book[7] or 0
        self.zoom = 1.3  
        self.current_theme = "dark" 

        self.page_labels = []
        self._drag_position = None

        self.setWindowTitle(f"YuBooks Reader - {self.book_title_str}")
        self.resize(1000, 850)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setup_ui()
        self.render_pages()

        QTimer.singleShot(200, self.restore_page)

    # ================= ARRASTAR JANELA CUSTOMIZADO =================
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and event.position().y() < 50:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_position = None

    def toggle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_maximize.setText("🗖")
        else:
            self.showMaximized()
            self.btn_maximize.setText("🗗")

    # ================= UI & LAYOUT =================
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. BARRA SUPERIOR
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(15, 0, 0, 0)

        lbl_title = QLabel(self.book_title_str)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 13px;")
        toolbar_layout.addWidget(lbl_title)
        toolbar_layout.addStretch()

        # Botões do Menu com Texto e Símbolos Universais
        self.btn_zoom_out = QPushButton("   − Zoom   ")
        self.btn_zoom_in = QPushButton("   + Zoom   ")
        self.btn_light = QPushButton(" ☀️ ")
        self.btn_sepia = QPushButton(" 🗩 ")
        self.btn_dark = QPushButton(" 🌙 ")

        for btn in [self.btn_zoom_out, self.btn_zoom_in, self.btn_light, self.btn_sepia, self.btn_dark]:
            btn.setFixedHeight(32)
            btn.setStyleSheet("font-weight: bold; font-size: 12px; padding: 0 5px;")
            toolbar_layout.addWidget(btn)

        toolbar_layout.addSpacing(20)

        # Controle de Janela Nativo
        self.btn_minimize = QPushButton("─")
        self.btn_maximize = QPushButton("🗖")
        self.btn_close = QPushButton("×")

        self.btn_minimize.setObjectName("windowCtrl")
        self.btn_maximize.setObjectName("windowCtrl")
        self.btn_close.setObjectName("windowClose")

        for btn in [self.btn_minimize, self.btn_maximize, self.btn_close]:
            btn.setFixedSize(45, 50) 
            btn.setStyleSheet("font-size: 16px; font-weight: bold;")
            toolbar_layout.addWidget(btn)

        main_layout.addWidget(self.toolbar)

        # 2. ÁREA DE LEITURA
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignCenter)
        self.scroll.setFrameShape(QFrame.NoFrame) 

        self.container = QWidget()
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setSpacing(20)          
        self.vbox.setContentsMargins(0, 20, 0, 20)

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

        # 3. BARRA INFERIOR COM PROGRESSO VISUAL
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(40)
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(15, 0, 15, 0)

        self.lbl_progress = QLabel(f"Página: {self.current_page + 1} / {self.total_pages}")
        status_layout.addWidget(self.lbl_progress)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False) 
        self.progress_bar.setFixedWidth(250)
        
        status_layout.addStretch()
        status_layout.addWidget(self.progress_bar)

        main_layout.addWidget(self.status_bar)

        # ================= CONEXÕES =================
        self.scroll.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.btn_zoom_in.clicked.connect(lambda: self.change_zoom(0.15))
        self.btn_zoom_out.clicked.connect(lambda: self.change_zoom(-0.15))
        
        self.btn_light.clicked.connect(lambda: self.apply_theme("light"))
        self.btn_sepia.clicked.connect(lambda: self.apply_theme("sepia"))
        self.btn_dark.clicked.connect(lambda: self.apply_theme("dark"))

        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_maximize.clicked.connect(self.toggle_maximize_restore)
        self.btn_close.clicked.connect(self.close)

        self.apply_theme(self.current_theme)

    # ================= ESTILO DE TEMAS DINÂMICOS =================
    def apply_theme(self, theme_name):
        self.current_theme = theme_name

        if theme_name == "dark":
            bg_main, bg_panel, text_color, border_color, progress_color, hover_ctrl, scroll_thumb = "#121212", "#1e1e1e", "#ffffff", "#333333", "#d29f22", "#2d2d2d", "#3e3f41"
        elif theme_name == "sepia":
            bg_main, bg_panel, text_color, border_color, progress_color, hover_ctrl, scroll_thumb = "#f4ecd8", "#e8dcbe", "#5b4636", "#d3c29d", "#8f7355", "#dfd2b2", "#c5b799"
        else:
            bg_main, bg_panel, text_color, border_color, progress_color, hover_ctrl, scroll_thumb = "#f5f5f7", "#ffffff", "#111111", "#e5e5e7", "#d29f22", "#f0f0f2", "#cccccc"

        self.setStyleSheet(f"""
            QWidget {{ background-color: {bg_main}; color: {text_color}; font-family: 'Segoe UI', Arial, sans-serif; }}
            QFrame {{ background-color: {bg_panel}; border: none; }}
            QScrollArea {{ background-color: {bg_main}; border: none; }}
            QPushButton {{ background-color: {bg_panel}; border: 1px solid {border_color}; border-radius: 6px; padding: 5px; }}
            QPushButton:hover {{ background-color: {hover_ctrl}; border-color: {progress_color}; }}
            
            QPushButton#windowCtrl, QPushButton#windowClose {{ background-color: transparent; border: none; border-radius: 0px; font-size: 16px; font-weight: bold; }}
            QPushButton#windowCtrl:hover {{ background-color: {hover_ctrl}; }}
            QPushButton#windowClose:hover {{ background-color: #e81123; color: white; }}

            QProgressBar {{ background-color: {border_color}; border: none; border-radius: 3px; }}
            QProgressBar::chunk {{ background-color: {progress_color}; border-radius: 3px; }}

            /* 🔥 BARRA DE SCROLL DO LEITOR ADAPTÁVEL AO TEMA */
            QScrollBar:vertical {{
                background-color: {bg_main};
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {scroll_thumb};
                min-height: 40px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {progress_color}; /* Destaca com a cor principal do tema */
            }}
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        self.toolbar.setStyleSheet(f"background-color: {bg_panel}; border-bottom: 1px solid {border_color};")
        self.status_bar.setStyleSheet(f"background-color: {bg_panel}; border-top: 1px solid {border_color};")
        self.render_pages()

    # ================= RENDERIZADOR DE PDF =================
    def render_pages(self):
        for label in self.page_labels:
            self.vbox.removeWidget(label)
            label.deleteLater()
        self.page_labels.clear()

        for i in range(self.total_pages):
            page = self.doc.load_page(i)
            matrix = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)
            
            if self.current_theme == "dark":
                try:
                    pix.invert_irect(pix.irect)
                except AttributeError:
                    samples = np.frombuffer(pix.samples, dtype=np.uint8)
                    inverted_samples = 255 - samples
                    pix = fitz.Pixmap(pix.colorspace, pix.width, pix.height, inverted_samples)

            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            label = QLabel()
            label.setPixmap(QPixmap.fromImage(img))
            label.setAlignment(Qt.AlignCenter)
            
            if self.current_theme == "light":
                label.setStyleSheet("border: 1px solid #dcdcdc; background-color: white;")
            elif self.current_theme == "sepia":
                label.setStyleSheet("border: 1px solid #e3d6b6; background-color: #fdf6e3;")
            else:
                label.setStyleSheet("border: 1px solid #2d2d2d; background-color: #1c1c1c;")

            self.vbox.addWidget(label)
            self.page_labels.append(label)

    # ================= NAVEGAÇÃO =================
    def change_zoom(self, delta):
        if 0.6 <= self.zoom + delta <= 3.0:
            saved_page = self.get_current_page()
            self.zoom += delta
            self.render_pages()
            self.current_page = saved_page
            QTimer.singleShot(50, self.restore_page)

    def restore_page(self):
        if not self.page_labels or self.current_page >= len(self.page_labels): return
        label = self.page_labels[self.current_page]
        self.scroll.verticalScrollBar().setValue(label.y())
        self.update_progress_ui(self.current_page)

    def get_current_page(self):
        scroll_y = self.scroll.verticalScrollBar().value()
        current = 0
        for i, label in enumerate(self.page_labels):
            if label.y() <= scroll_y + 100: current = i
        return current

    def on_scroll(self):
        page = self.get_current_page()
        if page != self.current_page:
            self.current_page = page
            self.update_progress_ui(page)

    def update_progress_ui(self, page_index):
        pct = round(((page_index + 1) / self.total_pages) * 100) if self.total_pages else 0
        self.lbl_progress.setText(f"Página: {page_index + 1} / {self.total_pages} ({pct}%)")
        self.progress_bar.setValue(pct)

    def keyPressEvent(self, event: QKeyEvent):
        scrollbar = self.scroll.verticalScrollBar()
        step = scrollbar.singleStep() * 4
        if event.key() in (Qt.Key_Down, Qt.Key_PageDown): scrollbar.setValue(scrollbar.value() + step)
        elif event.key() in (Qt.Key_Up, Qt.Key_PageUp): scrollbar.setValue(scrollbar.value() - step)
        else: super().keyPressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0: self.change_zoom(0.1)
            else: self.change_zoom(-0.1)
            event.accept()
        else: super().wheelEvent(event)

    def closeEvent(self, event):
        page = self.get_current_page()
        self.db.update_progress(self.book_id, page, self.total_pages)
        event.accept()