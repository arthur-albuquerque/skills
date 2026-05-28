#!/usr/bin/env python3
"""Build document.json for the sciwrite_interactive editor.

The agent emits only a compact suggestions.json (findings, in document order); this
script copies the unchanged prose straight from the source manuscript and splices
the suggestions in. The editor's per-paragraph faithfulness guarantee then holds
by construction instead of by hand, and the heavy work of re-typing the document
as JSON disappears from the agent's output.

Usage:
  python3 build_document.py --suggestions <suggestions.json> \
      [--out <document.json>] [--source <manuscript>]

suggestions.json schema:
  {
    "title": "...",
    "source_path": "/abs/path/to/manuscript.md",
    "reviewer": "Writing Review",
    "generated_at": "2026-05-27T10:00:00",
    "suggestions": [
      {"kind": "clutter", "sev": "minor",
       "original": "<verbatim slice of the source>",
       "replacement": "<revised text>",
       "rationale": "<3-6 word margin note>"}
    ]
  }

Exits non-zero with a clear message if any suggestion's "original" cannot be
located in the source in document order, or is too short to place unambiguously;
fix that quote and re-run.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

KINDS = {"clutter", "voice", "architecture", "terminology", "numbers"}
SEVS = {"critical", "major", "minor"}

FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^[\s|:\-]+$")
MATH_FENCE = "$$"


def parse_blocks(src):
    """Split source markdown into heading / verbatim / paragraph raw blocks.

    Verbatim is syntax-only: fenced code, $$ math, and pipe tables. Everything
    else that is not a heading becomes a paragraph block (raw text preserved).
    """
    lines = src.split("\n")
    blocks = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if line.strip() == "":
            i += 1
            continue
        m = FENCE_RE.match(line)
        if m:  # fenced code block
            fence = m.group(1)
            buf = [line]
            i += 1
            while i < n and not lines[i].lstrip().startswith(fence):
                buf.append(lines[i])
                i += 1
            if i < n:
                buf.append(lines[i])
                i += 1
            blocks.append({"type": "verbatim", "markdown": "\n".join(buf)})
            continue
        if line.strip() == MATH_FENCE:  # $$ math block
            buf = [line]
            i += 1
            while i < n and lines[i].strip() != MATH_FENCE:
                buf.append(lines[i])
                i += 1
            if i < n:
                buf.append(lines[i])
                i += 1
            blocks.append({"type": "verbatim", "markdown": "\n".join(buf)})
            continue
        hm = HEADING_RE.match(line)
        if hm:  # ATX heading
            blocks.append({"type": "heading",
                           "level": len(hm.group(1)),
                           "text": hm.group(2).rstrip()})
            i += 1
            continue
        # Gather a paragraph block until a blank line / EOF / new block start.
        buf = [line]
        i += 1
        while i < n and lines[i].strip() != "":
            if (HEADING_RE.match(lines[i]) or FENCE_RE.match(lines[i])
                    or lines[i].strip() == MATH_FENCE):
                break
            buf.append(lines[i])
            i += 1
        if (len(buf) >= 2 and "|" in buf[0] and "-" in buf[1]
                and "|" in buf[1] and TABLE_SEP_RE.match(buf[1].strip())):
            blocks.append({"type": "verbatim", "markdown": "\n".join(buf)})
        else:
            blocks.append({"type": "paragraph", "raw": "\n".join(buf)})
    return blocks


WS_RE = re.compile(r"\s+")

# Length-preserving fold of "smart" punctuation to ASCII so an agent that
# quotes `BALANCE's` still matches a source containing `BALANCE’s`. The build
# script always extracts the *source's* exact bytes for the segment's
# `original`, so the fold only affects matching, never the editor's view.
PUNCT_FOLD = str.maketrans({
    "‘": "'", "’": "'",  # ‘ ’ curly single quotes
    "“": '"', "”": '"',  # “ ” curly double quotes
    "–": "-", "—": "-",  # – — en-dash / em-dash
    "−": "-",                  # − minus sign
    "\u00a0": " ",                  # non-breaking space
})


def locate(raw, needle, start):
    """Find `needle` in `raw` starting at `start`.

    First tries an exact `str.find`. If that fails, retries on a
    whitespace-normalised view (every run of whitespace collapsed to a single
    space) and maps the hit back to raw-source coordinates. Returns
    ``(found, end)`` raw indices, or ``(-1, -1)`` if not located.
    """
    found = raw.find(needle, start)
    if found >= 0:
        return found, found + len(needle)
    # Punctuation-folded fast path: same length on both sides, so we can
    # search the folded raw for the folded needle and reuse the index 1:1.
    raw_folded = raw.translate(PUNCT_FOLD)
    needle_folded = needle.translate(PUNCT_FOLD)
    if needle_folded != needle or raw_folded != raw:
        f = raw_folded.find(needle_folded, start)
        if f >= 0:
            return f, f + len(needle_folded)

    # Build normalised view of raw[start:] with an index map back to raw.
    tail = raw[start:]
    norm_chars = []
    norm_to_raw = []  # norm_to_raw[i] = raw index of norm char i
    j = 0
    while j < len(tail):
        ch = tail[j]
        if ch.isspace():
            # Collapse run of whitespace to a single space.
            norm_chars.append(" ")
            norm_to_raw.append(start + j)
            while j < len(tail) and tail[j].isspace():
                j += 1
            continue
        norm_chars.append(ch.translate(PUNCT_FOLD))
        norm_to_raw.append(start + j)
        j += 1
    norm = "".join(norm_chars)

    needle_norm = WS_RE.sub(" ", needle).translate(PUNCT_FOLD)
    nf = norm.find(needle_norm)
    if nf < 0:
        return -1, -1
    raw_start = norm_to_raw[nf]
    # End is one past the raw index of the last normalised char of the match.
    last_norm = nf + len(needle_norm) - 1
    raw_last = norm_to_raw[last_norm]
    # Extend through any trailing whitespace run that the normaliser collapsed.
    raw_end = raw_last + 1
    return raw_start, raw_end


def segment_paragraph(raw, suggestions, start_idx, id_counter):
    """Split one paragraph into text/suggestion segments using a forward-only
    cursor. Consumes suggestions in order; stops at the first whose `original`
    cannot be located in this paragraph (it belongs to a later block).

    Matching is whitespace-tolerant via `locate`; the segment records the
    *source's* exact substring so the editor round-trips bytes faithfully."""
    segments = []
    pos = 0
    idx = start_idx
    while idx < len(suggestions):
        sug = suggestions[idx]
        found, end = locate(raw, sug["original"], pos)
        if found < 0:
            break
        if found > pos:
            segments.append({"type": "text", "text": raw[pos:found]})
        sid = "s%d" % id_counter[0]
        id_counter[0] += 1
        segments.append({
            "type": "suggestion",
            "id": sid,
            "kind": sug["kind"],
            "sev": sug["sev"],
            "original": raw[found:end],
            "replacement": sug["replacement"],
            "rationale": sug.get("rationale", ""),
        })
        pos = end
        idx += 1
    if pos < len(raw):
        segments.append({"type": "text", "text": raw[pos:]})
    return segments, idx


