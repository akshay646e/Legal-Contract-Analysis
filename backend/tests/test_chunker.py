import pytest
from app.parsers.document_parser import DocumentParser
from app.rag.chunker import LegalContractChunker

def test_legal_contract_chunker():
    parsed = DocumentParser.parse_file("sample_contracts/saas_agreement.txt")
    chunker = LegalContractChunker(max_chunk_size=800, chunk_overlap=150)
    chunks = chunker.chunk_document(parsed, contract_id="test-saas-101")

    assert len(chunks) > 0
    # Every chunk should have contract_id and text
    for c in chunks:
        assert c.contract_id == "test-saas-101"
        assert len(c.text) > 0
        assert c.chunk_id.startswith("test-saas-101_chunk_")

def test_chunker_preserves_section_context():
    parsed = DocumentParser.parse_file("sample_contracts/nda_mutual.txt")
    chunker = LegalContractChunker(max_chunk_size=1200)
    chunks = chunker.chunk_document(parsed, contract_id="test-nda-101")

    section_titles = [c.section_title for c in chunks if c.section_title]
    assert len(section_titles) > 0
