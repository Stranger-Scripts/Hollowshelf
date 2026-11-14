# Hollowshelf: Project Guidelines

> The rules for how work gets into Hollowshelf. They exist to keep the project
> pointed at [v1.0](ROADMAP.md) and stop it from growing in random directions.

## 1. Scope gate

Every new idea follows the same path:

```
idea ──► Parking Lot (ROADMAP.md) ──► promoted? ──► URS entry ──► milestone ──► branch
```

1. **Capture it, don't build it.** Write it in the Parking Lot as one line. That's all.
2. **Promote it only at a milestone boundary,** never in the middle of a milestone.
3. **Before promoting, answer these:**
   - Does it serve an existing *Must*, or close a gap in one?
   - Does it conflict with a non-goal (URS §2.2)? If so, reopening that non-goal needs a decision first (§5).
   - Does it delay the active milestone's exit criteria? If so, it waits.
4. **Promoting it means:** it gets a URS ID, a user story, a priority, acceptance criteria and a milestone. *Then* it can be built.

Rule of thumb: **no code without a URS ID.**

## 2. Definition of Done (per requirement)

A requirement is `Verified` only when all of these hold:

- [ ] Every acceptance criterion is met
- [ ] Verification is done: an automated test (`T`), or a manual check (`M`) with its steps and result written in the PR
- [ ] `ruff check` and `ruff format --check` pass, and CI is green
- [ ] User-visible strings are wrapped in `_()` (once UI-002 is in)
- [ ] Any schema change ships as a migration (once DATA-002 is in). `collection_schema.sql` is never edited in place after v0.2.0.
- [ ] The URS status column is updated in the same PR
- [ ] README is updated if behaviour visible to the user changed

## 3. Branching and commits

- `main` is always runnable and CI-green.
- **One feature branch at a time (WIP = 1):** `feat/<URS-ID>-short-name`, e.g. `feat/DATA-003-backups`.
- Open a PR into `main` even when working solo: it records the manual verification and gives CI something to run.
- Delete the branch once it's merged.
- Conventional commits (already in use), with the URS ID in the scope: `feat(DATA-003): rotate startup backups`.

## 4. Changing the URS

- Adding, reprioritising or withdrawing a requirement bumps the URS minor version and adds a row to its change history.
- IDs are never renumbered or reused.
- Priorities are reviewed at each milestone boundary, not in between.

## 5. Decisions

- Any choice that would be expensive to reverse goes into [DECISIONS.md](DECISIONS.md) with its date, context, decision and consequences: storage, schema shape, framework, deployment, non-goals.
- A resolved open decision (URS §4) becomes a D-entry, and the URS references it.

## 6. Milestone review (≈15 min, at each boundary)

1. Do the exit criteria hold? If not, the milestone stays open.
2. Which requirements slipped, and why?
3. Parking Lot triage: promote, keep or drop.
4. Reprioritise the next milestone's scope.
5. Tag the release.
