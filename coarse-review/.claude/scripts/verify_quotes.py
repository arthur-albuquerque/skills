#!/usr/bin/env python3
"""Verify that review comment quotes are actual substrings of the paper.

Uses fuzzy matching to correct garbled quotes from extraction artifacts.
Applies stricter thresholds for math-heavy quotes.

Pure Python — no API calls, only stdlib.
"""
from __future__ import annotations

import difflib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

_MIN_MATCH_RATIO = 0.80
_MIN_MATH_MATCH_RATIO = 0.92
_GARBLE_THRESHOLD = 0.005

_MATH_PATTERN = re.compile(
    r"\\[a-zA-Z]+|"
    r"\$[^$]+\$|"
    r"\b\d+\.?\d*\b|"
    r"[=<>≤≥±∑∏∫]"
)
_TABLE_LINE_RE = re.compile(r"^\s*\|.*\|\s*$")


@dataclass
class Comment:
    number: int = 0
    title: str = ""
    quote: str = ""
    feedback: str = ""
    confidence: str = "medium"
    comment_type: str = "gap"


@dataclass
class VerificationResult:
    verified: list[Comment] = field(default_factory=list)
    dropped: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _is_math_heavy(text: str) -> bool:
    if not text:
        return False
    matches = _MATH_PATTERN.findall(text)
    if not matches:
        return False
    math_len = sum(len(m) for m in matches)
    density = math_len / len(text)
    if density < 0.05:
        return False
    return len(matches) >= 3 or density > 0.10


def _normalize_for_matching(text: str) -> tuple[str, list[int]]:
    out: list[str] = []
    index_map: list[int] = []
    in_whitespace = False
    for idx, ch in enumerate(text):
        normalized = unicodedata.normalize("NFKC", ch)
        for norm_ch in normalized:
            if norm_ch in {"–", "—", "−"}:
                norm_ch = "-"
            elif norm_ch in {'\u201c', '\u201d'}:
                norm_ch = '"'
            elif norm_ch in {'\u2018', '\u2019'}:
                norm_ch = "\'"
            if norm_ch.isspace():
                if out and not in_whitespace:
                    out.append(" ")
                    index_map.append(idx)
                in_whitespace = True
                continue
            out.append(norm_ch.lower())
            index_map.append(idx)
            in_whitespace = False
    if out and out[-1] == " ":
        out.pop()
        index_map.pop()
    return "".join(out), index_map


def _find_normalized_substring(quote: str, paper_text: str) -> str:
    if not quote or not paper_text:
        return ""
    norm_quote, _ = _normalize_for_matching(quote)
    norm_paper, index_map = _normalize_for_matching(paper_text)
    if not norm_quote or not norm_paper:
        return ""
    start = norm_paper.find(norm_quote)
    if start == -1:
        return ""
    end = start + len(norm_quote) - 1
    return paper_text[index_map[start]:index_map[end] + 1]


def _canonicalize_table_line(line: str) -> str:
    if not _TABLE_LINE_RE.match(line):
        return ""
    raw_cells = line.strip().strip("|").split("|")
    cells = [re.sub(r"\s+", " ", cell.strip()) for cell in raw_cells]
    if not any(cells):
        return ""
    if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells if cell):
        return ""
    return "|".join(cells)


def _find_table_substring(quote: str, paper_text: str) -> str:
    quote_rows = []
    for line in quote.splitlines():
        canonical = _canonicalize_table_line(line)
        if canonical:
            quote_rows.append(canonical)
    if not quote_rows:
        return ""
    paper_lines = paper_text.splitlines()
    paper_rows = []
    for idx, line in enumerate(paper_lines):
        canonical = _canonicalize_table_line(line)
        if canonical:
            paper_rows.append((idx, canonical))
    if len(paper_rows) < len(quote_rows):
        return ""
    for start in range(0, len(paper_rows) - len(quote_rows) + 1):
        window = paper_rows[start:start + len(quote_rows)]
        if [row for _, row in window] == quote_rows:
            line_start = window[0][0]
            line_end = window[-1][0] + 1
            return "\n".join(paper_lines[line_start:line_end]).strip()
    return ""


