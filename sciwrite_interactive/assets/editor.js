/* SciWrite Interactive — interactive editor client.
 *
 * Flow: fetch /document.json -> render WYSIWYG prose with inline suggestion
 * "chips" + anchored margin cards -> user accepts/rejects (one click) and
 * edits freely -> Save & Finish serializes the DOM back to markdown and
 * POSTs it to /save (server writes <stem>_revised.md next to the source).
 *
 * The DOM is the single source of truth. Accepting a suggestion replaces its
 * chip with an editable text node of the replacement; rejecting replaces it
 * with the original. Pending chips export as their original text.
 */

const docEl = document.getElementById("doc");
const marginEl = document.getElementById("margin");
const counterEl = document.getElementById("counter");
const saveBtn = document.getElementById("save-btn");
const laterBtn = document.getElementById("later-btn");
const toastEl = document.getElementById("toast");

let MODEL = null;
let REVIEWER = "Writing Review";
let TOTAL = 0;
const anchorTops = {}; // last-known top per suggestion id (px, relative to #margin)
const autosaveEl = document.getElementById("autosave");
let FINISHED = false;

const turndown = new TurndownService({
  headingStyle: "atx",
  bulletListMarker: "-",
  emDelimiter: "*",
  codeBlockStyle: "fenced",
});

/* ---------- Boot ---------- */
function countSuggestions(model) {
  let n = 0;
  (model.blocks || []).forEach((b) => {
    if (b.type === "paragraph") {
      (b.segments || []).forEach((s) => {
        if (s.type === "suggestion") n++;
      });
    }
  });
  return n;
}

// After restoring saved HTML, re-attach the hover listeners that makeChip()
// adds (setting innerHTML drops all JS listeners).
function rewireChips() {
  docEl.querySelectorAll(".chip").forEach((chip) => {
    const id = chip.dataset.id;
    chip.addEventListener("mouseenter", () => setActive(id, true));
    chip.addEventListener("mouseleave", () => setActive(id, false));
  });
}

async function loadDoc() {
  const res = await fetch("/document.json", { cache: "no-store" });
  MODEL = await res.json();
  REVIEWER = MODEL.reviewer || "Writing Review";
  TOTAL = countSuggestions(MODEL);
  document.getElementById("doc-title").textContent = MODEL.title || "Document";
  document.getElementById("reviewer-name").textContent = REVIEWER;

  // Resume an in-progress draft if the server has one; else render fresh.
  let hydrated = false;
  try {
    const ck = await (await fetch("/checkpoint", { cache: "no-store" })).json();
    if (ck && ck.doc_html) {
      docEl.innerHTML = ck.doc_html;
      rewireChips();
      hydrated = true;
    }
  } catch (e) {
    /* no usable draft — fall through to a fresh render */
  }
  if (!hydrated) renderDoc(MODEL);

  renderCards(MODEL);
  updateCounter();
  reflow();
}

/* ---------- Render the document ---------- */
function appendInline(parent, mdText) {
  // Render inline markdown (em/strong/code) and append its nodes.
  const tmp = document.createElement("span");
  tmp.innerHTML = marked.parseInline(mdText);
  while (tmp.firstChild) parent.appendChild(tmp.firstChild);
}

function makeChip(seg) {
  const chip = document.createElement("span");
  chip.className = "chip";
  chip.contentEditable = "false";
  chip.dataset.id = seg.id;
  const ins = document.createElement("span");
  ins.className = "ins";
  ins.textContent = seg.replacement;
  const del = document.createElement("span");
  del.className = "del";
  del.textContent = seg.original;
  chip.appendChild(ins);
  chip.appendChild(del);
  chip.addEventListener("mouseenter", () => setActive(seg.id, true));
  chip.addEventListener("mouseleave", () => setActive(seg.id, false));
  return chip;
}

function renderDoc(model) {
  docEl.innerHTML = "";
  (model.blocks || []).forEach((block) => {
    if (block.type === "heading") {
      const h = document.createElement("h" + (block.level || 1));
      appendInline(h, block.text || "");
      docEl.appendChild(h);
    } else if (block.type === "paragraph") {
      const p = document.createElement("p");
      p.contentEditable = "true";
      (block.segments || []).forEach((seg) => {
        if (seg.type === "text") {
          appendInline(p, seg.text || "");
        } else if (seg.type === "suggestion") {
          p.appendChild(makeChip(seg));
        }
      });
      docEl.appendChild(p);
    } else if (block.type === "verbatim") {
      const div = document.createElement("div");
      div.className = "verbatim";
      div.contentEditable = "false";
      div.dataset.verbatim = "1";
      div.dataset.md = block.markdown || "";
      div.innerHTML = marked.parse(block.markdown || "");
      docEl.appendChild(div);
    }
  });
}

