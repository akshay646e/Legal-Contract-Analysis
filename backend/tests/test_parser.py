import pytest
from app.parsers.preprocessor import LegalTextPreprocessor
from app.parsers.document_parser import DocumentParser

SAMPLE_CONTRACT_TEXT = """
MUTUAL NONDISCLOSURE AGREEMENT

1. PURPOSE
The parties wish to explore a potential business transaction.

2. CONFIDENTIAL INFORMATION
"Confidential Information" means any proprietary information disclosed.

3. EXCLUSIONS FROM CONFIDENTIALITY
Information is excluded if publicly known through no breach.
"""

def test_legal_preprocessor_cleaning():
    dirty_text = "Page 1 of 5\n\n1. PURPOSE\n\n\n\nThis is a test.   Extra spaces."
    cleaned = LegalTextPreprocessor.clean_text(dirty_text)
    assert "Page 1 of 5" not in cleaned
    assert "   " not in cleaned
    assert "1. PURPOSE" in cleaned

def test_legal_preprocessor_section_identification():
    sections = LegalTextPreprocessor.identify_sections(SAMPLE_CONTRACT_TEXT)
    assert len(sections) >= 3
    section_titles = [s["title"].upper() for s in sections]
    assert "PURPOSE" in section_titles
    assert "CONFIDENTIAL INFORMATION" in section_titles

def test_parse_sample_file():
    parsed = DocumentParser.parse_file("sample_contracts/nda_mutual.txt")
    assert parsed.file_type == "txt"
    assert len(parsed.sections) > 0
    assert "Apex Digital Solutions" in parsed.full_text
