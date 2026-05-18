# coarse-review

> **Zero API keys. Zero setup. Just your coding agent subscription.**
>
> Review academic papers using the Claude Code or OpenCode subscription you already have. No OpenRouter. No Anthropic API. No Perplexity. No Python package to install.

A skill for Claude Code and OpenCode that produces rigorous academic peer reviews. Feed it a paper, get a structured markdown review back.

## What Is This?

This is a lightweight fork of [coarse](https://github.com/Davidvandijcke/coarse), a web-based academic paper review tool by David van Dijcke. The original tool requires OpenRouter API keys, a Python package install (`pip install coarse`), and a web backend (Supabase, Modal workers, subscription management).

**This fork reimplements the same peer review logic as a native skill** for Claude Code and OpenCode, leveraging your existing agent subscription instead of external APIs. It replaces the original's 11,000-line Python package and web infrastructure with ~600 lines of bundled scripts plus native agent parallelization.

## Quick Start

### Easiest Way: Let Your Agent Install It (Recommended)

Don't want to deal with terminal commands? Just copy and paste this prompt into your agent. It will download and install the skill for you.

```
Please install the coarse-review skill for me. Download the install script from https://raw.githubusercontent.com/arthur-albuquerque/coarse-skills/dev/install.sh and run it so I can use /coarse-review from anywhere.
```

Your agent will handle the entire setup. Once it's done, skip to Step 2 below.

---

## Step-by-Step: Your First Review

### 1. Install the skill (one time only)

Use the "Easiest Way" above.

### 2. Go to your paper's folder

Open your terminal and navigate to wherever your paper file is saved. For example:

```bash
cd ~/Documents/papers
```

Or if it's in your Downloads folder:

```bash
cd ~/Downloads
```

### 3. Start your coding agent

Make sure you start the agent from inside the folder that contains your paper. The review will be saved in this same folder.

**For Claude Code:**
```bash
claude
```

**For OpenCode:**
```bash
opencode
```

### 4. Run the review

Once you see the agent's prompt, type:

```bash
/coarse-review ./my_paper.md
```

Replace `my_paper.md` with your actual filename. For example:
- `./manuscript.tex`
- `./draft.docx`
- `./paper.txt`
- `./paper.pdf` (PDFs work automatically — see below)

You can also use the full file path if you prefer:

```bash
/coarse-review ~/Documents/papers/my_paper.md
```

**What happens next:** The skill takes 2-5 minutes to review your paper. When it's done, you'll find a new file called `paper_review.md` in your current folder with the full review.

## What You Need

| | Claude Code | OpenCode |
|---|---|---|
| **Subscription** | Claude Code | OpenCode |
| **Paper formats** | `.md` `.txt` `.tex` `.docx` `.html` `.epub` `.pdf` | same |
| **PDF extraction** | Automatic via PyMuPDF (free, local, no API) | same |
| **API keys** | None | None |
| **Python** | 3.x (for bundled scripts) | 3.x (for bundled scripts) |

## About PDF Support

This skill extracts text from PDFs using **PyMuPDF**, a free and open-source Python library. The extraction happens entirely on your computer:

- **No API calls** — your PDF never leaves your machine
- **No cloud OCR service** — no Google Vision, no AWS Textract, no OpenAI
- **No paid service** — PyMuPDF is free and open-source
- **Local processing** — the PDF is read directly by the Python script
- **Auto-installation** — if PyMuPDF is not installed, the skill installs it automatically when you first review a PDF

### Uploading PDFs Directly in Chat

If you upload a PDF file directly into the chat (drag-and-drop or file picker), the model may report that it cannot read the file. **This is expected** — most coding agents cannot process raw PDFs directly.

When this happens, the skill will detect the upload failure and ask you for the file path. Simply provide the full path (e.g., `/Users/arthur/papers/my_paper.pdf`) and the skill will extract and review it normally.

**Recommended:** Instead of uploading, just type the command with the file path:
```bash
/coarse-review ~/Documents/papers/my_paper.pdf
```

### Alternative: Convert PDFs to Markdown Online

If you prefer not to install anything extra, you can convert your PDF to a markdown file first using a free web tool, then run the review on the markdown file.

**Using datalab.to (free, no signup required):**

1. Go to https://www.datalab.to/playground/documents/new
2. Click **"Choose File"** and upload your PDF
3. Wait a few seconds for the conversion
4. Click **"Download"** to save the `.md` file
5. Move the downloaded `.md` file to the same folder as your paper
6. Run the skill on the markdown file:
   ```bash
   /coarse-review ./your_paper.md
   ```

This approach often produces cleaner markdown (better headings, tables, and math formatting) than automated text extraction, which can improve the quality of the review.

## How It Works

The skill bundles three Python scripts that handle deterministic work, leaving the LLM reasoning to your agent subscription:

1. **Parse** (`scripts/parse_paper.py`) — Split paper into sections, extract claims/definitions, detect math content, classify document form
2. **Verify** (`scripts/verify_quotes.py`) — Confirm every comment quote is an actual substring of the paper (catches hallucinations)
3. **Extract** (`scripts/extract_text.py`) — Convert `.pdf`, `.docx`, `.html`, `.epub`, `.tex` to markdown. PDF extraction uses PyMuPDF locally — no external API, no OCR service, no cloud upload.

Then the skill spawns parallel review agents:
4. **Overview** — High-level macro issues (conceptual gaps, methodological concerns)
5. **Per-section** — Detailed comments per major section (3-8 comments each)
6. **Cross-section** — Consistency check between Results and Discussion
7. **Editorial** — Filter duplicates, rank by severity
8. **Output** — Structured markdown review (`paper_review.md`)

## Example

```bash
/coarse-review ~/papers/diffusion_models.md
# → writes paper_review.md in current directory
```

Output:
- **Overall Feedback**: 4-6 high-level issues
- **Detailed Comments**: 15-30 specific, quoted comments with confidence levels
- **Quote Verification**: Exact matches, fuzzy-corrected quotes, dropped hallucinations
- **Recommendation**: accept / minor revisions / major revisions / reject

## Project Structure

```
coarse-skills/
├── .claude/
│   └── skills/
│       └── coarse-review/
│           ├── SKILL.md              # Claude skill instructions
│           └── scripts/
│               ├── parse_paper.py    # Structure parsing
│               ├── verify_quotes.py  # Quote verification
│               └── extract_text.py   # Format conversion
├── .opencode/
│   └── skills/
│       └── coarse-review/            # Same structure for OpenCode
├── install.sh                        # Global installer
├── LICENSE
└── README.md
```

## Uninstall

```bash
rm -rf ~/.claude/skills/coarse-review
rm -rf ~/.config/opencode/skills/coarse-review
```

## Comparison: This Fork vs. Original coarse

This fork strips away the original's web backend, worker queues, and API infrastructure, replacing them with native agent parallelization. Here's the difference:

| | Original coarse | This skill |
|---|---|---|
| **LLM backend** | OpenRouter API (~$0.25-2.00/review) | Your existing agent subscription |
| **Required keys** | `OPENROUTER_API_KEY` | None |
| **Setup** | 5-10 min | 1 min (OpenCode) / 0 min (Claude Code) |
| **Python package** | 11,000 lines | 3 scripts, ~600 lines |
| **Quote verification** | Yes (Python) | Yes (bundled script) |
| **Parallelism** | Python ThreadPool | Native agent fan-out |

The original `coarse` runs reviews through a web backend with Python ThreadPool workers and OpenRouter API calls. This fork runs reviews through your agent's native parallel subagents, and the bundled scripts handle all deterministic work (parsing, verification, extraction) without any API calls.

## Credits

- **Original tool**: [coarse](https://github.com/Davidvandijcke/coarse) by David van Dijcke — the web-based review system this fork reimplements
- **This fork**: Native skill adaptations for Claude Code and OpenCode by the OpenCode community

MIT License (same as original)
