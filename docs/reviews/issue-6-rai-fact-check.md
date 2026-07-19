# Issue #6 — Pre-Ship RAI + Fact Checker Pass

Date: 2026-07-18  
Reviewer: Rai (RAI Reviewer) + Fact Checker

## Scope Reviewed
- `src/api/main.py`, `src/api/filters.py`, `src/api/search.py`
- `docs/architecture.md`, `docs/sample-queries.md`, `docs/security-model.md`, `README.md`
- `src/api/entitlements.py`, `src/ingestion/metadata.json`

## RAI Findings and Remediations
1. **Privacy / logging minimization**
   - **Finding:** API request logs included raw `userId` and full query text in `/api/search` and `/api/chat`.
   - **Risk:** User identifiers and prompt content can contain sensitive data and should not be logged at info level.
   - **Remediation:** Updated logging to structured, non-content metadata only (mode, topK, query length), and removed user identifiers from warning/info paths.

2. **Authorization filter logging**
   - **Finding:** Filter builder logged user IDs and full entitlement filter strings.
   - **Risk:** Logs could expose tenant/business scope metadata.
   - **Remediation:** Replaced with non-sensitive summary logging (`restricted` and `hasGlobalReferenceClause` booleans).

## Fact Checker Verification
1. **Filter behavior claims validated**
   - Verified generated filters for all demo personas + unknown user with a direct Python check (`entitlements.py` + `filters.py`).
   - Result matched documented expected behavior (deny-by-default, partner/client/product/region scoping, global reference access).

2. **Documentation correction**
   - `docs/sample-queries.md` Query 5 expected filter was adjusted to exactly match runtime output:
     - from `(classification eq 'PublicDemoReference')`
     - to `classification eq 'PublicDemoReference'`

3. **Architecture wording correction**
   - `docs/architecture.md` updated to reflect current implementation truth:
     - from "Logs the generated filter for demo transparency"
     - to "API responses include the generated filter for demo transparency"

## Validation Run
- `python -m compileall src\api\main.py src\api\filters.py -q`
- `PYTHONPATH=src\api python -m pytest tests/test_filter_builder.py -v`
- Result: **26 passed**

## Verdict
**PASS (with remediations applied).**  
No credential leakage found in tracked files.  
Logging and factual consistency issues identified above were remediated in this branch.