def preflight(suggestions, src):
    """Locate every suggestion in the source with the same forward-only
    cursor segment_paragraph would use later, but over the whole source so we
    can diagnose *all* failures in one pass and distinguish their causes.

    Returns ``(ok, errors, spans)`` where ``ok`` is True iff there are no
    fatal issues, ``errors`` is a list of human-readable lines, and ``spans``
    is the list of (start, end) raw-source ranges for the successfully
    located suggestions (used to detect overlaps before placement).
    """
    errors = []
    spans = [None] * len(suggestions)
    cursor = 0
    for i, sug in enumerate(suggestions):
        original = sug["original"]
        f, e = locate(src, original, cursor)
        if f >= 0:
            spans[i] = (f, e)
            cursor = e
            continue
        # Forward-locate failed. Disambiguate by trying an unbounded probe.
        gf, ge = locate(src, original, 0)
        if gf >= 0 and gf < cursor:
            # The text DOES exist in source — earlier than the cursor. Either
            # the JSON order is wrong, or a previous suggestion's span
            # already swallowed this one (nested / overlapping).
            errors.append(
                "  #%d  MATCH FOUND at line %d but the forward cursor is "
                "already past it (cursor at line %d).\n"
                "       This usually means another suggestion's `original` "
                "span contains this one, or this suggestion is out of "
                "document order. Merge the two suggestions into one whose "
                "`replacement` applies both fixes, or reorder the JSON.\n"
                "       original: %r"
                % (i + 1, _line_of(src, gf), _line_of(src, cursor), original)
            )
            # Do not advance the cursor — keep checking subsequent ones from
            # the same anchor so we surface every problem in this pass.
            continue
        # Truly not in source even with whitespace + punctuation folding.
        hit = _nearest_in_source(original, src)
        if hit is None:
            errors.append(
                "  #%d  NOT FOUND in source (no similar text).\n"
                "       original: %r" % (i + 1, original)
            )
        else:
            s, e2, ratio = hit
            line = _line_of(src, s)
            snippet = src[max(0, s - 40):min(len(src), e2 + 40)].replace("\n", " ")
            errors.append(
                "  #%d  NOT FOUND in source.\n"
                "       original: %r\n"
                "       nearest (line %d, similarity %.2f):\n"
                "         …%s…"
                % (i + 1, original, line, ratio, snippet)
            )

    # Overlap detection across successfully placed spans. By construction
    # (forward cursor) consecutive spans cannot overlap, but if we ever
    # advance the cursor past a failed nested suggestion's anchor we want
    # this catch in place. O(N) by adjacent pairs is sufficient.
    placed = [(i, s) for i, s in enumerate(spans) if s is not None]
    for a, b in zip(placed, placed[1:]):
        (ia, (sa, ea)), (ib, (sb, eb)) = a, b
        if sb < ea:
            # The merged original is the union of both spans (sa..max(ea, eb)).
            # Whitespace-collapse it so the agent can paste it back into JSON
            # without worrying about embedded newlines from a paragraph-wrap.
            merged = src[sa:max(ea, eb)].replace("\n", " ")
            errors.append(
                "  #%d and #%d overlap in source (lines %d and %d).\n"
                "       Merge into ONE suggestion whose `original` is the full\n"
                "       span below and whose `replacement` applies both fixes.\n"
                "       merged original (verbatim from source, paste as-is):\n"
                "         %r"
                % (ia + 1, ib + 1, _line_of(src, sa), _line_of(src, sb), merged)
            )

    return (not errors), errors, spans


