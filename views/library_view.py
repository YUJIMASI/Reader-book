import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QMouseEvent, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QListWidget, QPushButton, QFileDialog, QFrame, QProgressBar
)

from database.database_manager import DatabaseManager
from utils.cover_generator import generate_pdf_cover
from views.reader_view import ReaderView

# Importa o ficheiro compilado de recursos locais
import resources_rc


class LibraryView(QMainWindow):

    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()
        self.selected_book = None
        self.current_filter = "all" 
        self._drag_position = None

        self.setWindowTitle("YuBooks")
        self.resize(1200, 750)
         
        # Remove a barra padrão do Windows
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setup_ui()

        # ================= CONEXÕES DOS SINAIS =================
        self.btn_all.clicked.connect(lambda: self.load_books("all"))
        self.btn_reading.clicked.connect(lambda: self.load_books("reading"))
        self.btn_finished.clicked.connect(lambda: self.load_books("finished"))
        self.btn_unread.clicked.connect(lambda: self.load_books("unread"))
        self.btn_favorites.clicked.connect(lambda: self.load_books("favorite"))
        
        self.btn_import.clicked.connect(self.import_book)
        self.book_list.itemClicked.connect(self.show_book_details)
        self.btn_continue.clicked.connect(self.open_reader)
        self.btn_fav.clicked.connect(self.toggle_favorite)
        self.btn_delete.clicked.connect(self.delete_book)

        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_maximize.clicked.connect(self.toggle_maximize_restore)
        self.btn_close.clicked.connect(self.close)

        self.load_books("all")

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
            self.btn_maximize.setIcon(QIcon(":/assets/icons/maximize.png"))
        else:
            self.showMaximized()
            self.btn_maximize.setIcon(QIcon(":/assets/icons/restore.png"))

    # ================= UI & LAYOUT =================
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # 1. BARRA SUPERIOR CUSTOMIZADA
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(50)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(15, 0, 0, 0)

        lbl_app_title = QLabel("YuBooks — Biblioteca")
        lbl_app_title.setStyleSheet("font-weight: bold; color: #d29f22; font-size: 14px;")
        top_layout.addWidget(lbl_app_title)
        top_layout.addStretch()

        # Botões de Controle Nativos com os teus Ícones Locais
        self.btn_minimize = QPushButton()
        self.btn_minimize.setIcon(QIcon(":/assets/icons/minimize.png"))
        self.btn_maximize = QPushButton()
        self.btn_maximize.setIcon(QIcon(":/assets/icons/maximize.png"))
        self.btn_close = QPushButton()
        self.btn_close.setIcon(QIcon(":/assets/icons/close.png"))

        self.btn_minimize.setObjectName("windowCtrl")
        self.btn_maximize.setObjectName("windowCtrl")
        self.btn_close.setObjectName("windowClose")

        for btn in [self.btn_minimize, self.btn_maximize, self.btn_close]:
            btn.setFixedSize(45, 50)
            top_layout.addWidget(btn)

        outer_layout.addWidget(self.top_bar)

        main_content = QHBoxLayout()
        main_content.setContentsMargins(15, 15, 15, 15)
        main_content.setSpacing(15)

        # ---------------- SIDEBAR ----------------
        sidebar = QVBoxLayout()
        sidebar.setSpacing(8)

        self.btn_all = QPushButton("  Todos")
        self.btn_all.setIcon(QIcon(":/assets/icons/book_all.png"))
        self.btn_reading = QPushButton("  Lendo")
        self.btn_reading.setIcon(QIcon(":/assets/icons/book_reading.png"))
        self.btn_finished = QPushButton("  Lidos")
        self.btn_finished.setIcon(QIcon(":/assets/icons/book_finished.png"))
        self.btn_unread = QPushButton("  Não lidos")
        self.btn_unread.setIcon(QIcon(":/assets/icons/bookmark.png"))
        self.btn_favorites = QPushButton("  Favoritos")
        self.btn_favorites.setIcon(QIcon(":/assets/icons/heart.png"))
        self.btn_import = QPushButton("  Importar Livro")
        self.btn_import.setIcon(QIcon(":/assets/icons/import.png"))

        for btn in [self.btn_all, self.btn_reading, self.btn_finished, self.btn_unread, self.btn_favorites, self.btn_import]:
            btn.setStyleSheet("text-align: left; padding: 10px; font-size: 13px;")
            sidebar.addWidget(btn)

        self.btn_import.setStyleSheet("background-color: #d29f22; color: black; font-weight: bold; text-align: left; padding: 10px; font-size: 13px;")

        sidebar.addSpacing(15)
        self.book_list = QListWidget()
        sidebar.addWidget(self.book_list)

        left_widget = QWidget()
        left_widget.setLayout(sidebar)
        left_widget.setMaximumWidth(280)
        main_content.addWidget(left_widget)

        # ---------------- DETALHES ----------------
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        self.book_cover = QLabel() 
        self.book_cover.setFixedSize(180, 260)
        self.book_cover.setAlignment(Qt.AlignCenter)

        self.book_title = QLabel("Nenhum livro selecionado")
        self.book_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #d29f22;")

        self.book_info = QLabel("")
        self.book_info.setStyleSheet("color: #ccc; font-size: 13px; line-height: 1.5;")

        self.lbl_pct = QLabel("Progresso: 0%")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        # Botões de Ação Dinâmicos
        self.btn_continue = QPushButton("  Começar leitura")
        self.btn_continue.setIcon(QIcon(":/assets/icons/play.png"))
        self.btn_fav = QPushButton("  Favorito")
        self.btn_fav.setIcon(QIcon(":/assets/icons/star_empty.png"))
        self.btn_delete = QPushButton("  Apagar")
        self.btn_delete.setIcon(QIcon(":/assets/icons/trash.png"))

        self.btn_continue.setStyleSheet("background:#d29f22; color:black; font-weight: bold; font-size: 13px; padding: 10px;")
        self.btn_delete.setStyleSheet("background:#5d0018; color:white; font-size: 13px; padding: 10px;")

        right_panel.addWidget(self.book_cover)
        right_panel.addWidget(self.book_title)
        right_panel.addWidget(self.book_info)
        right_panel.addWidget(self.lbl_pct)
        right_panel.addWidget(self.progress_bar)
        right_panel.addWidget(self.btn_continue)
        right_panel.addWidget(self.btn_fav)
        right_panel.addWidget(self.btn_delete)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        main_content.addWidget(right_widget)

        outer_layout.addLayout(main_content)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #19171b; }
            QWidget { background-color: #19171b; color: #ffffff; font-family: 'Segoe UI', Arial; }
            QFrame { background-color: #252628; border: none; }
            QListWidget { background-color: #252628; border: none; padding: 8px; border-radius: 10px; }
            QListWidget::item { padding: 12px; margin: 4px; background-color: #19171b; border-radius: 8px; }
            QListWidget::item:selected { background-color: #d29f22; color: black; font-weight: bold; }
            QPushButton { background-color: #252628; border: 1px solid #3e3f41; padding: 10px; border-radius: 8px; color: white; }
            QPushButton:hover { background-color: #323336; border-color: #d29f22; }
            
            QPushButton#windowCtrl, QPushButton#windowClose { background-color: transparent; border: none; border-radius: 0px; }
            QPushButton#windowCtrl:hover { background-color: #2d2d2d; }
            QPushButton#windowClose:hover { background-color: #e81123; color: white; }

            QProgressBar { background-color: #252628; border: none; border-radius: 3px; }
            QProgressBar::chunk { background-color: #d29f22; border-radius: 3px; }

            /* Barra de Scroll Customizada */
            QScrollBar:vertical {
                background-color: #19171b;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e3f41;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #d29f22;
            }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.top_bar.setStyleSheet("background-color: #252628; border-bottom: 1px solid #333333;")

    def load_books(self, filter_type=None):
        if filter_type: self.current_filter = filter_type
        self.book_list.clear()
        books = self.db.get_books_by_filter(self.current_filter)
        for book in books: self.book_list.addItem(book[1])

    def show_book_details(self, item):
        title = item.text()
        book = self.db.get_book_by_title(title)
        if not book: return
        self.selected_book = book

        if book[5] and os.path.exists(book[5]): pixmap = QPixmap(book[5])
        else: pixmap = QPixmap("assets/covers/default.png")

        self.book_cover.setPixmap(pixmap.scaled(180, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.book_title.setText(book[1])
        status_pt = {"unread": "Não lido", "reading": "Lendo", "finished": "Lido"}
        self.book_info.setText(f"Autor: {book[2]}\nFormato: {book[4]}\nEstado: {status_pt.get(book[9], book[9])}")
        
        self.lbl_pct.setText(f"Progresso de Leitura: {book[8]}%")
        self.progress_bar.setValue(book[8])

        if book[7] > 0:
            self.btn_continue.setText("  Continuar leitura")
        else:
            self.btn_continue.setText("  Começar leitura")

        if book[10] == 1:
            self.btn_fav.setText("  Favoritado ✔")
            self.btn_fav.setIcon(QIcon(":/assets/icons/star_filled.png"))
            self.btn_fav.setStyleSheet("color: #d29f22; font-weight: bold; padding: 10px;")
        else:
            self.btn_fav.setText("  Favorito")
            self.btn_fav.setIcon(QIcon(":/assets/icons/star_empty.png"))
            self.btn_fav.setStyleSheet("color: white; padding: 10px;")

    def toggle_favorite(self):
        if not self.selected_book: return
        self.db.toggle_favorite(self.selected_book[0])
        self.load_books(self.current_filter)
        updated_book = self.db.get_book_by_title(self.selected_book[1])
        if updated_book: self.show_book_details(self.book_list.currentItem())

    def delete_book(self):
        if not self.selected_book: return
        self.db.cursor.execute("DELETE FROM books WHERE id = ?", (self.selected_book[0],))
        self.db.connection.commit()
        self.selected_book = None
        self.book_title.setText("Nenhum livro selecionado")
        self.book_info.setText("")
        self.progress_bar.setValue(0)
        self.lbl_pct.setText("Progresso: 0%")
        self.book_cover.clear()
        self.load_books(self.current_filter)

    def import_book(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Livro", "", "Livros (*.pdf *.epub)")
        if not file_path: return
        file_name = os.path.basename(file_path)
        title = os.path.splitext(file_name)[0]
        extension = os.path.splitext(file_name)[1].upper()
        cover_path = None
        if extension == ".PDF":
            cover_path = os.path.join("assets", "covers", f"{title}.png")
            os.makedirs(os.path.dirname(cover_path), exist_ok=True)
            generate_pdf_cover(file_path, cover_path)
        self.db.add_book(title=title, author="Desconhecido", file_path=file_path, file_type=extension, cover_path=cover_path)
        self.load_books(self.current_filter)

    def open_reader(self):
        if not self.selected_book: return
        try:
            updated_book = self.db.get_book_by_title(self.selected_book[1])
            self.reader = ReaderView(updated_book)
            self.reader.setAttribute(Qt.WA_DeleteOnClose, False)
            self.reader.destroyed.connect(lambda: self.load_books(self.current_filter))
            self.reader.show()
        except Exception as e:
            import traceback
            traceback.print_exc()