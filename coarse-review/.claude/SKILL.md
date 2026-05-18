---
name: coarse-review
description: >
  Produce a rigorous academic peer review of a research paper, manuscript, or preprint.
  Supports markdown (.md), text (.txt), LaTeX (.tex), DOCX, HTML, EPUB, and PDF formats.
  For PDF inputs, uses PyMuPDF (free, local extraction — no API needed).
  Use when the user asks to review, critique, referee, or provide feedback on an academic paper.
  Also use when the user uploads or references a PDF file that the model cannot read directly
  (e.g., "[PDF] ERROR: Cannot read..." or "I uploaded a PDF"). In those cases, ask the user
  for the file path and proceed with extraction.
  Do NOT use for code review, blog posts, or non-academic documents.
  Make sure to use this skill whenever the user mentions paper review, manuscript critique,
  academic feedback, preprint evaluation, or referee report — even if they don't explicitly
  ask for a 'peer review'.
allowed-tools: Bash, Read, Write, Glob, Grep
argument-hint: <paper-path>
---

# coarse-review

Rigorous academic paper review using bundled Python scripts for structure parsing,
quote verification, and format extraction — combined with parallel agent review for
LLM reasoning. No API keys needed for text/markdown inputs.

## How It Works

```
1. Extract    → Convert input to markdown (scripts/extract_text.py)
2. Parse      → Split into sections, classify types (scripts/parse_paper.py)
3. Parallel   → Overview + per-section reviews (native agents)
4. Verify     → Confirm quotes are real (scripts/verify_quotes.py)
5. Editorial  → Filter duplicates, rank by severity (agent)
6. Render     → Write structured markdown review
```

## Prerequisites

- **Python 3** (for bundled scripts; any version works)
- **For PDF inputs**: PyMuPDF is installed automatically when needed (free, local, no API)
- **For DOCX/HTML/EPUB**: Optional packages (`pip install mammoth markdownify ebooklib`)

## Handling Direct PDF Uploads

If the user uploaded a PDF file directly and the model reports that it cannot read it (e.g., "[PDF] ERROR: Cannot read..."), the skill has been invoked because the description explicitly covers this scenario.

In this case:
1. Acknowledge the upload failure: "I see you uploaded a PDF, but I can't read it directly through the chat interface."
2. Ask the user for the file path: "Please provide the full file path (e.g., `/Users/arthur/papers/my_paper.pdf`) so I can extract and review it."
3. Wait for the user to provide the path
4. Proceed to Step 1 below with the provided path

**Do not** attempt to read the PDF directly from the upload — the model does not support PDF input. Always use the extraction script.

## Step 1: Load Paper

Get the paper path from the user argument. If not provided, ask for it.

```bash
ls -lh "<paper_path>"
```

If the file does not exist, ask for the correct path.

For any file (.pdf, .docx, .html, .epub), use the bundled extractor:

```bash
python3 <skill_dir>/scripts/extract_text.py "<input_path>" "<output.md>"
```

For .md, .txt, .tex files, read directly.

## Step 2: Parse Structure

Run the bundled structure parser to extract title, abstract, sections, claims, and math content:

```bash
python3 <skill_dir>/scripts/parse_paper.py "<paper_path>" > /tmp/paper_structure.json
```

Read the JSON output to get:
- **title**: Paper title
- **abstract**: Abstract text
- **domain**: Inferred academic domain (heuristic)
- **document_form**: manuscript / outline / draft / notes
- **sections**: List of sections with title, type, text, claims, definitions, math_content

**If parsing fails** (empty sections, unusual formatting), read the file manually and identify sections by headings.

## Step 3: Launch Parallel Review Agents

**CRITICAL**: Emit ALL agent calls in a SINGLE message to run in parallel.

### Platform Detection

Determine which platform you're running on:
- **Claude Code**: Use `Agent` tool with `subagent_type="general-purpose"` and `run_in_background=true`
- **OpenCode**: Use `task` with `category="deep"` and `run_in_background=true`

### Agent A: Overview Review

**Claude Code:**
```
description: "Review paper overview"
subagent_type: "general-purpose"
run_in_background: true
prompt: |
  You are an expert peer reviewer. Review this academic paper and provide
  4-6 high-level macro issues.

  PAPER TITLE: <title>
  ABSTRACT: <abstract>
  FULL PAPER TEXT:
  <entire paper text>

  For each issue, provide:
  1. A concise title (5-8 words)
  2. A detailed paragraph explaining the issue, its significance, and what the authors should do

  Focus on: conceptual gaps, methodological concerns, missing literature connections, structural problems, unsupported claims.
  Write as a constructive but direct colleague. Cite section names. Do NOT use generic phrases like "further research is needed."

  Return as:
  ### Issue N: <title>
  <detailed paragraph>
```

