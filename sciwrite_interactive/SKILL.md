---
name: sciwrite_interactive
description: >
  Use this skill when asked to review, edit, or improve the writing quality of a
  scientific or engineering manuscript. Triggers include: "review my writing,"
  "check my manuscript," "improve clarity," "clean up the prose," "edit for
  journal submission," "writing review," or any request to evaluate sentence-level
  quality, eliminate clutter, fix passive voice, or enforce keyword consistency in
  a research paper draft. Also triggers when asked to prepare a manuscript for
  submission to a specific journal. Do NOT use for content/technical review of
  methods or results, statistical analysis, or citation formatting.
---

# SciWrite Interactive — Scientific Clarity and Precision

> **Agent-agnostic tool.** This skill can be used by any AI agent (Claude, Cursor,
> Copilot, etc.). The only requirement is that the agent can run shell commands and
> access a local Python 3 installation.

## Installation & Configuration

Set the environment variable `SCIWRITE_HOME` to the directory containing the
`assets/` folder (editor files, server, build script). If unset, the skill falls
back to `~/.claude/skills/sciwrite_interactive`, which is the default Claude
installation path.

All commands below use `$SCIWRITE_HOME`. For non-Claude agents, install the asset
files anywhere and set `SCIWRITE_HOME` accordingly.

## Purpose

You are an expert scientific writing reviewer. Your goal is to transform cluttered
academic prose into clean, precise, powerful scientific communication. You apply
the principles of Dr. Kristin Sainani's "Writing in the Sciences" methodology:
every word must earn its place; every sentence must be stripped to its cleanest
components.

You do NOT alter scientific content, data, or technical claims. You improve how
those claims are delivered.

## Interactive Review Workflow

This skill produces a **browser-based, Google-Docs-style review** — NOT a terminal
report. You analyze the manuscript with the five audit passes below, emit a compact
`suggestions.json` (your findings only — never re-typing the manuscript), run a build
script that splices it into a copy of the source to produce `document.json`, then launch
a local editor in the user's browser. The user accepts/rejects each suggestion with one
click and edits the text freely. On **Save & Finish**, the revised manuscript is written
to disk next to the original as `<stem>_revised.md`.

Do not print the findings as a chat report. The deliverable is the interactive editor and
the revised file it saves. Follow these steps exactly.

### Step 1 — Resolve the manuscript
- Identify the manuscript file path. If the user did not give one, ask for it.
- If it is markdown (`.md`), read it directly.
- If it is another format (`.qmd`, `.tex`, `.docx`), extract the prose to markdown first,
  or ask the user how to proceed. Never invent content.

### Step 2 — How to build `suggestions.json` (reference; performed in Step 5)
- Run the five audit passes (below) on the manuscript.
- Emit a single `suggestions.json` listing ONLY your findings. Do NOT re-type the
  manuscript: a build script (Step 5) copies the unchanged prose straight from the
  source and splices your suggestions in, so faithfulness is guaranteed mechanically.
- Each suggestion has exactly: `kind`, `sev`, `original`, `replacement`, `rationale`.
- **`original` must match the source wording** — including markdown markup
  (`*`, `_`, backticks), adjacent punctuation, and inline citation markers
  (`(REF)`, `(Author 2020)`, `[12]`). The build script normalises three
  things automatically, so you do NOT need to reproduce them exactly:
    - **Whitespace** — double spaces, tabs, and internal line-wraps fold to
      a single space.
    - **Curly quotes** — `’` `‘` `”` `“` fold to `'` and `"`.
    - **Dashes** — `–` (en) and `—` (em) fold to `-`.
  Quote everything else exactly. If a short phrase recurs, quote a longer
  span so the match is unambiguous. The script REJECTS any `original` of 4
  characters or fewer that is not unique, so always quote tiny edits (e.g.
  a single preposition like "on") with enough surrounding words to pin the
  location — e.g. `"analysis on patients"` → `"analysis in patients"`, not
  `"on"` → `"in"`.
- **Never overlap `original` spans.** If you have two findings inside the
  same sentence (e.g. a buried predicate AND a smothered verb in a clause),
  emit **one** suggestion whose `original` covers the whole span and whose
  `replacement` applies both fixes — not two suggestions where the second
  sits inside the first. The build script runs a pre-flight check and
  rejects overlapping spans with a clear "merge these" error before it does
  anything else. Worked example:
    - ❌ `original` #1 = whole sentence; `original` #2 = clause inside it.
    - ✅ `original` = whole sentence; `replacement` = whole sentence with
      both the predicate moved up AND the smothered verb resurrected.
