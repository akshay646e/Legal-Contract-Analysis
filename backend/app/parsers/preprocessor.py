import re
from typing import List, Dict, Any

class LegalTextPreprocessor:
    """
    Cleans, normalizes, and segments legal contract text.
    Handles legal numbering artifacts, headers, footers, and whitespace.
    """

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Removes extraneous characters, standardizes line breaks and whitespace."""
        if not raw_text:
            return ""

        # Normalize line endings
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

        # Strip common legal header/footer noise (e.g. Page X of Y, Confidential)
        text = re.sub(r"(?i)Page\s+\d+\s+of\s+\d+", "", text)
        text = re.sub(r"(?i)---\s*Confidential\s*---", "", text)

        # Replace non-breaking spaces and excessive inline spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Collapse more than two consecutive newlines into two
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def identify_sections(text: str) -> List[Dict[str, Any]]:
        """
        Segments raw contract text into numbered sections / articles.
        Matches patterns like:
          - '1. PURPOSE'
          - 'Section 3. EXCLUSIONS'
          - 'ARTICLE IV - INDEMNIFICATION'
          - '4.1 Termination for Cause'
        """
        section_pattern = re.compile(
            r"(?m)^(?:(?P<prefix>SECTION|ARTICLE|CLAUSE)\s+)?(?P<num>\d+(?:\.\d+)*|[IVXLCDM]+)[\.\:\-\s]+(?P<title>[A-Z\s\(\)\,\-\/]{3,60})(?:\n|$)",
            re.IGNORECASE
        )

        matches = list(section_pattern.finditer(text))
        sections = []

        if not matches:
            # If no explicit numbered sections found, treat as one general section
            return [{
                "section_number": "1",
                "title": "General Terms",
                "content": text.strip(),
                "start_char": 0,
                "end_char": len(text)
            }]

        # Process matched sections and capture content between headers
        for i, match in enumerate(matches):
            section_num = match.group("num") or str(i + 1)
            title = match.group("title").strip() if match.group("title") else "Untitled"
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            content = text[start_pos:end_pos].strip()

            sections.append({
                "section_number": section_num.strip(),
                "title": title.strip(),
                "content": content,
                "start_char": match.start(),
                "end_char": end_pos
            })

        return sections
