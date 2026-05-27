---
name: html_viewer
description: Share a local HTML file as a live webpage by uploading it to a GitHub Gist and generating a htmlpreview.github.io URL. Use this skill whenever the user wants to preview, share, publish, or view an HTML file in a browser without setting up a web server. Trigger on phrases like "share this HTML", "preview this HTML file", "put this HTML online", "view HTML in browser", or when the user has generated HTML content and wants to make it accessible via a shareable URL.
---

# HTML Viewer

Quickly turn any local HTML file into a shareable live webpage using GitHub Gist + htmlpreview.github.io.

## Important Limitations

- **External assets won't load**: If the HTML references local CSS, JavaScript, images, or other files via relative paths (`src="style.css"`, `href="./script.js"`), those assets will not render in the preview. Only self-contained HTML (all styles/scripts embedded inline) will display correctly.
- **One file at a time**: This workflow uploads a single HTML file to one gist. For multi-file websites, this approach will not work.
- **Public gists**: The created gist is public and searchable. Do not use this for sensitive or private content.

## Prerequisites

Before proceeding, verify all of the following. If any check fails, stop and report the issue to the user:

1. **GitHub CLI installed**: Run `which gh` or `gh --version`. If missing, tell the user to install it from https://cli.github.com/
2. **Authenticated with GitHub**: Run `gh auth status`. If not logged in, tell the user to run `gh auth login` first.
3. **HTML file exists**: Confirm the file path provided by the user points to an existing file.
4. **File is HTML**: Verify the file has a `.html` or `.htm` extension.

## Steps

### 1. Create the GitHub Gist

Run the following command, replacing `<file>` with the HTML file path:

```bash
gh gist create "<file>" --public -d "HTML preview via htmlpreview.github.io"
```

Capture the full output. The last line will be the gist URL, e.g.:

```
https://gist.github.com/username/abc123def456
```

### 2. Construct the Preview URL

From the gist URL, extract:
- `<user>` — the GitHub username in the URL
- `<gist_id>` — the alphanumeric string after the username
- `<filename>` — the original filename (including `.html` extension)

**Parsing tip:** The gist URL format is `https://gist.github.com/<user>/<gist_id>`. Use a robust parsing method (e.g., `awk -F'/' '{print $4}'` for the user, `awk -F'/' '{print $5}'` for the gist ID) rather than simple string splitting, as usernames may contain hyphens.

Build the raw gist URL:

```
https://gist.githubusercontent.com/<user>/<gist_id>/raw/<filename>
```

Then prepend the htmlpreview prefix:

```
https://htmlpreview.github.io/?https://gist.githubusercontent.com/<user>/<gist_id>/raw/<filename>
```

### 3. Present the Result

Print the final URL clearly in the terminal using a format like this:

```
✅ Your HTML file is now live at:

https://htmlpreview.github.io/?https://gist.githubusercontent.com/username/abc123/raw/file.html

Copy and paste this URL to share it. Note: external assets (CSS, JS, images) referenced with relative paths will not load.
```

## Example

**User says:** "I just generated this report.html file, can you put it online so I can share it?"

**You do:**
1. Verify `gh` is installed and authenticated
2. Verify `report.html` exists
3. Run `gh gist create report.html --public -d "HTML preview via htmlpreview.github.io"`
4. Capture output: `https://gist.github.com/johndoe/a1b2c3d4e5f6`
5. Build URL: `https://htmlpreview.github.io/?https://gist.githubusercontent.com/johndoe/a1b2c3d4e5f6/raw/report.html`
6. Print it clearly for the user to copy