def _line_of(src, idx):
    """1-based line number of character index `idx` in `src`."""
    return src.count("\n", 0, idx) + 1


def _nearest_in_source(needle, src):
    """Return (start, end, ratio) of the closest substring of `src` to
    `needle`, using difflib. Coarse but good enough for a 'did you mean' hint.
    """
    import difflib
    sm = difflib.SequenceMatcher(a=src, b=needle, autojunk=False)
    m = sm.find_longest_match(0, len(src), 0, len(needle))
    if m.size == 0:
        return None
    # Expand the window in `src` to roughly the length of `needle`.
    pad = max(0, (len(needle) - m.size) // 2)
    s = max(0, m.a - pad)
    e = min(len(src), m.a + m.size + pad)
    # Ratio of the local window vs. the needle.
    ratio = difflib.SequenceMatcher(a=src[s:e], b=needle, autojunk=False).ratio()
    return s, e, ratio


def report_placement_failures(suggestions, next_idx, raw_blocks, src):
    """Write a single combined error report to stderr listing every
    unplaced suggestion plus the closest substring we could find in the
    source, with line number and a ±40-char snippet."""
    rest = suggestions[next_idx:]
    sys.stderr.write(
        "ERROR: %d suggestion(s) could not be placed in document order.\n"
        "Each failure is shown below with the nearest substring we found in "
        "the source (line number + snippet). Fix the quotes in your "
        "suggestions.json (whitespace is normalised automatically, so worry "
        "about wording / citation markers like '(REF)' / word order), then "
        "re-run.\n\n"
        % len(rest)
    )
    for offset, sug in enumerate(rest):
        n = next_idx + offset + 1
        original = sug["original"]
        sys.stderr.write("  #%d  original: %r\n" % (n, original))
        hit = _nearest_in_source(original, src)
        if hit is None:
            sys.stderr.write("       (no similar text found)\n\n")
            continue
        s, e, ratio = hit
        line = _line_of(src, s)
        snippet = src[max(0, s - 40):min(len(src), e + 40)].replace("\n", " ")
        sys.stderr.write(
            "       nearest in source (line %d, similarity %.2f):\n"
            "         …%s…\n\n" % (line, ratio, snippet)
        )


def _sort_by_source(suggestions, src):
    """Re-order suggestions to match document order via an unbounded
    whole-source locate of each `original`.

    The forward-cursor placement in segment_paragraph requires document
    order; rather than make the agent maintain that order manually (a common
    retry-loop trigger), we sort here. The sort is stable — when two
    suggestions tie on source position (identical `original`, or one
    anchored at the same offset as another), the agent's authored order is
    preserved and the existing overlap / ambiguity guards in preflight catch
    any collision. Suggestions whose `original` does not occur in the source
    get sorted to the tail with a sentinel key so preflight's NOT FOUND
    branch reports them last.
    """
    keyed = []
    for i, sug in enumerate(suggestions):
        f, _ = locate(src, sug["original"], 0)
        key = f if f >= 0 else float("inf")
        keyed.append((key, i, sug))
    keyed.sort()
    return [t[2] for t in keyed]


def build(suggestions_path, out_path=None, source_override=None):
    data = json.loads(Path(suggestions_path).read_text(encoding="utf-8"))
    suggestions = data.get("suggestions", [])

    errs = []
    for k, s in enumerate(suggestions):
        if not s.get("original"):
            errs.append("suggestion #%d: missing/empty 'original'" % (k + 1))
        if "replacement" not in s:
            errs.append("suggestion #%d: missing 'replacement'" % (k + 1))
        if s.get("kind") not in KINDS:
            errs.append("suggestion #%d: bad kind %r" % (k + 1, s.get("kind")))
        if s.get("sev") not in SEVS:
            errs.append("suggestion #%d: bad sev %r" % (k + 1, s.get("sev")))
    if errs:
        sys.stderr.write("Invalid suggestions.json:\n  " + "\n  ".join(errs) + "\n")
        return 2

    source_path = source_override or data["source_path"]
    src = Path(source_path).read_text(encoding="utf-8")

    # Auto-sort suggestions by source position so the agent does not have to
    # maintain document order manually. The forward-cursor algorithm below is
    # unchanged — it just sees a pre-sorted list. Stable sort preserves the
    # agent's authored order on ties; preflight catches any resulting overlap.
    suggestions = _sort_by_source(suggestions, src)

    # Ambiguity guard: a tiny original (<=4 chars) is prone to colliding with
    # other occurrences — often as a substring inside a larger word — so the
    # forward-only cursor could silently anchor it to the wrong spot. Reject it
    # loudly unless it is unique (or matched exactly as many times as quoted).
    quoted = Counter(s["original"] for s in suggestions)
    for k, s in enumerate(suggestions):
        o = s["original"]
        occ = src.count(o)
        if len(o.strip()) <= 4 and occ > quoted[o]:
            sys.stderr.write(
                "ERROR: suggestion #%d 'original' %r is too short to place "
                "unambiguously (it occurs %d times in the source but is quoted "
                "%d time(s)).\nLengthen it to a unique multi-word span that "
                "includes surrounding text, then re-run.\n"
                % (k + 1, o, occ, quoted[o])
            )
            return 1

    ok, pre_errs, _spans = preflight(suggestions, src)
    if not ok:
        sys.stderr.write(
            "ERROR: %d suggestion(s) failed pre-flight checks.\n"
            "Whitespace, curly quotes (’ → '), and en-/em-dashes (– — → -) "
            "are normalised automatically — these errors are about wording, "
            "ordering, or overlapping spans, NOT punctuation.\n\n"
            % len(pre_errs)
        )
        sys.stderr.write("\n\n".join(pre_errs) + "\n")
        return 1

    raw_blocks = parse_blocks(src)
    id_counter = [1]
    next_idx = 0
    out_blocks = []
    for b in raw_blocks:
        if b["type"] == "heading":
            out_blocks.append({"type": "heading", "level": b["level"], "text": b["text"]})
        elif b["type"] == "verbatim":
            out_blocks.append({"type": "verbatim", "markdown": b["markdown"]})
        else:
            segs, next_idx = segment_paragraph(b["raw"], suggestions, next_idx, id_counter)
            out_blocks.append({"type": "paragraph", "segments": segs})

    if next_idx < len(suggestions):
        report_placement_failures(suggestions, next_idx, raw_blocks, src)
        return 1

    document = {
        "title": data.get("title", "Writing Review"),
        "source_path": str(Path(source_path).resolve()),
        "reviewer": data.get("reviewer", "Writing Review"),
        "generated_at": data.get("generated_at", ""),
        "blocks": out_blocks,
    }
    out = Path(out_path) if out_path else Path(suggestions_path).with_name("document.json")
    out.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    placed = sum(1 for b in out_blocks if b["type"] == "paragraph"
                 for s in b["segments"] if s["type"] == "suggestion")
    print("Wrote %s — %d blocks, %d suggestions placed." % (out, len(out_blocks), placed))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suggestions", required=True)
    ap.add_argument("--out")
    ap.add_argument("--source")
    args = ap.parse_args()
    return build(args.suggestions, args.out, args.source)


if __name__ == "__main__":
    sys.exit(main())
