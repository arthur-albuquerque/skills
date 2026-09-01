# Fable guidance

Standalone guide for briefing a `--model fable` dispatch (Claude Fable 5.1). Every rule here comes from [Prompting Claude Fable 5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1) and the Fable 5.1 migration notes in the `claude-api` skill.

## Spec, not script

Fable does its best work when handed the **complete task specification up front and left to run**. The brief is a specification, not a procedure: the finished state, absolute paths, any diagnosis you already made embedded inline (signatures, schemas, the exact error text), what to leave alone, and a done-criterion checkable from outside the run. Give the goal and the constraints. Leave the route to the agent.

Brief it lean. Prescriptive step lists written for prior models reduce Fable's output quality, and one steering sentence beats enumerating each unwanted pattern by name. Cut any instruction that merely restates good default behaviour.

## Give the reason, not only the request

Fable performs better when it knows the intent. Context lets it connect the task to relevant information rather than inferring intent on its own. Open the brief with one sentence of it:

```text
I'm working on [the larger task] for [who it's for]. They need [what the output enables]. With that in mind: [request].
```

## Act, don't overplan

At `high` effort Fable can gather context and deliberate past what the task needs. On an ambiguous brief, add:

```text
When you have enough information to act, act. Do not re-derive facts already established, re-litigate a decision the brief has already made, or narrate options you will not pursue. If you are weighing a choice, give a recommendation, not an exhaustive survey.
```

## Keep it running

Deep into a long run Fable can end a turn on a statement of intent ("Next, I'll ...") without the tool call, or stop to ask permission for a step the brief already covered. Nobody is watching a background run, so every unattended dispatch gets both blocks below. The opening sentence of the first one carries most of the effect; keep it as written. If the run must stop for specific confirmations, add a sentence after it listing them.

```text
You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to...?' or 'Shall I...?' will block the work. For reversible actions that follow from the original request, proceed without asking. Stop only for destructive actions or genuine scope changes the user must decide. Offering follow-ups after the task is done is fine; asking permission before doing the work is not.

Exception: when the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one.

Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ('I'll...', 'let me know when...'), do that work now with tool calls. That includes retrying after errors and gathering missing information yourself. Do not stop because the context or session is long. End your turn only when the task is complete or you are blocked on input only the user can provide.

Before running a command that changes system state (such as restarts, deletes, or config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.
```

The second block makes the brief the scope of the deliverable. Fable reads it as "finish all of it, and nothing beyond it":

```text
# Delivering work
The user's request, or the plan they approved, sets the scope, and the scope is the deliverable: don't quietly narrow, widen, or swap it. Read ambiguity the way a careful colleague would: make routine judgment calls yourself, and check in only when different readings would lead to materially different work. If you see a real problem with the task as specified, say so in a sentence or two and keep building under stated assumptions; if the user hears the concern and reaffirms, that is their decision, so deliver the full request.

If a question comes up partway, first do everything that doesn't depend on the answer; then state the assumption you made, or, when going ahead on a wrong guess would be unsafe or would make the work useless, put the question at the end of a turn that also delivers that progress. If one part turns out to be blocked, complete every other part in full and say exactly what you left out and why: the whole task is the deliverable, and scaling it down is the user's call, not yours. A step you have decided on is something to run, not to announce: describing the next step and ending the turn leaves it undone until the user replies.

Keep changes to what the request needs. Something else you notice worth doing, such as cleanup or documentation the task didn't call for, or a change to a file the task didn't require, is a suggestion to make at the end, not a change to make; actions clearly beyond what the ask implies, and risky or destructive ones, still need the user's go-ahead.
```

These two blocks make Fable write slightly more code, mostly extra tests in files it is already editing. Pair them with the coding block below and the progress audit.

## Bound the scope on coding tasks

On an open-ended feature Fable delivers what was asked and sometimes more: it fixes nearby code, extends behaviour the task never mentioned, and commits scratch checks as permanent test files. This block cuts unrequested additions and committed test code with no measured loss in task success. Paste it on every coding dispatch:

```text
If, while working or testing, you find a pre-existing bug, a performance concern, or behavior the task doesn't mention, don't fix, optimize or extend it in this change unless the requested behavior cannot work without it; report it as a follow-up in your summary. Where the task is ambiguous, implement the reading its wording and the surrounding code most directly support, state that assumption in your summary, and don't build for the other readings as well. Verify your work however you like; scratch scripts and quick checks need not be kept. Commit tests only where the task asks for them or this repository already keeps tests for this kind of change, sized like the neighboring test files, roughly one focused test per stated behavior, and don't turn scratch checks into additional permanent test files. This is about extras only: implement every behavior the task asks for, completely.

The number of tokens used to edit files is best minimized, all else being equal. Therefore, when it will not affect the end result, try to surgically edit a file rather than rewrite the entire thing.
```

