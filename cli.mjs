#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as clack from "@clack/prompts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = __dirname;

const CLIENTS = ["claude-code", "codex", "opencode"];
const CLIENT_LABELS = {
  "claude-code": "Claude Code",
  codex: "Codex",
  opencode: "OpenCode",
};

const HELP = `skills — install Arthur's agent skills

Usage:
  npx github:arthur-albuquerque/skills [add]   Interactive installer
  npx github:arthur-albuquerque/skills list    List available skills

Options:
  --skill, -s <name>        Install only this skill (repeatable)
  --client, -a <client>     claude-code, codex, opencode, or all (repeatable / comma-separated)
  --scope <user|project>    Install for your user or into the current project (default: user)
  -g, --global              Alias for --scope user
  --project                 Alias for --scope project
  --cwd <dir>               Base directory for project-scope installs (default: current dir)
  -y, --yes                 Non-interactive: accept defaults (all skills, all clients, user scope)
  --dry-run                 Print intended writes without changing files
  --json                    Print machine-readable JSON (list / add)
`;

function unique(values) {
  return [...new Set(values)];
}

function defaultArgs(command) {
  return {
    command,
    skillNames: [],
    clients: [],
    scope: "user",
    scopeExplicit: false,
    baseDir: undefined,
    yes: false,
    dryRun: false,
    printJson: false,
  };
}

function parseScope(value) {
  if (value === "user" || value === "project") return value;
  throw new Error("--scope must be user or project.");
}

function normalizeClients(value) {
  return value.split(",").flatMap((raw) => {
    const c = raw.trim().toLowerCase();
    if (!c) return [];
    if (c === "all") return CLIENTS;
    if (c === "codex") return ["codex"];
    if (c === "opencode") return ["opencode"];
    if (c === "claude" || c === "claude-code" || c === "claude-code-cli") return ["claude-code"];
    throw new Error(`Unsupported client "${raw}". Use claude-code, codex, opencode, or all.`);
  });
}

function normalizeSkillName(value) {
  const n = value.trim().toLowerCase();
  if (!/^[a-z0-9][a-z0-9._-]*$/.test(n)) throw new Error(`Invalid skill name "${value}".`);
  return n;
}

function parseArgs(argv) {
  const first = argv[0];
  if (!first || first === "help" || first === "--help" || first === "-h") {
    return defaultArgs(!first ? "add" : "help");
  }
  const command = first === "list" ? "list" : "add";
  const args = first === "add" || first === "list" ? argv.slice(1) : argv;
  const out = defaultArgs(command);
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    const eat = (flag) => {
      if (arg === flag) {
        const next = args[++i];
        if (!next || next.startsWith("-")) throw new Error(`Missing value for ${flag}.`);
        return next;
      }
      if (arg.startsWith(`${flag}=`)) {
        const v = arg.slice(flag.length + 1);
        if (!v) throw new Error(`Missing value for ${flag}.`);
        return v;
      }
      return undefined;
    };
    let v;
    if ((v = eat("--skill")) !== undefined) out.skillNames.push(v);
    else if ((v = eat("-s")) !== undefined) out.skillNames.push(v);
    else if ((v = eat("--client")) !== undefined) out.clients.push(...normalizeClients(v));
    else if ((v = eat("--agent")) !== undefined) out.clients.push(...normalizeClients(v));
    else if ((v = eat("-a")) !== undefined) out.clients.push(...normalizeClients(v));
    else if ((v = eat("--scope")) !== undefined) {
      out.scope = parseScope(v);
      out.scopeExplicit = true;
    } else if ((v = eat("--cwd")) !== undefined) out.baseDir = v;
    else if (arg === "-g" || arg === "--global") {
      out.scope = "user";
      out.scopeExplicit = true;
    } else if (arg === "--project") {
      out.scope = "project";
      out.scopeExplicit = true;
    } else if (arg === "-y" || arg === "--yes") out.yes = true;
    else if (arg === "--dry-run") out.dryRun = true;
    else if (arg === "--json") out.printJson = true;
    else if (arg.startsWith("-")) throw new Error(`Unknown option: ${arg}`);
    else throw new Error(`Unexpected argument: ${arg}`);
  }
  out.skillNames = unique(out.skillNames.map(normalizeSkillName));
  out.clients = unique(out.clients);
  return out;
}

