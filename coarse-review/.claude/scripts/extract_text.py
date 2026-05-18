#!/usr/bin/env python3
"""Extract text from various document formats to markdown.

Supports: .md, .txt, .tex, .html, .htm, .docx, .epub, .pdf
Pure Python — uses only stdlib + optional packages (markdownify, mammoth, ebooklib, pymupdf).
For PDFs, uses PyMuPDF (free, local, no API).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SUPPORTED_EXTENSIONS = {".md", ".txt", ".tex", ".latex", ".html", ".htm", ".docx", ".epub", ".pdf"}

_LATEX_HEADING_RE = re.compile(r"\\(section|subsection|subsubsection|paragraph)\*?\{([^}]*)\}")
_LATEX_HEADING_LEVEL = {
    "section": "#",
    "subsection": "##",
    "subsubsection": "###",
    "paragraph": "####",
}
_LATEX_PREAMBLE_RE = re.compile(
    r"^\\(documentclass|usepackage|title|author|date|maketitle"
    r"|begin\{document\}|end\{document\}).*$",
    re.MULTILINE,
)


def _extract_plaintext(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_latex(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = _LATEX_PREAMBLE_RE.sub("", text)
    text = _LATEX_HEADING_RE.sub(lambda m: f"{_LATEX_HEADING_LEVEL[m.group(1)]} {m.group(2)}", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_html(path: Path) -> str:
    try:
        import markdownify
    except ImportError:
        raise RuntimeError("HTML extraction requires markdownify: pip install markdownify")
    html_str = path.read_text(encoding="utf-8")
    return markdownify.markdownify(html_str, heading_style="ATX")


def _extract_docx(path: Path) -> str:
    try:
        import mammoth
    except ImportError:
        raise RuntimeError("DOCX extraction requires mammoth: pip install mammoth")
    with open(path, "rb") as f:
        result = mammoth.convert_to_markdown(f)
    return result.value


def _extract_epub(path: Path) -> str:
    try:
        import ebooklib
        import markdownify
        from ebooklib import epub
    except ImportError:
        raise RuntimeError("EPUB extraction requires ebooklib and markdownify")
    book = epub.read_epub(str(path))
    chapters = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        html_content = item.get_content().decode("utf-8", errors="replace")
        md = markdownify.markdownify(html_content, heading_style="ATX")
        md = md.strip()
        if md:
            chapters.append(md)
    if not chapters:
        raise RuntimeError(f"No text content found in EPUB: {path}")
    return "\n\n---\n\n".join(chapters)


def _extract_pdf(path: Path) -> str:
    try:
        import pymupdf
    except ImportError:
        import subprocess
        import sys
        print("PyMuPDF not found. Installing automatically...", file=sys.stderr)
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pymupdf"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            import pymupdf
        except Exception:
            raise RuntimeError(
                "Failed to install PyMuPDF automatically. Please run manually:\n"
                "  pip install pymupdf\n"
                "PyMuPDF is a free, open-source PDF library. No API key needed.\n"
                "Alternatively, convert your PDF to markdown first using https://www.datalab.to/playground/documents/new"
            )
    doc = pymupdf.open(path)
    pages = []
    for page in doc:
        text = page.get_text("text", sort=True)
        if text.strip():
            pages.append(text.strip())
    doc.close()
    if not pages:
        raise RuntimeError(f"No text content found in PDF: {path}")
    return "\n\n".join(pages)


def extract_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".md", ".txt", ".markdown"):
        return _extract_plaintext(path)
    if ext in (".tex", ".latex"):
        return _extract_latex(path)
    if ext in (".html", ".htm"):
        return _extract_html(path)
    if ext == ".docx":
        return _extract_docx(path)
    if ext == ".epub":
        return _extract_epub(path)
    if ext == ".pdf":
        return _extract_pdf(path)
    raise RuntimeError(f"Unsupported file extension: {ext}")


def main():
    if len(sys.argv) < 2:
        print("Usage: extract_text.py <input_file> [output_file]", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        text = extract_file(input_path)
        if output_path:
            output_path.write_text(text, encoding="utf-8")
            print(f"Extracted to: {output_path}")
        else:
            print(text)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
