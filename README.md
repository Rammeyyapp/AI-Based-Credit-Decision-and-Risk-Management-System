# FinTrust Sentinel

**FinTrust Sentinel** is a demo-ready, AI-assisted merchant payment-risk console for the Razorpay AI Risk Manager track. It prioritizes suspicious transactions, explains model evidence, detects a high-risk spike, and records a human analyst's bounded decision.

> **Data boundary:** all transactions and labels in this repository are synthetic. The product does not use, claim access to, or imply access to Razorpay private data.

## What it demonstrates

- Transaction-level probabilistic risk scoring with a gradient-boosted ML model.
- Local evidence attribution in a SHAP-compatible format. The demo uses feature perturbation so it remains lightweight and transparent; `shap` is included for a production-grade explainer extension.
- Seeded queue and fraud-spike signal for a reliable live demo.
- Investigation workspace: risk score, influential evidence, recommended action, and analyst decision.
- Bounded “agent” policy: it can summarize model evidence and recommend only `approve`, `step_up_verify`, or `hold_review`. It cannot make the core prediction, move funds, or take irreversible action.
- Audit events for model investigations and human decisions.
- Held-out evaluation: precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, threshold policy, and FP/FN cost estimate.

## Architecture

```text
React analyst console ──HTTP──> FastAPI API
                                   ├─ Synthetic data generator + seeded stream
                                   ├─ Gradient-boosted risk engine
                                   ├─ Evidence/SHAP-compatible attribution
                                   ├─ Evaluation and cost analysis
                                   └─ In-memory audit trail + bounded action policy
```

## Run locally

Prerequisites: Python 3.11+ and Node 20+.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:5173`. The API docs are available at `http://localhost:8000/docs`. Keep both terminals open: Vite forwards the frontend's `/api/*` requests to FastAPI on port 8000.

## Validate

```powershell
cd backend
pytest

cd ..\frontend
npm.cmd run build
```

## Five-minute demo flow

1. **0:00–0:35 — Problem.** Merchants need a defensible way to triage suspicious payments before loss; this demo uses synthetic data only.
2. **0:35–1:20 — Overview.** Show payment volume, high-risk queue, potential exposure, and the seeded risk-spike banner.
3. **1:20–2:40 — Investigate.** Open a red transaction. Explain how the model score is separate from the agent: the model scores; the evidence view explains the top contributing features; the policy recommends a bounded defensive action.
4. **2:40–3:25 — Human control.** Request verification or hold for review. Explain that this changes workflow state only and writes an audit event—no automatic money movement.
5. **3:25–4:30 — Proof.** Open Model evaluation. Adjust the threshold, show precision/recall/F1, ROC-AUC and PR-AUC, confusion matrix, and the explicit FP/FN cost trade-off.
6. **4:30–5:00 — Close.** Highlight the integration seam: replace synthetic ingestion with a merchant-authorized event source, revalidate on representative labelled data, and retain human-review guardrails.

## Production notes

Before production, use merchant-authorized labelled data, establish privacy/legal controls, monitor drift and calibration, evaluate fairness across lawful segments, protect the audit store, and obtain security review. Threshold and cost assumptions are examples, not business advice.