function frontmatterField(frontmatter, field) {
  if (!frontmatter) return undefined;
  const lines = frontmatter.split(/\r?\n/);
  for (let i = 0; i < lines.length; i += 1) {
    const match = lines[i].match(new RegExp(`^${field}:\\s*(.*)$`));
    if (!match) continue;
    const raw = match[1].trim();
    if (raw === ">-" || raw === ">" || raw === "|-" || raw === "|") {
      const block = [];
      for (let j = i + 1; j < lines.length; j += 1) {
        const line = lines[j];
        if (line.trim() && !/^\s/.test(line)) break;
        block.push(line.replace(/^\s+/, ""));
      }
      const value = raw.startsWith("|") ? block.join("\n") : block.join(" ");
      return value.replace(/\s+/g, " ").trim() || undefined;
    }
    return raw.replace(/^["']|["']$/g, "").trim() || undefined;
  }
  return undefined;
}

function readSkillMeta(skillFile, fallbackName) {
  const body = fs.readFileSync(skillFile, "utf-8");
  const fm = body.match(/^---\n([\s\S]*?)\n---/);
  const name = frontmatterField(fm?.[1], "name") ?? fallbackName;
  const description = frontmatterField(fm?.[1], "description");
  return { name: normalizeSkillName(name), description };
}

function clientSubdir(client) {
  if (client === "claude-code") return ".claude";
  if (client === "opencode") return ".opencode";
  return ".codex";
}

function discoverSkills(root) {
  const dirs = fs
    .readdirSync(root, { withFileTypes: true })
    .filter((e) => e.isDirectory() && !e.name.startsWith(".") && e.name !== "node_modules");
  const skills = [];
  for (const e of dirs) {
    const dir = path.join(root, e.name);
    const flat = path.join(dir, "SKILL.md");
    if (fs.existsSync(flat)) {
      const meta = readSkillMeta(flat, e.name);
      skills.push({ name: meta.name, description: meta.description, dir, perClient: false });
      continue;
    }
    const claudeSkill = path.join(dir, ".claude", "SKILL.md");
    const opencodeSkill = path.join(dir, ".opencode", "SKILL.md");
    const metaFile = fs.existsSync(claudeSkill)
      ? claudeSkill
      : fs.existsSync(opencodeSkill)
        ? opencodeSkill
        : null;
    if (metaFile) {
      const meta = readSkillMeta(metaFile, e.name);
      skills.push({ name: meta.name, description: meta.description, dir, perClient: true });
    }
  }
  return skills.sort((a, b) => a.name.localeCompare(b.name));
}

function sourceDirForClient(skill, client) {
  if (!skill.perClient) return skill.dir;
  const preferred = path.join(skill.dir, clientSubdir(client));
  if (fs.existsSync(path.join(preferred, "SKILL.md"))) return preferred;
  for (const sub of [".claude", ".opencode"]) {
    const cand = path.join(skill.dir, sub);
    if (fs.existsSync(path.join(cand, "SKILL.md"))) return cand;
  }
  return null;
}

function installRootForClient(client, scope, baseDir) {
  const home = process.env.HOME || os.homedir();
  if (scope === "project") {
    if (client === "claude-code") return path.join(baseDir, ".claude", "skills");
    if (client === "codex") return path.join(baseDir, ".agents", "skills");
    return path.join(baseDir, ".opencode", "skills");
  }
  if (client === "claude-code") return path.join(home, ".claude", "skills");
  if (client === "codex") {
    return process.env.CODEX_HOME
      ? path.join(process.env.CODEX_HOME, "skills")
      : path.join(home, ".codex", "skills");
  }
  return path.join(home, ".config", "opencode", "skills");
}

function isInteractive(opts) {
  if (opts.yes) return false;
  if (process.env.CI === "true") return false;
  return Boolean(process.stdin.isTTY && process.stdout.isTTY);
}

function compactHint(value) {
  const hint = value?.replace(/\s+/g, " ").trim() ?? "";
  if (!hint) return "Skill from this repo.";
  return hint.length <= 96 ? hint : `${hint.slice(0, 93).trimEnd()}...`;
}

function bail() {
  clack.cancel("Cancelled.");
  process.exit(0);
}

async function resolveSkills(entries, opts) {
  const byName = new Map(entries.map((e) => [e.name, e]));
  const requested = unique(opts.skillNames.map(normalizeSkillName));
  if (requested.length > 0) {
    const missing = requested.filter((n) => !byName.has(n));
    if (missing.length) {
      throw new Error(
        `Unknown skill${missing.length === 1 ? "" : "s"}: ${missing.join(", ")}. ` +
          `Available: ${entries.map((e) => e.name).join(", ")}.`,
      );
    }
    return requested.map((n) => byName.get(n));
  }
  if (!isInteractive(opts)) return entries;
  const result = await clack.multiselect({
    message: "Which skills do you want to install?\n  (space toggles, enter confirms)",
    options: entries.map((e) => ({ value: e.name, label: e.name, hint: compactHint(e.description) })),
    initialValues: entries.map((e) => e.name),
    required: true,
  });
  if (clack.isCancel(result)) bail();
  return result.filter((x) => typeof x === "string").map((n) => byName.get(n));
}

async function resolveClients(opts) {
  const requested = unique(opts.clients);
  if (requested.length) return requested;
  if (!isInteractive(opts)) return CLIENTS;
  const result = await clack.multiselect({
    message: "Install these skills for which agents?\n  (space toggles, enter confirms)",
    options: CLIENTS.map((c) => ({
      value: c,
      label: CLIENT_LABELS[c],
      hint: `Install into ${CLIENT_LABELS[c]} skill directories`,
    })),
    initialValues: CLIENTS,
    required: true,
  });
  if (clack.isCancel(result)) bail();
  return result.filter((x) => CLIENTS.includes(x));
}

async function resolveScope(opts) {
  if (opts.scopeExplicit) return opts.scope;
  if (!isInteractive(opts)) return "user";
  const result = await clack.select({
    message: "Where do you want to install these skills?",
    options: [
      {
        value: "user",
        label: "User",
        hint: "Your home directory (~/.claude, ~/.codex, ~/.config/opencode), across projects",
      },
      {
        value: "project",
        label: "Project",
        hint: "This repo only (.claude / .agents / .opencode in the current directory)",
      },
    ],
    initialValue: "user",
  });
  if (clack.isCancel(result)) bail();
  return result === "project" ? "project" : "user";
}

function shortenPath(file, baseDir) {
  const resolved = path.resolve(file);
  const home = process.env.HOME || os.homedir();
  if (resolved === home || resolved.startsWith(`${home}${path.sep}`)) {
    return `~${resolved.slice(home.length)}`;
  }
  const rel = path.relative(path.resolve(baseDir), resolved);
  if (rel && !rel.startsWith("..") && !path.isAbsolute(rel)) return `.${path.sep}${rel}`;
  return file;
}

function plural(count, singular, pluralForm = `${singular}s`) {
  return `${count} ${count === 1 ? singular : pluralForm}`;
}

function summarizePaths(files, baseDir, max = 4) {
  const short = unique(files).map((f) => shortenPath(f, baseDir));
  if (short.length <= max) return short.join(", ");
  return `${short.slice(0, max).join(", ")} +${short.length - max} more`;
}

async function install(opts) {
  const baseDir = path.resolve(opts.baseDir ?? process.cwd());
  const entries = discoverSkills(REPO_ROOT);
  if (entries.length === 0) throw new Error(`No skills found in ${REPO_ROOT}.`);
  const selected = await resolveSkills(entries, opts);
  if (!selected.length) throw new Error("No skills selected.");
  const clients = await resolveClients(opts);
  const scope = await resolveScope(opts);

  const progress = isInteractive(opts) ? clack.progress({ max: 1, indicator: "timer" }) : null;
  const written = [];
  try {
    progress?.start("Installing skill files...");
    for (const client of clients) {
      const root = installRootForClient(client, scope, baseDir);
      for (const skill of selected) {
        const src = sourceDirForClient(skill, client);
        if (!src) continue;
        const dest = path.join(root, skill.name);
        written.push(dest);
        if (!opts.dryRun) {
          fs.rmSync(dest, { recursive: true, force: true });
          fs.mkdirSync(path.dirname(dest), { recursive: true });
          fs.cpSync(src, dest, { recursive: true });
        }
      }
    }
    progress?.advance(1, "Skill files installed");
    progress?.stop("Installation complete");
  } catch (err) {
    progress?.error("Installation failed");
    throw err;
  }
  return {
    skills: selected.map((s) => s.name),
    clients,
    scope,
    written,
    dryRun: Boolean(opts.dryRun),
    baseDir,
  };
}

function printResult(result) {
  const verb = result.dryRun ? "Would install" : "Installed";
  const summary = [
    `Skills        ${result.skills.join(", ") || "none"}`,
    `Agents        ${result.clients.map((c) => CLIENT_LABELS[c]).join(", ") || "none"}`,
    `Scope         ${result.scope}`,
    result.written.length
      ? `Locations     ${plural(result.written.length, "folder")} (${summarizePaths(result.written, result.baseDir)})`
      : "",
  ].filter(Boolean);
  clack.note(summary.join("\n"), verb);
  if (!result.dryRun) {
    clack.note("Restart or reload your agent if the new skills don't show up.", "Reload");
  }
  clack.outro(`${result.dryRun ? "Dry run complete" : "All set"} ✅`);
}

async function main(argv) {
  const parsed = parseArgs(argv);
  if (parsed.command === "help") {
    process.stdout.write(`${HELP}\n`);
    return;
  }
  if (parsed.command === "list") {
    const skills = discoverSkills(REPO_ROOT);
    if (parsed.printJson) {
      const data = skills.map((s) => ({ name: s.name, description: s.description }));
      process.stdout.write(`${JSON.stringify(data, null, 2)}\n`);
      return;
    }
    for (const s of skills) {
      process.stdout.write(`${s.name}${s.description ? ` - ${s.description}` : ""}\n`);
    }
    return;
  }
  if (isInteractive(parsed)) clack.intro("Install Arthur's agent skills");
  const result = await install(parsed);
  if (parsed.printJson) {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }
  if (isInteractive(parsed)) {
    printResult(result);
  } else {
    const verb = result.dryRun ? "Would install" : "Installed";
    process.stdout.write(
      `${verb} ${result.skills.join(", ")} for ${result.clients.join(", ")} (${result.scope}).\n`,
    );
    for (const w of result.written) process.stdout.write(`  ${shortenPath(w, result.baseDir)}\n`);
  }
}

main(process.argv.slice(2)).catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