def _tokenize(text: str) -> set[str]:
    return set(text.lower().split())


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _similarity_ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _trim_to_best_match(quote: str, passage: str) -> str:
    if len(passage) <= len(quote):
        return passage
    quote_len = len(quote)
    max_window = min(len(passage), int(quote_len * 1.5))
    candidate_windows = sorted({quote_len, max_window, int(quote_len * 1.1), int(quote_len * 1.25)})
    best_ratio = 0.0
    best_sub = passage[:max_window]
    for window in candidate_windows:
        window = max(quote_len, min(window, len(passage)))
        step = max(1, window // 8)
        for start in range(0, len(passage) - window + 1, step):
            sub = passage[start:start + window]
            ratio = _similarity_ratio(quote, sub)
            if ratio > best_ratio + 0.02:
                best_ratio = ratio
                best_sub = sub
            elif ratio >= best_ratio - 0.02 and len(sub) > len(best_sub):
                best_ratio = ratio
                best_sub = sub
    return best_sub


def _find_candidate_passages(quote: str, paper_text: str, top_k: int = 3) -> list[tuple[str, float]]:
    if not quote or not paper_text:
        return []
    quote_len = len(quote)
    window_size = max(int(quote_len * 1.5), 50)
    step = max(1, quote_len // 4)
    quote_tokens = _tokenize(quote)
    stop = max(1, len(paper_text) - window_size + 1)
    candidates = []
    for i in range(0, stop, step):
        chunk = paper_text[i:i + window_size]
        score = _jaccard(quote_tokens, _tokenize(chunk))
        candidates.append((score, i))
    candidates.sort(key=lambda x: x[0], reverse=True)
    top_candidates = candidates[:5]
    scored = []
    seen = set()
    for _, i in top_candidates:
        candidate = paper_text[i:i + window_size]
        trimmed = _trim_to_best_match(quote, candidate)
        variants = [candidate, trimmed]
        best_variant = ""
        best_ratio = 0.0
        for variant in variants:
            ratio = _similarity_ratio(quote, variant)
            if ratio > best_ratio:
                best_ratio = ratio
                best_variant = variant
        norm, _ = _normalize_for_matching(best_variant)
        canonical = norm
        if best_variant and canonical not in seen:
            seen.add(canonical)
            scored.append((best_variant, best_ratio))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:top_k]


def verify_quotes(comments: list[Comment], paper_text: str) -> VerificationResult:
    paper_lower = paper_text.lower()
    result = []
    dropped = []
    stats = {"exact": 0, "fuzzy": 0, "dropped": 0, "empty": 0}

    for comment in comments:
        if not comment.quote or not comment.quote.strip():
            stats["empty"] += 1
            result.append(comment)
            continue

        if comment.quote.lower() in paper_lower:
            stats["exact"] += 1
            result.append(comment)
            continue

        normalized_match = _find_normalized_substring(comment.quote, paper_text)
        if normalized_match:
            stats["fuzzy"] += 1
            comment.quote = normalized_match
            result.append(comment)
            continue

        table_match = _find_table_substring(comment.quote, paper_text)
        if table_match:
            stats["fuzzy"] += 1
            comment.quote = table_match
            result.append(comment)
            continue

        candidates = _find_candidate_passages(comment.quote, paper_text)
        best_match, ratio = candidates[0] if candidates else ("", 0.0)

        math_heavy = _is_math_heavy(comment.quote)
        threshold = _MIN_MATH_MATCH_RATIO if math_heavy else _MIN_MATCH_RATIO

        if ratio >= threshold and best_match:
            stats["fuzzy"] += 1
            comment.quote = best_match
            result.append(comment)
        else:
            stats["dropped"] += 1
            dropped.append({
                "comment": {"title": comment.title, "quote": comment.quote},
                "ratio": ratio,
                "threshold": threshold,
                "best_match": best_match,
            })

    return VerificationResult(verified=result, dropped=dropped, stats=stats)


def main():
    if len(sys.argv) < 3:
        print("Usage: verify_quotes.py <paper.md> <comments.json>", file=sys.stderr)
        sys.exit(1)

    paper_path = sys.argv[1]
    comments_path = sys.argv[2]

    paper_text = Path(paper_path).read_text(encoding="utf-8")
    comments_data = json.loads(Path(comments_path).read_text(encoding="utf-8"))

    comments = []
    for c in comments_data:
        c = dict(c)
        if "type" in c:
            c["comment_type"] = c.pop("type")
        comments.append(Comment(**c))
    result = verify_quotes(comments, paper_text)

    output = {
        "verified": [
            {"number": c.number, "title": c.title, "quote": c.quote,
             "feedback": c.feedback, "confidence": c.confidence, "type": c.comment_type}
            for c in result.verified
        ],
        "dropped": result.dropped,
        "stats": result.stats,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
