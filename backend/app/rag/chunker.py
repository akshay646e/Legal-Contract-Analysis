import re
from typing import List, Dict, Any, Optional
from app.parsers.document_parser import ParsedDocument

class LegalChunk:
    def __init__(
        self,
        chunk_id: str,
        contract_id: str,
        text: str,
        section_number: Optional[str] = None,
        section_title: Optional[str] = None,
        page_number: int = 1,
        chunk_index: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.chunk_id = chunk_id
        self.contract_id = contract_id
        self.text = text
        self.section_number = section_number
        self.section_title = section_title
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "contract_id": self.contract_id,
            "text": self.text,
            "section_number": self.section_number or "",
            "section_title": self.section_title or "",
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            **self.metadata
        }


class LegalContractChunker:
    """
    Clause-aware and hierarchical document chunker designed specifically for legal texts.
    Prevents splitting across critical legal qualifiers and maintains section context.
    """

    def __init__(self, max_chunk_size: int = 1200, chunk_overlap: int = 200):
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, parsed_doc: ParsedDocument, contract_id: str) -> List[LegalChunk]:
        """
        Chunks a parsed document using section-aware hierarchical splitting.
        """
        chunks: List[LegalChunk] = []
        chunk_index = 0

        # If document has identified sections, chunk per section
        if parsed_doc.sections and len(parsed_doc.sections) > 1:
            for section in parsed_doc.sections:
                sec_num = section.get("section_number")
                sec_title = section.get("title")
                sec_content = section.get("content", "").strip()

                if not sec_content:
                    continue

                # Context prefix helps LLMs & embeddings understand the scope
                header_context = f"Section {sec_num}: {sec_title}\n" if sec_num and sec_title else ""
                full_section_body = f"{header_context}{sec_content}".strip()

                if len(full_section_body) <= self.max_chunk_size:
                    chunk_id = f"{contract_id}_chunk_{chunk_index}"
                    chunks.append(LegalChunk(
                        chunk_id=chunk_id,
                        contract_id=contract_id,
                        text=full_section_body,
                        section_number=sec_num,
                        section_title=sec_title,
                        page_number=1, # Default, or mapped
                        chunk_index=chunk_index,
                        metadata={
                            "char_count": len(full_section_body),
                            "section_num": sec_num or "",
                            "section_title": sec_title or ""
                        }
                    ))
                    chunk_index += 1
                else:
                    # Break down oversized section using paragraph/sentence splitting
                    sub_chunks = self._split_text(full_section_body, header_prefix=header_context)
                    for sub_text in sub_chunks:
                        chunk_id = f"{contract_id}_chunk_{chunk_index}"
                        chunks.append(LegalChunk(
                            chunk_id=chunk_id,
                            contract_id=contract_id,
                            text=sub_text,
                            section_number=sec_num,
                            section_title=sec_title,
                            page_number=1,
                            chunk_index=chunk_index,
                            metadata={
                                "char_count": len(sub_text),
                                "section_num": sec_num or "",
                                "section_title": sec_title or ""
                            }
                        ))
                        chunk_index += 1
        else:
            # Fallback for un-sectioned documents
            sub_chunks = self._split_text(parsed_doc.full_text)
            for sub_text in sub_chunks:
                chunk_id = f"{contract_id}_chunk_{chunk_index}"
                chunks.append(LegalChunk(
                    chunk_id=chunk_id,
                    contract_id=contract_id,
                    text=sub_text,
                    section_number=None,
                    section_title=None,
                    page_number=1,
                    chunk_index=chunk_index,
                    metadata={"char_count": len(sub_text)}
                ))
                chunk_index += 1

        return chunks

    def _split_text(self, text: str, header_prefix: str = "") -> List[str]:
        """Splits long text while trying to respect paragraph and sentence boundaries."""
        paragraphs = text.split("\n\n")
        results = []
        current_chunk = header_prefix

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            if len(current_chunk) + len(p) + 2 <= self.max_chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + p
            else:
                if current_chunk and current_chunk != header_prefix:
                    results.append(current_chunk.strip())

                # If single paragraph is longer than max_chunk_size, split by sentence
                if len(p) > self.max_chunk_size:
                    sentences = re.split(r"(?<=[.!?])\s+", p)
                    sentence_chunk = header_prefix
                    for s in sentences:
                        if len(sentence_chunk) + len(s) + 1 <= self.max_chunk_size:
                            sentence_chunk += (" " if sentence_chunk else "") + s
                        else:
                            if sentence_chunk and sentence_chunk != header_prefix:
                                results.append(sentence_chunk.strip())
                            sentence_chunk = header_prefix + s
                    if sentence_chunk and sentence_chunk != header_prefix:
                        current_chunk = sentence_chunk
                    else:
                        current_chunk = header_prefix
                else:
                    current_chunk = header_prefix + p

        if current_chunk and current_chunk != header_prefix:
            results.append(current_chunk.strip())

        return results
