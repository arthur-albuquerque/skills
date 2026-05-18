---
name: implement_plan
description: Execute a plan or spec file by reading it and implementing its contents. Use this whenever the user provides a path to a plan, spec, or design document and wants it implemented — even if they just drop a file path and say "do it" or "follow this". Trigger on: "implement the plan", "follow the spec", "execute plan at <path>", "implement from <file>", or any message where the user references a plan/spec file path and wants it carried out. Make sure to use this skill whenever there's a file path and an intent to implement, even if the word "implement" isn't used.
argument-hint: <path-to-spec-or-plan-file>
---

The user has provided a path to a spec or plan file. Read it, then implement it.

## Steps

1. Read the file at the path given in the skill arguments.
2. Treat its full contents as the spec and follow the instruction below.
3. Maintain a running `implementation-notes.html` in the working directory throughout — update it as you go, not just at the end.

## Instruction

Implement [the spec you just read]. As you work maintain a running implementation-notes.html file that captures anything I should know about how the implementation diverges from or interprets the spec, including:

- Design decisions: choices you made where the spec was ambiguous
- Deviations: places where you intentionally departed from the spec, and why
- Tradeoffs: alternatives you considered and why you picked what you did
- Open questions: anything you'd want me to confirm or revise