**OpenCode:**
```
task(category="deep", load_skills=[], run_in_background=true, prompt="""
You are an expert peer reviewer. Review this academic paper and provide 4-6 high-level macro issues.

TITLE: <title>
ABSTRACT: <abstract>
FULL TEXT:
<paper_text>

For each issue, provide:
1. A concise title (5-8 words)
2. A detailed paragraph explaining the issue, its significance, and what the authors should do

Focus on: conceptual gaps, methodological concerns, missing literature connections, structural problems, unsupported claims.
Write as a constructive but direct colleague. Cite section names. Do NOT use generic phrases like "further research is needed."

Return as:
### Issue N: <title>
<detailed paragraph>
""")
```

### Agent B: Per-Section Reviews

For EACH major section (INTRODUCTION, METHODOLOGY, RESULTS, DISCUSSION, CONCLUSION), spawn one agent. Skip ABSTRACT, REFERENCES, APPENDIX unless substantive.

**Claude Code:**
```
description: "Review <section_title> section"
subagent_type: "general-purpose"
run_in_background: true
prompt: |
  You are an expert peer reviewer. Review this specific section.

  PAPER TITLE: <title>
  ABSTRACT: <abstract>
  SECTION TITLE: <section_title>
  SECTION TYPE: <section_type>
  SECTION TEXT:
  <section_text>

  Provide 3-8 detailed comments. For each:
  1. **Quote**: Verbatim quote from the section (1-3 sentences)
  2. **Feedback**: Detailed, actionable feedback (2-4 sentences)
  3. **Confidence**: high/medium/low
  4. **Type**: error/gap/clarity/strength

  Guidelines:
  - Only flag genuine issues. If you resolve your own concern, do NOT include it
  - Cite specific claims, equations, tables, or assumptions
  - For math-heavy sections, check derivations and proof logic
  - For methodology: check assumptions, identification, data quality, robustness
  - For results: check interpretation, significance, omitted analyses
  - For discussion: check whether claims are supported by results

  Return as:
  ### Comment N
  **Quote**: "..."
  **Feedback**: ...
  **Confidence**: high/medium/low
  **Type**: error/gap/clarity/strength
```

**OpenCode:**
```
task(category="deep", load_skills=[], run_in_background=true, prompt="""
You are an expert peer reviewer. Review this specific section.

PAPER TITLE: <title>
ABSTRACT: <abstract>
SECTION TITLE: <section_title>
SECTION TYPE: <section_type>
SECTION TEXT:
<section_text>

Provide 3-8 detailed comments. For each:
1. **Quote**: Verbatim quote from the section (1-3 sentences)
2. **Feedback**: Detailed, actionable feedback (2-4 sentences)
3. **Confidence**: high/medium/low
4. **Type**: error/gap/clarity/strength

Return as:
### Comment N
**Quote**: "..."
**Feedback**: ...
**Confidence**: high/medium/low
**Type**: error/gap/clarity/strength
""")
```

### Agent C: Cross-Section Consistency

ONLY if the paper has both RESULTS and DISCUSSION sections:

**Claude Code:**
```
description: "Check cross-section consistency"
subagent_type: "general-purpose"
run_in_background: true
prompt: |
  You are checking whether Discussion/Conclusion is consistent with Results.

  PAPER TITLE: <title>
  RESULTS SECTION:
  <results_text>
  DISCUSSION/CONCLUSION SECTION:
  <discussion_text>

  Identify claims in Discussion that:
  1. Are NOT supported by Results
  2. Overstate the findings
  3. Ignore important caveats
  4. Make causal claims without proper identification

  Return 0-4 comments in the same format as section reviews.
```

**OpenCode:**
```
task(category="deep", load_skills=[], run_in_background=true, prompt="""
You are checking whether Discussion/Conclusion is consistent with Results.

PAPER TITLE: <title>
RESULTS SECTION:
<results_text>
DISCUSSION/CONCLUSION SECTION:
<discussion_text>

Identify claims in Discussion that:
1. Are NOT supported by Results
2. Overstate the findings
3. Ignore important caveats
4. Make causal claims without proper identification

Return 0-4 comments in the same format as section reviews.
""")
```

## Step 4: Collect Results

Wait for all background agents to complete.

**Claude Code**: Use `TaskOutput` tool to retrieve each result.
**OpenCode**: Read outputs from background tasks.

Store all comments in a structured list.

## Step 5: Verify Quotes

Save comments to a JSON file and run the bundled quote verifier:

