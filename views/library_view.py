from utils.cover_generator import generate_pdf_cover
from views.reader_view import ReaderView
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QFileDialog
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from database.database_manager import DatabaseManager
import os


class LibraryView(QMainWindow):

    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()

        self.setWindowTitle("YuBooks")
        self.resize(1200, 700)

        self.selected_book = None

        self.setup_ui()

        self.btn_import.clicked.connect(self.import_book)
        self.book_list.itemClicked.connect(self.show_book_details)
        self.action_button.clicked.connect(self.open_reader)

        self.load_books()

    # ================= UI =================
    def setup_ui(self):

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        sidebar = QVBoxLayout()

        title = QLabel("YuBooks")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #3E3024;
            padding: 10px;
        """)

        sidebar.addWidget(title)

        self.btn_all = QPushButton("Todos")
        self.btn_reading = QPushButton("Lendo")
        self.btn_finished = QPushButton("Lidos")
        self.btn_unread = QPushButton("Não lidos")
        self.btn_favorites = QPushButton("Favoritos")
        self.btn_import = QPushButton("Importar Livro")

        sidebar.addWidget(self.btn_all)
        sidebar.addWidget(self.btn_reading)
        sidebar.addWidget(self.btn_finished)
        sidebar.addWidget(self.btn_unread)
        sidebar.addWidget(self.btn_favorites)
        sidebar.addWidget(self.btn_import)

        sidebar.addSpacing(20)

        self.book_list = QListWidget()
        sidebar.addWidget(self.book_list)

        left_widget = QWidget()
        left_widget.setLayout(sidebar)
        left_widget.setMaximumWidth(300)

        # RIGHT PANEL
        right_panel = QVBoxLayout()

        self.book_cover = QLabel()
        self.book_cover.setAlignment(Qt.AlignCenter)
        self.book_cover.setStyleSheet("""
            border: 1px solid #D4B06A;
            border-radius: 10px;
            background-color: #FFFCF8;
            min-height: 200px;
            max-height: 300px;
        """)

        self.book_title = QLabel("Nenhum livro selecionado")
        self.book_title.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #3E3024;
        """)

        self.book_info = QLabel(
            "Selecione um livro para visualizar as informações."
        )

        self.action_button = QPushButton("Começar Leitura")

        right_panel.addWidget(self.book_cover)
        right_panel.addWidget(self.book_title)
        right_panel.addWidget(self.book_info)
        right_panel.addStretch()
        right_panel.addWidget(self.action_button)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

    # ================= IMPORT =================
    def import_book(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Livro",
            "",
            "Livros (*.pdf *.epub)"
        )

        if not file_path:
            return

        file_name = os.path.basename(file_path)

        title = os.path.splitext(file_name)[0]

        extension = os.path.splitext(file_name)[1].upper()

        cover_path = None

        if extension == ".PDF":

            cover_filename = f"{title}.png"

            cover_path = os.path.join(
                "assets",
                "covers",
                cover_filename
            )

            generate_pdf_cover(file_path, cover_path)

        self.db.add_book(
            title=title,
            author="Desconhecido",
            file_path=file_path,
            file_type=extension,
            cover_path=cover_path
        )

        self.load_books()

    # ================= LOAD =================
    def load_books(self):

        self.book_list.clear()

        books = self.db.get_books()

        for book in books:
            self.book_list.addItem(book[1])

    # ================= DETAILS =================
    def show_book_details(self, item):

        title = item.text()

        book = self.db.get_book_by_title(title)

        if not book:
            return

        self.selected_book = book

        self.set_cover(book[5])

        self.book_title.setText(book[1])

        status_map = {
            "unread": "Não lido",
            "reading": "A ler",
            "finished": "Concluído"
        }

        status = status_map.get(book[9], "Não lido")

        self.book_info.setText(f"""
Autor: {book[2]}
Formato: {book[4]}
Estado: {status}
Progresso: {book[8]}%
""")
        
    # ================= COVER =================
    def set_cover(self, cover_path):

        if cover_path and os.path.exists(cover_path):

            pixmap = QPixmap(cover_path)

        else:

            pixmap = QPixmap("assets/covers/default.png")

        self.book_cover.setPixmap(
            pixmap.scaled(
                180,
                240,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    # ================= READER =================
    def open_reader(self):

        if not self.selected_book:
            return

        self.reader = ReaderView(self.selected_book)
        self.reader.show()
