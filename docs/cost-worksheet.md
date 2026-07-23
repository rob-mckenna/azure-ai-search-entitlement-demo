# Cost Worksheet (Azure AI Search Entitlement Demo)

Use this worksheet to estimate monthly run cost for this solution using your own pricing inputs.

---

## 1. Deployment Baseline (from `infra/main.bicep`)

| Component | Config in repo | Notes |
|---|---|---|
| Azure AI Search | `standard`, `replicaCount=1`, `partitionCount=1` | Core retrieval cost driver |
| App Service Plan | Linux `B1`, capacity `1`, `alwaysOn=true` | API host |
| App Service (API) | Python 3.11 on App Service | Uses managed identity for Search |
| Storage Account | `Standard_LRS` (Blob container) | Stores sample docs |
| Log Analytics | `PerGB2018`, retention 30 days | Ingestion + API logs |
| Application Insights | Workspace-based | Telemetry cost follows ingestion volume |
| Azure OpenAI | Optional (`ENABLE_LLM=false` by default) | Only billed if enabled/used |

---

## 2. Workload Inputs (enter expected usage)

| Input | Symbol | Example | Your value |
|---|---:|---:|---:|
| Business days / month | `D` | 22 | |
| Search requests / day | `Qd` | 5,000 | |
| Chat requests / day | `Cd` | 500 | |
| Average search topK | `K` | 8 | |
| Avg chat input tokens / request | `Tin_chat` | 2,000 | |
| Avg chat output tokens / request | `Tout_chat` | 600 | |
| Avg embedding input tokens / chunk | `Tin_emb` | 800 | |
| New/updated chunks ingested / month | `Nchunks` | 25,000 | |
| Log ingestion GB / month | `GB_logs` | 15 | |
| Stored data GB (docs + index growth proxy) | `GB_store` | 20 | |

Derived:

- Monthly search calls: `Qm = D * Qd`
- Monthly chat calls: `Cm = D * Cd`
- Monthly chat input tokens: `Tin_chat_m = Cm * Tin_chat`
- Monthly chat output tokens: `Tout_chat_m = Cm * Tout_chat`
- Monthly embedding tokens: `Tin_emb_m = Nchunks * Tin_emb`

---

## 3. Price Inputs (from Azure Pricing Calculator / Meter rates)

> Enter unit prices for your region and tier.

| Price input | Symbol | Unit | Your price |
|---|---:|---|---:|
| Azure AI Search S1 price | `P_search_s1` | per service-month (1 partition, 1 replica) | |
| Additional Search replica price | `P_search_replica` | per replica-month | |
| Additional Search partition price | `P_search_partition` | per partition-month | |
| App Service B1 | `P_app_b1` | per plan-month | |
| Storage LRS | `P_store_gb` | per GB-month | |
| Log Analytics ingestion | `P_log_gb` | per GB | |
| Chat model input | `P_chat_in` | per 1M tokens | |
| Chat model output | `P_chat_out` | per 1M tokens | |
| Embedding model input | `P_emb_in` | per 1M tokens | |

If `ENABLE_LLM=false` in production, set all OpenAI terms to zero.

---

## 4. Monthly Cost Formulas

### 4.1 Fixed platform cost

- `Cost_search_fixed = P_search_s1`
- `Cost_search_scale = (Replicas - 1) * P_search_replica + (Partitions - 1) * P_search_partition`
- `Cost_api_host = P_app_b1`

### 4.2 Storage and observability

- `Cost_storage = GB_store * P_store_gb`
- `Cost_logs = GB_logs * P_log_gb`

### 4.3 OpenAI (optional)

- `Cost_chat = (Tin_chat_m / 1,000,000) * P_chat_in + (Tout_chat_m / 1,000,000) * P_chat_out`
- `Cost_embed = (Tin_emb_m / 1,000,000) * P_emb_in`

### 4.4 Total

- `Monthly_Total = Cost_search_fixed + Cost_search_scale + Cost_api_host + Cost_storage + Cost_logs + Cost_chat + Cost_embed`

---

## 5. Scenario Table (Low / Expected / High)

| Scenario | Qd | Cd | Nchunks | GB_logs | Replicas | Partitions | Monthly_Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Low | | | | | 1 | 1 | |
| Expected | | | | | 1 | 1 | |
| High | | | | | 2 | 1 | |

---

## 6. Validation Plan (model vs actual)

1. Tag all resources with `solution=entitlement-demo` and `env=<name>`.
2. Capture 7-day actual cost by service in Cost Management.
3. Compare actual vs worksheet by component (Search, App Service, Logs, Storage, OpenAI).
4. Adjust inputs (`Qd`, `Cd`, `GB_logs`, token assumptions) and rerun.
5. Lock alert thresholds:
   - budget warning at 70%
   - budget critical at 90%

---

## 7. Quick notes for this repo

- The deployed baseline includes backend only (App Service API); the React UI is local/static and not separately hosted in `azure.yaml`.
- `postprovision` runs PDF generation + ingestion once after deploy; treat this as one-time/periodic ingestion cost.
- Main runtime cost drivers are typically:
  1. Azure AI Search service tier/capacity
  2. App Service plan
  3. Azure OpenAI tokens (if `ENABLE_LLM=true`)
  4. Log ingestion volume