/* ---------- Render margin cards ---------- */
function fmtTime(iso) {
  const d = iso ? new Date(iso) : new Date();
  if (isNaN(d)) return "Today";
  const t = d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  return t + " Today";
}

function truncate(s, n) {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function initial(name) {
  return (name || "?").trim().charAt(0).toUpperCase();
}

function eachSuggestion(model, fn) {
  (model.blocks || []).forEach((b) => {
    if (b.type === "paragraph") {
      (b.segments || []).forEach((s) => {
        if (s.type === "suggestion") fn(s);
      });
    }
  });
}

function renderCards(model) {
  marginEl.innerHTML = "";
  const time = fmtTime(model.generated_at);
  eachSuggestion(model, (seg) => {
    // Skip suggestions already resolved in a restored draft (chip is gone).
    if (!chipById(seg.id)) return;
    const card = document.createElement("div");
    card.className = "card";
    card.dataset.id = seg.id;
    card.dataset.sev = seg.sev || "minor";

    const head = document.createElement("div");
    head.className = "card-head";
    head.innerHTML =
      `<div class="avatar">${initial(REVIEWER)}</div>` +
      `<div class="who"><span class="name">${REVIEWER}</span>` +
      `<span class="time">${time}</span></div>`;
    const actions = document.createElement("div");
    actions.className = "head-actions";
    const acc = document.createElement("button");
    acc.className = "icon-btn accept";
    acc.title = "Accept suggestion";
    acc.textContent = "✓"; // ✓
    acc.addEventListener("click", () => accept(seg.id));
    const rej = document.createElement("button");
    rej.className = "icon-btn reject";
    rej.title = "Reject suggestion";
    rej.textContent = "✕"; // ✕
    rej.addEventListener("click", () => reject(seg.id));
    actions.appendChild(acc);
    actions.appendChild(rej);
    head.appendChild(actions);
    card.appendChild(head);

    const line = document.createElement("div");
    line.className = "replace-line";
    line.innerHTML =
      `Replace: <span class="q">“${truncate(seg.original, 80)}”</span>` +
      ` with <span class="q">“${truncate(seg.replacement, 80)}”</span>`;
    card.appendChild(line);

    if (seg.rationale) {
      const rat = document.createElement("div");
      rat.className = "rationale";
      rat.innerHTML =
        `<div class="avatar">${initial(REVIEWER)}</div>` +
        `<div class="r-body"><div class="r-head">` +
        `<span class="name">${REVIEWER}</span>` +
        `<span class="time">${time}</span>` +
        `<span class="more">⋮</span></div>` +
        `<div class="r-text">${seg.rationale}</div></div>`;
      card.appendChild(rat);
    }

    card.addEventListener("mouseenter", () => setActive(seg.id, true));
    card.addEventListener("mouseleave", () => setActive(seg.id, false));
    marginEl.appendChild(card);
  });
}

/* ---------- Interaction ---------- */
function chipById(id) {
  return docEl.querySelector('.chip[data-id="' + id + '"]');
}
function cardById(id) {
  return marginEl.querySelector('.card[data-id="' + id + '"]');
}

function setActive(id, on) {
  const chip = chipById(id);
  const card = cardById(id);
  if (chip) chip.classList.toggle("active", on);
  if (card) card.classList.toggle("active", on);
}

function resolve(id, useReplacement) {
  const chip = chipById(id);
  if (chip) {
    const text = useReplacement
      ? chip.querySelector(".ins").textContent
      : chip.querySelector(".del").textContent;
    chip.replaceWith(document.createTextNode(text));
  }
  // Remove the card entirely; remaining cards reflow upward into the gap.
  const card = cardById(id);
  if (card) card.remove();
  delete anchorTops[id];
  updateCounter();
  reflow();
  postCheckpoint();
}

function accept(id) {
  resolve(id, true);
}
function reject(id) {
  resolve(id, false);
}

function updateCounter() {
  const remaining = docEl.querySelectorAll(".chip").length;
  const resolved = TOTAL - remaining;
  counterEl.textContent =
    TOTAL + " suggestion" + (TOTAL === 1 ? "" : "s") + " · " + resolved + " resolved";
}

/* ---------- Card positioning (anchor alignment + overlap push-down) ---------- */
function reflow() {
  const marginTop = marginEl.getBoundingClientRect().top;
  const cards = Array.from(marginEl.querySelectorAll(".card"));
  const items = cards.map((card) => {
    const id = card.dataset.id;
    const chip = chipById(id);
    let top;
    if (chip) {
      top = chip.getBoundingClientRect().top - marginTop;
      anchorTops[id] = top;
    } else {
      top = anchorTops[id] != null ? anchorTops[id] : 0;
    }
    return { card, top };
  });
  items.sort((a, b) => a.top - b.top);
  let prevBottom = -Infinity;
  const gap = 12;
  items.forEach(({ card, top }) => {
    const t = Math.max(top, prevBottom + gap);
    card.style.top = t + "px";
    prevBottom = t + card.offsetHeight;
  });
}

let reflowTimer = null;
function scheduleReflow() {
  clearTimeout(reflowTimer);
  reflowTimer = setTimeout(reflow, 120);
}
window.addEventListener("resize", scheduleReflow);
docEl.addEventListener("input", () => {
  scheduleReflow();
  scheduleCheckpoint();
});

/* ---------- Autosave draft (pause/resume support) ---------- */
function setAutosave(msg) {
  if (autosaveEl) autosaveEl.textContent = msg;
}

function checkpointBody() {
  return JSON.stringify({
    doc_html: docEl.innerHTML,
    saved_at: new Date().toISOString(),
  });
}

async function postCheckpoint() {
  if (FINISHED) return;
  setAutosave("Saving…");
  try {
    // keepalive lets the request complete even if the tab is closing, so an
    // accept/reject made right before close still persists.
    await fetch("/checkpoint", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: checkpointBody(),
      keepalive: true,
    });
    setAutosave("Draft saved");
  } catch (e) {
    setAutosave("Draft not saved");
  }
}

