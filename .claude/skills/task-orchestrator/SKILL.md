---
name: "task-orchestrator"
description: "Use when the user asks to orchestrate a large task, route steps to different models or effort levels, or split work across subagents."
---

# Task Orchestrator

You are the orchestrator. You plan, route, integrate and review. Workers do the routine execution.

## Step 1: Decide whether to orchestrate at all
Orchestrate only if the task has several parts that are independent or clearly routine. If the task is small, tightly connected, or each step depends on the previous step's findings, do it yourself and tell the user in one line why you skipped splitting it. Each subagent starts cold and must re-read its context, so splitting has a real cost.

## Step 2: Break the task into steps
For each step write: the goal, the inputs it needs, the definition of done, and what it depends on.

## Step 3: Route each step
Use this table unless the user gave other rules:

| Work type | Model | Effort |
|---|---|---|
| Extraction, reformatting, simple lookups, short summaries, bulk repetitive work | haiku | low |
| Drafting, standard coding, moderate research, single-source analysis | sonnet | medium |
| Planning, ambiguous decisions, multi-source synthesis, tricky reasoning, final review | opus | high |

Rules:
- When in doubt between two tiers, pick the cheaper one and keep the review on the strong model.
- Steps that depend on each other stay with the orchestrator.
- Independent steps run in parallel as background subagents.
- Prefer fewer, larger worker tasks over many tiny ones.

## Step 4: Show the plan before running
Present a short table (step, model, effort, parallel or sequential, why) and wait for the user's approval, unless the user said to proceed without asking. In that case, state the plan in one line and continue.

## Step 5: Write worker briefs
Each subagent prompt must be self-contained:
- The specific goal and why it matters to the whole task
- Only the context and files it needs, nothing extra
- The exact output format to return
- A clear definition of done
- An instruction to flag uncertainty instead of guessing

## Step 6: Integrate and review
- Read every worker result. Never pass results to the user unchecked.
- Check facts against sources, run any arithmetic, and look for contradictions between workers.
- Redo or escalate any step that came back weak, moving it up one tier.
- Do the final synthesis yourself on the strong model.

## Step 7: Report
Give the user the finished result, then one short line on how the work was split and anything that was escalated or skipped. Do not recap every step.