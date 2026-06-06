class Book:
    def __init__(
        self,
        title,
        author,
        file_path,
        file_type,
        cover_path=None,
        total_pages=0,
        current_page=0,
        progress=0,
        status="unread",
        favorite=0
    ):
        self.title = title
        self.author = author
        self.file_path = file_path
        self.file_type = file_type
        self.cover_path = cover_path

        self.total_pages = total_pages
        self.current_page = current_page

        self.progress = progress

        self.status = status

        self.favorite = favorite

    def __str__(self):
        return f"{self.title} ({self.file_type})"