// Last-chance flush when the page is hidden or unloaded. sendBeacon is designed
// to deliver during unload, when a normal fetch would be cancelled — without it,
// progress accepted just before closing the tab is lost and the resumed review
// shows every suggestion again.
function flushCheckpoint() {
  if (FINISHED) return;
  try {
    const blob = new Blob([checkpointBody()], { type: "application/json" });
    navigator.sendBeacon("/checkpoint", blob);
  } catch (e) {
    /* best-effort */
  }
}
window.addEventListener("pagehide", flushCheckpoint);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") flushCheckpoint();
});

let checkpointTimer = null;
function scheduleCheckpoint() {
  if (FINISHED) return;
  clearTimeout(checkpointTimer);
  checkpointTimer = setTimeout(postCheckpoint, 800);
}

/* ---------- Export to markdown ---------- */
function serializeMarkdown() {
  const clone = docEl.cloneNode(true);

  // Pending suggestions -> their original text.
  clone.querySelectorAll(".chip").forEach((chip) => {
    const del = chip.querySelector(".del");
    chip.replaceWith(document.createTextNode(del ? del.textContent : ""));
  });

  // Verbatim blocks -> placeholder paragraphs, re-substituted after turndown.
  const verbs = [];
  clone.querySelectorAll("[data-verbatim]").forEach((v) => {
    const i = verbs.length;
    verbs.push(v.dataset.md || "");
    const marker = document.createElement("p");
    marker.textContent = "xVERBATIMMARKERx" + i + "x";
    v.replaceWith(marker);
  });

  let md = turndown.turndown(clone.innerHTML);
  verbs.forEach((raw, i) => {
    md = md.replace("xVERBATIMMARKERx" + i + "x", raw);
  });
  return md.trim() + "\n";
}

/* ---------- Save ---------- */
function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.hidden = false;
}

async function save() {
  saveBtn.disabled = true;
  try {
    const res = await fetch("/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ markdown: serializeMarkdown() }),
    });
        const data = await res.json();
        FINISHED = true; // stop autosave; the server clears the draft on /save
        clearTimeout(checkpointTimer);
        setAutosave("Review saved");
        showToast("✓ Saved to " + data.path);
      } catch (e) {
    showToast("Save failed: " + e);
    saveBtn.disabled = false;
  }
}
saveBtn.addEventListener("click", save);

/* ---------- Continue later (pause) ---------- */
async function continueLater() {
  laterBtn.disabled = true;
  await postCheckpoint(); // guarantee the latest draft is on disk
  const saved = autosaveEl && autosaveEl.textContent === "Draft saved";
  if (!saved) {
    showToast(
      "Could not save draft — the server may be offline. Please keep this tab open and try again."
    );
    laterBtn.disabled = false;
    return;
  }
  showToast(
    "✓ Progress saved. You can close this tab; re-run the skill on the same manuscript to continue."
  );
  // The tab was opened by the OS (not by script), so window.close is usually
  // blocked by the browser; the toast tells the user to close it. We still try.
  setTimeout(() => {
    try {
      window.close();
    } catch (e) {
      /* best-effort */
    }
  }, 400);
}
laterBtn.addEventListener("click", continueLater);

loadDoc();