```bash
cat > /tmp/comments.json << 'EOF'
[<array of comment objects with number, title, quote, feedback, confidence, type>]
EOF

python3 <skill_dir>/scripts/verify_quotes.py "<paper_path>" /tmp/comments.json > /tmp/verified_comments.json
```

Read the verified output. Comments with quotes that couldn't be verified are dropped.

## Step 6: Editorial Pass

Run a single agent to filter, deduplicate, and rank verified comments:

**Claude Code:**
```
description: "Editorial filter"
subagent_type: "general-purpose"
run_in_background: false
prompt: |
  You are an editorial filter for peer review comments. Deduplicate, rank, and filter.

  PAPER TITLE: <title>
  ABSTRACT: <abstract>

  COLLECTED COMMENTS:
  <all verified comments>

  Editorial rules:
  1. Remove duplicates: keep the better one (more specific, better quote)
  2. Remove contradictions: flag both as low-confidence or remove the less specific
  3. Remove false positives: drop comments that state a concern and then dismiss it
  4. Remove generic praise: keep only substantive critical feedback
  5. Prioritize by severity: high-confidence, actionable comments first
  6. Ensure coverage: keep at least one comment per major section

  Return as:
  ### Comment N (renumbered)
  **Quote**: "..."
  **Feedback**: ...
  **Confidence**: high/medium/low
  **Type**: error/gap/clarity/strength
```

**OpenCode:**
```
task(category="deep", load_skills=[], run_in_background=false, prompt="""
You are an editorial filter for peer review comments. Deduplicate, rank, and filter.

PAPER TITLE: <title>
ABSTRACT: <abstract>

COLLECTED COMMENTS:
<all verified comments>

Editorial rules:
1. Remove duplicates: keep the better one
2. Remove contradictions: flag both as low-confidence or remove
3. Remove false positives: drop comments that state a concern and then answer it
4. Remove generic praise: keep only substantive critical feedback
5. Prioritize: high-confidence, actionable comments first
6. Ensure coverage: keep at least one comment per major section

Return as:
### Comment N (renumbered)
**Quote**: "..."
**Feedback**: ...
**Confidence**: high/medium/low
**Type**: error/gap/clarity/strength
""")
```

## Step 7: Render Final Review

Write the final review to a markdown file in the current working directory:

```markdown
# Peer Review: <Paper Title>

**Date**: <YYYY-MM-DD>
**Reviewer**: AI Peer Review (coarse)
**Format**: <original format>
**Domain**: <inferred domain>

---

## Overall Feedback

<overview issues from Agent A>

---

## Detailed Comments (<N>)

<all filtered and renumbered comments>

---

## Summary

<2-4 sentence synthesis: main strengths and weaknesses>

**Recommendation**: <accept / minor revisions / major revisions / reject>
```

Save as `paper_review.md` in the current working directory (or next to the input file).

## Step 8: Report to User

Show the user:
1. **Output path**: Full path to the written file
2. **Comment count**: Total number of detailed comments after verification and filtering
3. **Verified quotes**: How many quotes were exact vs fuzzy-corrected vs dropped
4. **Top issues**: The 2-3 most important macro issues
5. **Recommendation**: accept / minor revisions / major revisions / reject
6. **Coverage gaps**: Any major section that received no comments

Example:
> Review complete! Output written to `paper_review.md`
>
> **Recommendation**: Major revisions
> **Comments**: 18 detailed comments (22 generated, 4 dropped for unverified quotes)
> **Quote verification**: 14 exact, 3 fuzzy-corrected, 4 dropped
>
> **Top issues**:
> 1. The identification strategy relies on an untestable exclusion restriction (Section 3)
> 2. Results overstate causal claims given the observational design (Section 5)
> 3. Missing robustness checks for the main specification (Section 4)

## Notes

- **No API keys needed**: All LLM calls go through your agent subscription
- **Quote verification**: The bundled `verify_quotes.py` catches hallucinated quotes by checking they are actual substrings of the paper text
- **For text/markdown/PDF inputs**: Zero external API calls. PDF extraction uses free PyMuPDF locally.
- **Parallel execution**: Section reviews run in parallel via background agents
- **Cost**: Uses your agent subscription quota only. No per-paper charges
- **Reproducibility**: Results may vary between runs. Save the review output alongside the paper

## Troubleshooting

- **"No sections found"**: The parser may fail on unusual formatting. Check that the paper has clear headings. If the parser fails, manually identify sections by reading the file.
- **"All comments dropped"**: The editorial filter may be too aggressive. Re-run with instructions to be less strict, or skip it and use raw collected comments.
- **"File too large"**: If the paper exceeds ~50 pages or 100KB, individual agents may time out. Split the paper into logical chunks or skip non-critical sections.
