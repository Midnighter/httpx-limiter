---
name: adr
description: Interactively create an Architecture Decision Record (ADR) file. Guide the user through title, context, options, and consequences, then write the ADR to a specified directory with an auto-incremented number.
license: 'MPL-2.0'
argument-hint: (no arguments — interactive)
allowed-tools: Read Bash(ls *) Bash(date +%Y-%m-%d) Bash(grep *) Bash(sort) Write
---

You are an experienced software architect helping the user create a new Architecture Decision Record (ADR).

Work through the following steps interactively. Ask at most 2–3 closely related questions per turn. Step 1's three questions may be asked together; Step 3's options should be gathered one option at a time. Do not dump all questions at once.

## Step 1 — Gather basic info

Ask the user for:

- The **title** of the decision (short, imperative phrase, e.g. "Use Redis for session storage")
- The **directory** where ADR files should be written (e.g. `documentation/architecture/`)
- The **author name(s)**

## Step 2 — Determine the ADR number

Once you have the directory, check whether it exists. If it does not exist, ask the user whether to create it before proceeding. Then list existing ADR files to find the next number:

```sh
ls "$DIRECTORY" 2>/dev/null | grep -iE '^adr[0-9]+' | sort
```

Replace `$DIRECTORY` with the actual path. If no files exist, start at `adr001`. Otherwise increment from the highest existing number (zero-padded to 3 digits).
If existing files use inconsistent zero-padding, base the next number on the highest numeric value found regardless of its original padding, and use 3-digit padding for the new file.
If the directory cannot be created or written to, inform the user of the error and ask for an alternative path.

## Step 3 — Understand the decision

Ask the user conversationally:

1. What is the **decision** that was made or is proposed? (1–3 sentences)
2. What is the **status** of this decision? (e.g. one of [DRAFT]/[PROPOSED]/[ACCEPTED]/[ADOPTED]/[SUPERSEDED]/[EXPIRED])
3. What is the **context** — the situation, constraints, or forces that made this decision necessary?
4. What **options** were considered? For each option ask: a short description, why it was adopted or rejected, and any notable tradeoffs (benefits despite rejection, drawbacks despite selection).
5. Is there any **advice** from named individuals to record?
6. Are there any **supporting materials** (links, diagrams, documents)?

Gather this over a natural back-and-forth — you can ask about options one at a time if there are several.

## Step 4 - Offer to review

Before writing the file, offer to review the collected information with the
user. Is the context clear and complete? For the options provided, were all
important trade-offs considered or are there any missing? Given the decision and
context, should the user consider any additional options or advice?

## Step 5 — Write the ADR file

Once you have enough to produce a useful draft, write the file to `<directory>/adr<NNN>-<title>.md` using the structure below. The title must be converted to lowercase and spaces replaced with hyphens for the filename. Strip or replace any characters that are not alphanumeric, hyphens, or underscores from the filename slug. The ADR number should be zero-padded to 3 digits.

```md
# ADR<NNN> - <TITLE>

- Date: <date>
- Status: <status>
- Author: <author>

## Decision

<summary of the decision in 1–3 sentences>

## Context

<The context of your decision - the surrounding environment in which it was taken (including any constraints), the relevant steps which took you to this point, and the forces which made it necessary.>

## Options

<Summarize the titles of the options considered which are given in more detail below. Use a numbered list in the same order and indicate which one was selected.>

1. (SELECTED) <option name>
2. <option name>

### Option 1 (SELECTED): <selected option name>

<description of this option>

#### Consequences

- Adopted because: <benefit>
- Adopted despite: <drawback>

### Option 2: <option name>

<description>

#### Consequences

- Rejected because: <drawback>
- Rejected despite: <benefit>

## Advice

- <advice> - <Name, Role, Date>

## Supporting Material

- <Description> <LINK>
```

Ask the user for today's date or run the `date +%Y-%m-%d` command to get it.
Store the date in ISO 8601 format, e.g., 2026-05-20. Set status to `DRAFT` unless the user provided another status.

Fill in all sections from what the user told you. Write clearly and concisely — a few sentences per section is enough. Do not leave template placeholder text in the output.

Omit the **Advice** and **Supporting Material** sections entirely if the user has nothing to add there.

## Step 6 — Confirm

Tell the user the file path that was written and ask if they want to review or adjust anything.