The last sentence is there because Fable 5.1 rewrites whole files for small changes more often than Fable 5 did. Same result, more tokens and time.

If higher effort still produces unrequested refactors, add:

```text
Don't add features, refactor, or introduce abstractions beyond what the task requires. A bug fix doesn't need surrounding cleanup and a one-shot operation usually doesn't need a helper. Do the simplest thing that works well. Don't add error handling, fallbacks, or validation for scenarios that cannot happen; validate only at system boundaries (user input, external APIs). Don't use feature flags or backwards-compatibility shims when you can just change the code.
```

## Delegation

Parallel subagents are dependable on Fable, and on genuinely large parallelizable work delegation is a strength: leave it open, and tell it to keep working while they run rather than block on each one.

```text
Delegate independent subtasks to subagents and keep working while they run. Intervene if a subagent goes off track or is missing relevant context.
```

Inside a background run, though, subagents multiply cost and time where you can't see them, and the standing policy is at most 3 parallel subagents and never more than 1 parallel Fable subagent. On any task small enough that fan-out would be waste, paste instead:

```text
Delegate to a subagent only for large tasks that are genuinely independent and parallelizable, such as a wide multi-file investigation. Do not delegate work you can finish yourself in a handful of tool calls. If one subagent can complete the task, use one rather than several, and keep spawn counts low.
```

## Verification

Naming the command that has to pass (`pytest tests/test_auth.py passes with no failures`) is a done-criterion. Put it in every brief. If an existing brief already asks the model to test or check its work before reporting, keep that line: the Opus advice to strip verification instructions does not carry over to Fable.

A multi-hour autonomous build also gets a cadence. Fresh-context verifier subagents outperform self-critique:

```text
Establish a method for checking your own work as you build. After each [module / milestone], verify the work so far with a fresh subagent against the specification.
```

For an overnight run, also name a notes file where the agent keeps one lesson per line. Fable works measurably better when it can re-read what earlier hours taught it.

## Ground progress claims

For a long autonomous run, include this. In Anthropic's testing it nearly eliminated fabricated status reports:

```text
Before reporting progress, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so explicitly. Report outcomes faithfully: if tests fail, say so with the output; if a step was skipped, say that; when something is done and verified, state it plainly without hedging.
```

## Progress updates and the final message

Fable 5.1 writes fewer updates during long tool-calling turns than Fable 5 did, more so at higher effort. Never brief it to hold findings for the end or to update "only when something important happens"; those lines were written for chattier models and now silence it. Say instead when you want user-facing text, and shape the final message, which is your entire view of the run:

```text
Before you start, say in a line what you're about to do; brief updates while you work help the user follow along. Close with a recap that stands on its own for a reader who saw none of the run: lead with the outcome, so your first sentence answers "what happened" or "what did you find", then what you did, what's next, and the supporting detail. Complete sentences, terms spelled out, no arrow chains or labels you coined mid-run. If you have to choose between short and clear, choose clear.
```

When the deliverable is a document the agent writes to disk, calibrate it too. Fable 5.1's prose can run denser than Fable 5's, with longer sentences and fewer paragraph breaks:

```text
Match the length of written documents to what the task needs: cover the substance, but do not pad with filler sections, redundant summaries, or boilerplate. Remove all mannered prose: when a literal phrase is available, use it.
```

## What must stay out

State what the brief needs shown, never how the model reasoned: instructions to echo, transcribe, or explain internal reasoning trigger Fable's reasoning-extraction refusals.

Fable's safety classifiers can refuse a request outright. Finding bugs and vulnerabilities in source code is permitted, but offensive-security and biology or life-sciences tasks still route to Opus. Three phrasings raise false positives on ordinary coding work: ask "are there any bugs in this program?" rather than "does this compile without errors?"; give context and docs for a lesser-known language; and keep base64-encoded data out of tool output.

## Effort and wall-clock

Use the level the user named; when they leave it to you, judge it from the task. `high` is the ceiling and the default. The user's standing cost policy caps Fable there; if the user asked higher, dispatch at `high` and say so. Effort level names do not map to the same amount of thinking across models, so do not carry a Fable 5 choice over unexamined. `medium` roughly matches Fable 5 at lower cost, and `low` often beats Opus and Sonnet on cost per task, so both are the cost lever for routine work. Two caveats at `low`: Fable searches less and answers from memory more, so a research or lookup task gets `medium` or better; and on dense images it may answer from an overall impression without cropping.

Expect long turns: many minutes per request at higher effort, hours for autonomous runs. Check on the run asynchronously rather than blocking, and warn the user the run may be slow and quota-hungry.
