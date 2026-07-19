# Work Routing

How to decide who handles what.

## Routing Table

| Work Type | Route To | Examples |
|-----------|----------|----------|
| Architecture, prioritization, cross-cutting tradeoffs | Morpheus | Scope decisions, interfaces across API/ingestion/web |
| Backend API and authorization flow | Trinity | FastAPI routes, entitlement checks, filter enforcement |
| Ingestion and search indexing | Niobe | Chunking, metadata mapping, index schema, ingestion scripts |
| Frontend and UX | Link | React UI flows, API integration, demo usability |
| Testing and quality | Tank | pytest coverage, authz edge cases, regression checks |
| Code review | Morpheus | Review PRs, enforce architectural coherence |
| Scope & priorities | Morpheus | What to build next, trade-offs, milestones |
| Session logging | Scribe | Automatic — never needs routing |
| RAI review | Rai | Content safety, bias checks, credential detection, ethical review |
| Claim verification / devil's advocate | Fact Checker | Verify claims, challenge assumptions, pre-mortem risks |

## Issue Routing

| Label | Action | Who |
|-------|--------|-----|
| `squad` | Triage: analyze issue, assign `squad:{member}` label | Morpheus |
| `squad:morpheus` | Pick up issue and complete the work | Morpheus |
| `squad:trinity` | Pick up issue and complete the work | Trinity |
| `squad:niobe` | Pick up issue and complete the work | Niobe |
| `squad:link` | Pick up issue and complete the work | Link |
| `squad:tank` | Pick up issue and complete the work | Tank |

### How Issue Assignment Works

1. When a GitHub issue gets the `squad` label, the **Lead** triages it — analyzing content, assigning the right `squad:{member}` label, and commenting with triage notes.
2. When a `squad:{member}` label is applied, that member picks up the issue in their next session.
3. Members can reassign by removing their label and adding another member's label.
4. The `squad` label is the "inbox" — untriaged issues waiting for Lead review.

## Rules

1. **Eager by default** — spawn all agents who could usefully start work, including anticipatory downstream work.
2. **Scribe always runs** after substantial work, always as `mode: "background"`. Never blocks.
3. **Quick facts → coordinator answers directly.** Don't spawn an agent for "what port does the server run on?"
4. **When two agents could handle it**, pick the one whose domain is the primary concern.
5. **"Team, ..." → fan-out.** Spawn all relevant agents in parallel as `mode: "background"`.
6. **Anticipate downstream work.** If a feature is being built, spawn the tester to write test cases from requirements simultaneously.
7. **Issue-labeled work** — when a `squad:{member}` label is applied to an issue, route to that member. The Lead handles all `squad` (base label) triage.
