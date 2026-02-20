"""PDF generation via WeasyPrint – returns bytes for web download."""

from weasyprint import HTML as WeasyHTML


class PDFGenerationError(Exception):
    pass


def generate_pdf_bytes(html_content: str) -> bytes:
    """Generate PDF from HTML string, return raw bytes."""
    try:
        return WeasyHTML(string=html_content).write_pdf()
    except Exception as e:
        raise PDFGenerationError(f"WeasyPrint failed: {e}") from e
