# Writing the brief

Every rule here comes from [Prompting Claude Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5).

## Spec, not script

Opus 5 does its best work on difficult multi-file and end-to-end tasks when handed the **complete task specification up front and left to run**. So the brief is a specification, not a procedure: the finished state, absolute paths, any diagnosis you already made embedded inline (signatures, schemas, the exact error text), what to leave alone, and a done-criterion checkable from outside the run. Give the goal and the constraints; leave the route to the agent.

## Leave verification out

Opus 5 verifies its own work and catches its own mistakes unprompted. Instructions that add a verification ritual — "include a final verification step", "use a subagent to verify", "double-check before you finish", "re-verify your answer" — compound with behaviour the model already has: they burn tokens and wall-clock without improving the result.

Naming the command that has to pass is a done-criterion, not a ritual. `pytest tests/test_auth.py passes with no failures` belongs in the brief; `then verify your work thoroughly` does not.

## Bound the scope

Opus 5 can expand a task, adding steps that weren't requested or applying its own judgment about what the task should be. For a narrow task, say so — and note that a background run cannot ask you, so a request that reads two ways gets resolved without you:

```text
Deliver what was asked, at the scope intended. Make routine judgment calls yourself, and check in only when different readings of the request would lead to materially different work. If the request seems mistaken or a better approach exists, say so in a sentence and continue with the task as asked rather than quietly narrowing, widening, or transforming it. Finish the whole task, and stop short of actions that are clearly beyond what was asked.
```

## Cap delegation

Opus 5 delegates readily, and inside a background run its subagents multiply cost and time where you can't see them. Include this whenever the task is small enough that fan-out would be waste:

```text
Delegate to a subagent only for large tasks that are genuinely independent and parallelizable, such as a wide multi-file investigation. Do not delegate work you can finish yourself in a handful of tool calls, and do not use subagents to verify or double-check your own work. If one subagent can complete the task, use one rather than several, and keep spawn counts low.
```

## Length

Opus 5 runs longer than Opus 4.8 on both counts below, and each needs its own lever. Effort controls how much the model thinks, not how much it says, so lowering effort will not shorten either one.

The final message is your entire view of the run, so shape it rather than just shortening it:

```text
Before your first tool call, say in one sentence what you're about to do. While working, give a brief update only when you find something important or change direction. When you finish, lead with the outcome: your first sentence should answer "what happened" or "what did you find," with supporting detail after it for readers who want it.
```

When the deliverable is a document the agent writes to disk, calibrate it too:

```text
Match the length of written documents to what the task needs: cover the substance, but do not pad with filler sections, redundant summaries, or boilerplate.
```

## Effort

`high` is the default. Use `low` and `medium` liberally — they hold quality at a fraction of the tokens and latency, and they are the primary control over what a background run costs. Step up to `xhigh` for demanding coding and agentic work: multi-file features, larger refactors, end-to-end feature work.

## Review and audit briefs

Opus 5 finds real bugs at a high rate per pass, and its extra findings are mostly real issues rather than false positives — but it takes a filtering instruction literally and will report less. Ask for everything and filter in a second pass yourself; never brief a review run with "only report high-severity issues" or "be conservative". Its accuracy holds at lower effort, so a fast cheap pass at review time and a thorough one later both work.
