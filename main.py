import sys

from PySide6.QtWidgets import QApplication

from views.library_view import LibraryView


app = QApplication(sys.argv)

window = LibraryView()
window.show()

sys.exit(app.exec())