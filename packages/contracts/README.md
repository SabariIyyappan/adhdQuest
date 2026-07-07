# @adhdquest/contracts

The shared data shapes that cross person boundaries (Section 8 of the implementation
plan). **These are a shared source of truth — do not change them unilaterally.** A change
here ripples into all three packages; it requires team agreement.

| Contract | Producer | Store | Consumer | File |
|----------|----------|-------|----------|------|
| A — Upload → Pipeline 1 | Person A | — | Person B | `src/pipeline1.ts` |
| B — Pipeline 1 output     | Person B | Person A | Person C | `src/pipeline1.ts` |
| C — Realtime events       | Person B | Person A | Person C | `src/realtime.ts` |
| D — Session event payload | Person B | Person A | Person C | `src/session-events.ts` |
| E — Report JSON           | Person B | Person A | Person C | `src/report.ts` |

`src/domain.ts` holds the shared enums/entities (topics, difficulty, statuses) referenced
across contracts. `schemas/` holds language-neutral JSON Schema so the Python pipelines
can validate against the exact same shapes without importing TypeScript.
