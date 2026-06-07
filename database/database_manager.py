import sqlite3
from pathlib import Path


class DatabaseManager:

    def __init__(self):
        self.db_path = Path("database/books.db")
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

        self.create_tables()

    def create_tables(self):

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                cover_path TEXT,

                total_pages INTEGER DEFAULT 0,
                current_page INTEGER DEFAULT 0,

                progress REAL DEFAULT 0,

                status TEXT DEFAULT 'unread',

                favorite INTEGER DEFAULT 0,

                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_opened TIMESTAMP
            )
        """)

        self.connection.commit()

    def add_book(
        self,
        title,
        author,
        file_path,
        file_type,
        cover_path=None
    ):

       self.cursor.execute("""
        INSERT INTO books (
            title,
            author,
            file_path,
            file_type,
            cover_path
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        title,
        author,
        file_path,
        file_type,
        cover_path
    ))

       self.connection.commit()

    def get_books(self):

        self.cursor.execute("""
            SELECT *
            FROM books
            ORDER BY date_added DESC
        """)

        return self.cursor.fetchall()

    def get_book_by_title(self, title):

        self.cursor.execute("""
            SELECT *
            FROM books
            WHERE title = ?
        """, (title,))

        return self.cursor.fetchone()
    
    def update_progress(
        self,
        book_id,
        current_page,
        total_pages
    ):

        progress = round(
            (current_page / total_pages) * 100,
            1 
        )

        status = "reading"

        if progress >= 100:
            status = "finished"

        self.cursor.execute("""
        UPDATE books
        SET
            current_page = ?,
            progress = ?,
            status = ?
        WHERE id = ?
        """, (
        current_page,
        progress,
        status,
        book_id
        ))

        self.connection.commit()

    def toggle_favorite(self, book_id):
        self.cursor.execute("""
            UPDATE books
            SET favorite = CASE WHEN favorite = 1 THEN 0 ELSE 1 END
            WHERE id = ?
        """, (book_id,))
        self.connection.commit()

    def get_books_by_filter(self, filter_type):
        """Retorna os livros filtrados do banco de dados."""
        if filter_type == "all":
            return self.get_books()
            
        elif filter_type == "favorite":
            self.cursor.execute("""
                SELECT * FROM books WHERE favorite = 1 ORDER BY date_added DESC
            """)
            return self.cursor.fetchall()
            
        else:
            # Filtros por status: 'reading' (Lendo), 'finished' (Lidos), 'unread' (Não lidos)
            self.cursor.execute("""
                SELECT * FROM books WHERE status = ? ORDER BY date_added DESC
            """, (filter_type,))
            return self.cursor.fetchall()    

    def close(self):
        self.connection.close()