#!/usr/bin/env python3
"""Parse academic paper structure from markdown/text.

Extracts title, abstract, sections, claims, definitions, and math content.
Pure Python — no API calls, no external dependencies beyond stdlib.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Section type classification
# ---------------------------------------------------------------------------

_TYPE_KEYWORDS: dict[str, str] = {
    "abstract": "ABSTRACT",
    "introduction": "INTRODUCTION",
    "related work": "RELATED_WORK",
    "literature": "RELATED_WORK",
    "prior work": "RELATED_WORK",
    "background": "RELATED_WORK",
    "method": "METHODOLOGY",
    "methodology": "METHODOLOGY",
    "approach": "METHODOLOGY",
    "model": "METHODOLOGY",
    "identification": "METHODOLOGY",
    "estimation": "METHODOLOGY",
    "result": "RESULTS",
    "finding": "RESULTS",
    "experiment": "RESULTS",
    "simulation": "RESULTS",
    "empirical": "RESULTS",
    "discussion": "DISCUSSION",
    "conclusion": "CONCLUSION",
    "concluding": "CONCLUSION",
    "summary": "CONCLUSION",
    "appendix": "APPENDIX",
    "supplementary": "APPENDIX",
    "reference": "REFERENCES",
    "bibliography": "REFERENCES",
}

# Regex for markdown headings: # through ####
_HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)

# Regex to detect formal statement headers
_FORMAL_HEADER_RE = re.compile(
    r"\*{0,2}"
    r"\b(Theorem|Lemma|Proposition|Corollary|Claim|Result"
    r"|Definition|Assumption|Condition|Axiom|Conjecture|Hypothesis)\b"
    r"\s*\*{0,2}"
    r"\s*"
    r"([A-Z]?\d*[a-z]?(?:\.\d+)?)",
    re.IGNORECASE,
)

# Math detection patterns
_MATH_PATTERN = re.compile(
    r"\\[a-zA-Z]+|"
    r"\$[^$]+\$|"
    r"\\\[|\\\]|"
    r"\\begin\{equation\}|"
    r"\\begin\{align\}|"
    r"\\begin\{theorem\}|"
    r"\\begin\{proof\}|"
    r"\\begin\{lemma\}|"
    r"\\begin\{definition\}"
)

_PROOF_KEYWORDS = frozenset([
    "theorem", "proof", "lemma", "proposition", "corollary",
    "q.e.d", "qed", "∎", "□", "we prove", "we show that", "it follows that",
])


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Section:
    number: int = 0
    title: str = ""
    text: str = ""
    section_type: str = "OTHER"
    claims: list[str] = field(default_factory=list)
    definitions: list[str] = field(default_factory=list)
    math_content: bool = False


@dataclass
class PaperStructure:
    title: str = "Untitled"
    abstract: str = ""
    domain: str = "unknown"
    document_form: str = "manuscript"
    sections: list[Section] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsing functions
# ---------------------------------------------------------------------------

def _classify_section_type(title: str) -> str:
    title_lower = title.lower()
    for keyword, stype in _TYPE_KEYWORDS.items():
        if keyword in title_lower:
            return stype
    return "OTHER"


def _is_section_heading(title: str) -> bool:
    title_lower = title.lower().strip()
    title_lower = re.sub(r"^[\dA-Za-z]+[\.\)]\s*", "", title_lower).strip()
    return any(kw in title_lower for kw in _TYPE_KEYWORDS)


def _extract_title(markdown: str) -> str:
    matches = list(_HEADING_RE.finditer(markdown))
    for match in matches:
        candidate = match.group(2).strip()
        if not _is_section_heading(candidate):
            return candidate
    if matches:
        preamble = markdown[: matches[0].start()].strip()
        if preamble:
            for line in preamble.split("\n"):
                line = line.strip()
                if line and len(line) > 3:
                    return line
    for line in markdown.split("\n"):
        line = line.strip()
        if line:
            return line
    return "Untitled"


def _extract_abstract(sections: list[Section], markdown: str) -> str:
    for section in sections:
        if section.section_type == "ABSTRACT":
            return section.text[:2000]
    match = _HEADING_RE.search(markdown)
    if match and match.start() > 0:
        return markdown[: match.start()].strip()[:2000]
    return markdown[:500].strip()


def _extract_claims_and_definitions(text: str) -> tuple[list[str], list[str]]:
    claims: list[str] = []
    definitions: list[str] = []
    paragraphs = re.split(r"\n\s*\n", text)
    for para in paragraphs:
        m = _FORMAL_HEADER_RE.search(para)
        if not m:
            continue
        kind = m.group(1).lower()
        label = m.group(2).strip()
        statement = para[m.end():].strip()
        statement = re.sub(r"^[.*:)\s]+", "", statement)
        short = statement[:500] + ("..." if len(statement) > 500 else "")
        entry = f"{m.group(1)} {label}: {short}".strip()
        if kind in ("definition", "axiom"):
            definitions.append(entry)
        else:
            claims.append(entry)
    return claims, definitions


def _detect_math_content(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    has_proof_keywords = any(kw in text_lower for kw in _PROOF_KEYWORDS)
    has_math_syntax = bool(_MATH_PATTERN.search(text))
    return has_proof_keywords or has_math_syntax


def _parse_sections(markdown: str) -> list[Section]:
    matches = list(_HEADING_RE.finditer(markdown))
    if not matches:
        return [Section(number=1, title="Full Document", text=markdown.strip())]

    sections: list[Section] = []
    for i, match in enumerate(matches):
        title = match.group(2).strip()
        text_start = match.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        text = markdown[text_start:text_end].strip()
        section_type = _classify_section_type(title)
        claims, definitions = _extract_claims_and_definitions(text)
        math_content = _detect_math_content(text)

        sections.append(Section(
            number=i + 1,
            title=title,
            text=text,
            section_type=section_type,
            claims=claims,
            definitions=definitions,
            math_content=math_content,
        ))
    return sections


def _detect_document_form(sections: list[Section]) -> str:
    """Heuristic document form detection without LLM."""
    if not sections:
        return "draft"

    total_prose = 0
    bullet_lines = 0
    heading_lines = 0

    for s in sections:
        for line in s.text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped[0] in ("-", "*", "•"):
                bullet_lines += 1
            elif stripped[0] == "#":
                heading_lines += 1
            else:
                total_prose += len(stripped)

    avg_prose = total_prose / len(sections) if sections else 0

    # Heavy bullet/heading ratio suggests outline
    total_lines = sum(len(s.text.splitlines()) for s in sections)
    if total_lines > 0:
        non_prose_ratio = (bullet_lines + heading_lines) / total_lines
        if non_prose_ratio > 0.6 and avg_prose < 200:
            return "outline"

    # Very low prose average suggests outline or notes
    if avg_prose < 100:
        return "notes"

    # Moderate prose with bullets suggests draft
    if avg_prose < 300 and bullet_lines > 0:
        return "draft"

    return "manuscript"


def _heuristic_domain(text: str) -> str:
    """Simple keyword-based domain detection."""
    text_lower = text.lower()
    domains = {
        "computer_science": ["algorithm", "neural network", "deep learning", "machine learning",
                            "training", "model", "dataset", "benchmark", "code", "software"],
        "economics": ["causal", "instrumental variable", "treatment effect", "policy",
                     "regression", "rd design", "difference-in-differences", "panel data"],
        "biology": ["gene", "protein", "cell", "tissue", "organism", "species",
                   "clinical trial", "patient", "drug", "treatment"],
        "physics": ["quantum", "field theory", "hamiltonian", "lagrangian",
                   "experiment", "measurement", "particle"],
        "mathematics": ["theorem", "proof", "lemma", "conjecture", "axiom",
                       "category", "homology", "cohomology"],
        "social_science": ["survey", "interview", "ethnography", "qualitative",
                          "mixed methods", "case study"],
    }

    scores = {domain: sum(1 for kw in keywords if kw in text_lower)
              for domain, keywords in domains.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else "general"


def parse_paper(markdown: str) -> PaperStructure:
    """Parse paper structure from markdown text."""
    sections = _parse_sections(markdown)
    title = _extract_title(markdown)
    abstract = _extract_abstract(sections, markdown)
    document_form = _detect_document_form(sections)
    domain = _heuristic_domain(markdown[:5000])

    return PaperStructure(
        title=title,
        abstract=abstract,
        domain=domain,
        document_form=document_form,
        sections=sections,
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: parse_paper.py <paper.md|->", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    if path == "-":
        text = sys.stdin.read()
    else:
        text = Path(path).read_text(encoding="utf-8")

    result = parse_paper(text)
    # Convert dataclasses to dicts for JSON serialization
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