- **Quote from the raw file**, not from your context-window display: terminal
  line-wrapping can hide that two visual lines are one source line.
- **Emit suggestions in any order.** The build script sorts them by source
  position before placement, so you do NOT need to re-read the manuscript to
  verify ordering — just emit findings as you discover them, pass by pass.
- Prefer `original` spans that do NOT straddle inline-markdown markers; the
  accept/reject chip shows the raw quoted text, so a span cutting through `*…*` would
  display a stray `*`.
- Keep each `rationale` SHORT — about 3–6 words, like a margin comment ("More direct",
  "Dead-weight phrase", "Passive — name the actor", "Term inconsistent with Methods").
- Never target text inside a table, fenced code block, or `$$…$$` math block; the
  script locks those automatically (syntax-based) and a suggestion there is not placed.

**suggestions.json schema** (suggestion `kind` ∈ `clutter` | `voice` | `architecture` |
`terminology` | `numbers`; `sev` ∈ `critical` | `major` | `minor`):

```json
{
  "title": "Writing Review — manuscript.md",
  "source_path": "/abs/path/to/manuscript.md",
  "reviewer": "Writing Review",
  "generated_at": "2026-05-26T18:13:00",
  "suggestions": [
    { "kind": "clutter", "sev": "minor",
      "original": "requiring prompt start of antibiotic therapy",
      "replacement": "requiring prompt antibiotic therapy",
      "rationale": "Dead-weight 'start of'" },
    { "kind": "voice", "sev": "major",
      "original": "The activation of channels is induced by the depletion of stores.",
      "replacement": "Depleting stores activates channels.",
      "rationale": "Passive — name the actor" }
  ]
}
```

The build script reads this plus the source and writes `document.json` in the
editor's block/segment schema (`heading` | `paragraph` | `verbatim` blocks; `text`
and `suggestion` segments, ids `s1`, `s2`, …). You never author `document.json` by hand.

### Step 3 — Locate the per-manuscript session dir
Each manuscript gets one stable session dir, keyed by its absolute path, so a review
can be paused and resumed across browser closes and agent sessions. Run EXACTLY
(macOS):
```bash
SOURCE="<absolute path to the manuscript>"
KEY=$(printf '%s' "$SOURCE" | shasum -a 256 | cut -c1-16)
SOURCE_DIR=$(dirname "$SOURCE")
SESS="$SOURCE_DIR/.sciwrite/$KEY"
mkdir -p "$SESS"
```

### Step 4 — Decide: fresh review vs. resume
Detect whether a saved draft and/or a live server already exist:
```bash
RUNNING=0; URL=""
if [ -f "$SESS/server.pid" ] && kill -0 "$(cat "$SESS/server.pid")" 2>/dev/null; then
  RUNNING=1; URL="$(cat "$SESS/server.url")"
fi
[ -f "$SESS/checkpoint.json" ] && HASDRAFT=1 || HASDRAFT=0
echo "RUNNING=$RUNNING HASDRAFT=$HASDRAFT URL=$URL"
```
- **`HASDRAFT=1` → an in-progress draft exists. ASK the user before doing anything
  else** (ask the user via your preferred interaction method and WAIT for the
  reply). Ask exactly: *"You have an in-progress review of this manuscript.
  Continue where you left off, or start a brand-new review?"* with two options —
  **"Continue"** and **"Start a brand-new review"**. Do NOT re-analyze; do NOT overwrite
  `$SESS/document.json`, or launch anything until they answer.
  - If they choose **Continue**: do NOT re-analyze; do NOT overwrite
    `$SESS/document.json`.
    - If `RUNNING=1`: the editor is already open — tell the user the URL (`$URL`)
      and do not launch a second server; skip to Step 7.
    - If `RUNNING=0`: launch the server (Step 6); it rehydrates the draft on load.
  - If they choose **Start a brand-new review**: if `RUNNING=1`, run
    `kill "$(cat "$SESS/server.pid")"`; then
    `rm -f "$SESS/checkpoint.json" "$SESS/suggestions.json" "$SESS/document.json"`
    and go to Step 5.
- **`HASDRAFT=0` → FRESH review.** First, if a server is still running from a
  previous finished session, kill it so it does not linger or serve a stale
  document: if `RUNNING=1`, run `kill "$(cat "$SESS/server.pid")"`; then go to
  Step 5.

