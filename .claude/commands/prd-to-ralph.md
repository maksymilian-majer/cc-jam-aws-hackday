---
description: Convert a PRD to Ralph's prd.json format for autonomous execution
argument-hint: [path/to/prd.md]
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Convert PRD to Ralph Format

Use the **ralph skill** to convert the PRD at `$ARGUMENTS` to Ralph's prd.json format.

Follow the instructions in the ralph skill (`.claude/skills/ralph/SKILL.md`) to:

1. Read the PRD file provided
2. Split large features into small, single-iteration stories
3. Order stories by dependencies (schema → backend → UI)
4. Generate prd.json with verifiable acceptance criteria
5. Archive existing prd.json if it's from a different feature

## Key Requirements

- Each story must be completable in ONE Ralph iteration
- Always include "Typecheck passes" in acceptance criteria
- UI stories must include "Verify in browser using dev-browser skill"
- Stories execute in priority order - no forward dependencies

## Output

Save the generated prd.json to the ralph directory (typically project root or `ralph/` folder).
