# Squad Team

> Python/FastAPI + React demo for external entitlement-based query-time filtering in Azure AI Search.

## Coordinator

| Name | Role | Notes |
|------|------|-------|
| Squad | Coordinator | Routes work, enforces handoffs and reviewer gates. |

## Members

| Name | Role | Charter | Status |
|------|------|---------|--------|
| Morpheus | Lead | `.squad/agents/morpheus/charter.md` | ✅ Active |
| Trinity | Backend Dev | `.squad/agents/trinity/charter.md` | ✅ Active |
| Niobe | Data/Ingestion Dev | `.squad/agents/niobe/charter.md` | ✅ Active |
| Link | Frontend Dev | `.squad/agents/link/charter.md` | ✅ Active |
| Tank | Tester | `.squad/agents/tank/charter.md` | ✅ Active |
| Scribe | Session Logger | `.squad/agents/scribe/charter.md` | 📋 Silent |
| Ralph | Work Monitor | `.squad/agents/ralph/charter.md` | 🔄 Monitor |
| Rai | RAI Reviewer | `.squad/agents/Rai/charter.md` | 🛡️ RAI |
| Fact Checker | Fact Checker | `.squad/agents/fact-checker/charter.md` | 🔍 Verifier |

## Project Context

- **Owner:** Rob McKenna
- **Project:** azure-ai-search-entitlement-demo
- **Stack:** Python 3.11+, FastAPI, Azure AI Search, Azure OpenAI (optional), React/Vite, pytest
- **Description:** Demonstrates deny-by-default metadata entitlement filtering at retrieval time so unauthorized chunks never reach the LLM.
- **Created:** 2026-07-16T18:51:29.849-04:00