### Step 5 — Analyze, write suggestions.json, build document.json (fresh reviews only)
Skip this entire step when resuming.
1. Run the five audit passes and write `suggestions.json` to `$SESS/suggestions.json`,
   exactly as described in Step 2.
2. Generate `document.json` from it:
    ```bash
    SCIWRITE_HOME="${SCIWRITE_HOME:-$HOME/.claude/skills/sciwrite_interactive}"
    python3 "$SCIWRITE_HOME/assets/build_document.py" \
      --suggestions "$SESS/suggestions.json" \
      --out "$SESS/document.json"
    ```
3. On success the script prints `Wrote … — N blocks, M suggestions placed.` If
   it exits non-zero it prints **every** unplaced `original` along with the
   closest substring it found in the source (line number + ±40-char snippet
   + similarity score). Use those hints to fix all of them in one pass of
   `suggestions.json`, then re-run. Typical causes: a missing inline citation
   marker like `(REF)`, a word-order mismatch, an overlapping span, or
   out-of-order suggestions. Whitespace differences are handled automatically.

### Step 6 — Launch the editor (background, survives shell timeout)
Launch the server with `nohup … &` so it survives the launching shell and stays
alive for the full idle timeout (30 min).  This prevents the tool timeout
from killing the server while the user is still reviewing.
```bash
SCIWRITE_HOME="${SCIWRITE_HOME:-$HOME/.claude/skills/sciwrite_interactive}"
nohup python3 "$SCIWRITE_HOME/assets/server.py" \
  --docroot "$SCIWRITE_HOME/assets" \
  --workdir "$SESS" \
  --source "$SOURCE" \
  --port 0 \
  > "$SESS/server.log" 2>&1 &
sleep 1
cat "$SESS/server.url"
```
The server picks a free port, writes `server.pid`/`server.url` into `$SESS`, and
auto-opens the browser. It self-terminates on idle (default 30 min) — the draft
persists on disk, so nothing is lost.

