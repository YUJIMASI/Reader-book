import fitz
import os


def generate_pdf_cover(pdf_path, output_path):

    try:
        doc = fitz.open(pdf_path)

        page = doc.load_page(0)

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

        pix.save(output_path)

        doc.close()

        return output_path

    except Exception as e:
        print("Erro ao gerar capa:", e)
        return None