import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
import docx

from app.parsers.preprocessor import LegalTextPreprocessor
from app.core.logging import logger

class ParsedPage:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text

class ParsedDocument:
    def __init__(self, filename: str, file_type: str, total_pages: int, full_text: str, pages: List[ParsedPage], sections: List[Dict[str, Any]]):
        self.filename = filename
        self.file_type = file_type
        self.total_pages = total_pages
        self.full_text = full_text
        self.pages = pages
        self.sections = sections

class DocumentParser:
    """
    Multi-format legal document parser supporting PDF, DOCX, and TXT.
    Extracts text while preserving page numbers and legal clause structures.
    """

    @classmethod
    def parse_file(cls, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Contract file not found at: {file_path}")

        suffix = path.suffix.lower()
        logger.info(f"Parsing document: [cyan]{path.name}[/cyan] with extension [yellow]{suffix}[/yellow]")

        if suffix == ".pdf":
            return cls._parse_pdf(path)
        elif suffix in [".docx", ".doc"]:
            return cls._parse_docx(path)
        elif suffix in [".txt", ".md", ".rtf"]:
            return cls._parse_text(path)
        else:
            raise ValueError(f"Unsupported document format: {suffix}. Allowed formats: .pdf, .docx, .txt")

    @classmethod
    def _parse_pdf(cls, path: Path) -> ParsedDocument:
        reader = PdfReader(str(path))
        pages: List[ParsedPage] = []
        full_text_parts = []

        total_pages = len(reader.pages)
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            cleaned_page_text = LegalTextPreprocessor.clean_text(page_text)
            pages.append(ParsedPage(page_number=idx + 1, text=cleaned_page_text))
            full_text_parts.append(cleaned_page_text)

        full_text = "\n\n".join(full_text_parts)
        sections = LegalTextPreprocessor.identify_sections(full_text)

        return ParsedDocument(
            filename=path.name,
            file_type="pdf",
            total_pages=total_pages,
            full_text=full_text,
            pages=pages,
            sections=sections
        )

    @classmethod
    def _parse_docx(cls, path: Path) -> ParsedDocument:
        doc = docx.Document(str(path))
        paragraphs = []
        for p in doc.paragraphs:
            if p.text.strip():
                paragraphs.append(p.text.strip())

        # Also extract table text if any
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)

        raw_text = "\n".join(paragraphs)
        cleaned_text = LegalTextPreprocessor.clean_text(raw_text)
        sections = LegalTextPreprocessor.identify_sections(cleaned_text)

        # DOCX doesn't have intrinsic page layout without Word rendering engine, so estimate ~500 words per page
        word_count = len(cleaned_text.split())
        est_pages = max(1, (word_count // 500) + 1)
        pages = [ParsedPage(page_number=1, text=cleaned_text)]

        return ParsedDocument(
            filename=path.name,
            file_type="docx",
            total_pages=est_pages,
            full_text=cleaned_text,
            pages=pages,
            sections=sections
        )

    @classmethod
    def _parse_text(cls, path: Path) -> ParsedDocument:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

        cleaned_text = LegalTextPreprocessor.clean_text(content)
        sections = LegalTextPreprocessor.identify_sections(cleaned_text)

        word_count = len(cleaned_text.split())
        est_pages = max(1, (word_count // 500) + 1)
        pages = [ParsedPage(page_number=1, text=cleaned_text)]

        return ParsedDocument(
            filename=path.name,
            file_type="txt",
            total_pages=est_pages,
            full_text=cleaned_text,
            pages=pages,
            sections=sections
        )