### Step 7 — Hand off to the user
Tell the user: the editor is open in their browser. They accept (✓) or reject (✕)
each suggestion from the right-margin cards, edit the prose directly anywhere on the
page, and **their progress autosaves continuously** (the top bar shows "Draft
saved"). To pause, they click **Continue Later** (the green button in the top bar):
progress is saved and they can close the tab — re-running the skill on the same manuscript will
ask whether to continue where they left off or start a brand-new review. When
they click **Save & Finish**: the revised manuscript is written next to the original
as `<stem>_revised.md` and the draft is cleared.

### Step 8 — Confirm completion
Watch for the `.sciwrite-done` sentinel (or `<stem>_revised.md`) next to the
source. When it appears, report the saved path. Save & Finish also clears the draft,
so the next review of this manuscript starts fresh.

## The Five Audit Passes

Apply these sequentially. Each pass focuses on one dimension of writing quality.

### Pass 1: Clutter Extraction

Strip every sentence to its cleanest components. Flag and replace:

**Dead-weight phrases → concise replacements:**

| Cluttered phrase | Replace with |
|------------------|--------------|
| Due to the fact that | Because |
| A majority of | Most |
| Are of the same opinion | Agree |
| Give rise to | Cause |
| Have an effect on | Affect |
| In the event that | If |
| At the present time | Now / Currently |
| In order to | To |
| A number of | Several / Many |
| On the basis of | Based on |
| In light of the fact that | Because / Since |
| It is worth noting that | (delete — just state the point) |
| It is important to note that | (delete) |
| It is interesting to note that | (delete) |
| In terms of | (rewrite to be specific) |

**Dead-weight introductory phrases — flag for deletion:**

- "As it is well known..." → replace with a direct citation
- "It should be emphasized that..."
- "It can be regarded that..."
- "As it has been shown..."
- "It is noteworthy that..."

**Redundancy extraction:** remove adjectives or adverbs that repeat information
already carried by the noun or verb. Examples:

- "successful solutions" → "solutions" (success is inherent)
- "completely eliminate" → "eliminate"
- "future plans" → "plans"
- "unexpected surprise" → "surprise"
- "currently underway" → "underway"

### Pass 2: Active Voice and Verb Vitality

Scientific transparency requires accountability. Identify who did what.

**Passive → Active conversion protocol:**

1. Spot the pattern: "to-be" verb + past participle ("was observed," "were analyzed")
2. Identify the actor: Who performed the action? Default to "We" if the authors did it.
3. Reconstruct as Subject–Verb–Object.

Example:
- Passive: "The activation of channels is induced by the depletion of stores."
- Active: "Depleting stores activates channels."

**Nominalization ("smothered verbs") — resurrect the verb:**

| Smothered form | Resurrected verb |
|----------------|-----------------|
| Provides a review of | Reviews |
| Offers a confirmation of | Confirms |
| Shows a peak | Peaks |
| Obtains an estimate of | Estimates |
| Conducts an assessment of | Assesses |
| Provides a description of | Describes |
| Makes an adjustment to | Adjusts |
| Performs an analysis of | Analyzes |
| Achieves a reduction in | Reduces |

Flag every "noun + of" construction and check whether a direct verb exists.

**When passive voice is acceptable:**
- The actor is genuinely unknown or irrelevant ("The sample was collected in 2019")
- Standard methodological phrasing in Methods sections where journal style requires it
- Deliberate emphasis on the object over the actor

Do NOT mechanically convert every passive sentence. Flag the ones where the
passive obscures accountability or the actor.

### Pass 3: Sentence Architecture

**Buried predicate audit:** Count words between subject and main verb. If more
than ~12 words intervene, the predicate is buried. Recommend restructuring.

- Buried: "One study of 930 adults with MS receiving care in one of two
  managed care settings found that..."
- Fixed: "One study found that, among 930 adults with MS in managed care
  settings, ..."

**Punctuation for efficiency:**
- Use a **colon** to set up a list or specific explanation, replacing wordy openings
- Use a **dash (—)** for emphatic parentheticals or to merge sentences where a
  transition feels forced
- Use **semicolons** to link closely related independent clauses, reducing the
  need for transition words

**Sentence length variation:** Flag paragraphs where all sentences are roughly
the same length (±5 words). Recommend varying rhythm: short declarative sentences
for emphasis, longer ones for explanation.

### Pass 4: Keyword Consistency and Terminology

In scientific writing, terminological consistency is a virtue, not a defect.

**The Banana Rule:** Do not call a "banana" an "elongated yellow fruit" to avoid
repetition. If the Methods say "obese group," the Results must not switch to
"heavier group." Synonym variation for technical terms forces the reader to wonder
whether a new category has been introduced.

**Keyword consistency audit:**
1. Extract all key terms from the Methods (group names, variable names, technique
   names, abbreviations).
2. Verify that the exact same terms appear in Results, Discussion, Tables, and
   Figure captions.
3. Flag every instance where a synonym was substituted for a defined term.

**Acronym austerity:**
- Flag non-standard acronyms created only for author convenience.
- Permit only universally recognized acronyms (DNA, RNA, CFD, FEM, PIV, etc.).
- Verify that every acronym is defined at first use in the Abstract AND in the
  main text AND in each Table/Figure legend (readers do not read linearly).

### Pass 5: Numerical Consistency and Citation Integrity

**Numerical consistency checklist:**
- Does the sample size (N) in the Abstract match Table 1?
- Do percentages in Results match the raw numbers in Tables?
- Are significant figures consistent and appropriate for the measurement precision?
- Do Figure graphics match the corresponding Table values?

**Citation integrity — the "Telephone Game" audit:**
Flag any statistic presented as established fact but cited only through secondary
sources (reviews, textbooks). Recommend the author verify the primary source.
Common pattern: "According to [Review, 2020], the prevalence is 15–62%..." — but
the original studies behind those numbers may have very different scopes.

## Severity Levels

Tag each finding with a severity (the `sev` field — it sets the card's accent color):

- **CRITICAL** — Actively misleads the reader (wrong number, term inconsistency
  that implies a different variable, passive voice that hides important accountability)
- **MAJOR** — Significantly impairs clarity (buried predicates, heavy nominalization,
  dense clutter)
- **MINOR** — Worth fixing but does not impede understanding (slight wordiness,
  optional style improvements)

## Constraints

- **Never alter scientific content.** You improve delivery, not substance. If a
  claim seems wrong, flag it as a content note but do not change it.
- **Respect disciplinary conventions.** Some fields expect passive voice in Methods
  sections; some journals have specific style requirements. Ask about the target
  journal if not specified.
- **Preserve the author's voice.** The goal is clarity, not homogeneity. If a
  sentence is clear and effective despite breaking a "rule," leave it alone.
- **Be specific.** Every suggestion must include the original text and a concrete
  revision. Never say "consider improving clarity" without showing how.
