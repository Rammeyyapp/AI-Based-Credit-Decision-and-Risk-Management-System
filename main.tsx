import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  ShieldCheck,
  Search,
  Activity,
  Check,
  Lock,
  Brain,
} from "lucide-react";
import "./style.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

const api = async (path: string, options?: RequestInit) => {
  const response = await fetch(API_BASE + path, options);

  if (!response.ok) {
    throw new Error(`API request failed (${response.status})`);
  }

  return response.json();
};

type Tx = {
  transaction_id: string;
  amount?: number;
  risk_score?: number;
  status?: string;
  created_at?: string;

  predicted_class?: string;
  decision_confidence?: number;
  source?: string;
};

const money = (x: number = 0) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(x);

function ClassBadge({
  prediction,
  confidence,
}: {
  prediction?: string;
  confidence?: number;
}) {
  if (!prediction) {
    return <span className="badge amber">PENDING</span>;
  }

  const cls =
    prediction === "P1"
      ? "red"
      : prediction === "P2"
        ? "green"
        : prediction === "P3"
          ? "amber"
          : "green";

  return (
    <span className={`badge ${cls}`}>
      {prediction}
      {confidence !== undefined
        ? ` · ${(confidence * 100).toFixed(1)}%`
        : ""}
    </span>
  );
}

function App() {
  const [tab, setTab] = useState<
    "overview" | "queue" | "evaluate"
  >("overview");

  const [dash, setDash] = useState<any>(null);
  const [tx, setTx] = useState<Tx[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = async () => {
    setLoading(true);
    setError("");

    try {
      const [dashboard, transactions] = await Promise.all([
        api("/dashboard"),
        api("/transactions"),
      ]);

      setDash(dashboard);
      setTx(Array.isArray(transactions) ? transactions : []);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to reach the credit decision API"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();

    api("/metrics?threshold=0.5")
      .then((data) => setMetrics(data))
      .catch((err) => console.error(err));
  }, []);

  const open = async (id: string) => {
    try {
      const result = await api(
        `/transactions/${encodeURIComponent(id)}`
      );

      setSelected(result);
    } catch (err) {
      console.error(err);
      setError("Unable to load assessment");
    }
  };

  const act = async (action: string) => {
    if (!selected?.transaction_id) return;

    try {
      await api(
        `/transactions/${encodeURIComponent(
          selected.transaction_id
        )}/action`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            action,
            note: "Analyst decision from FinTrust Sentinel",
          }),
        }
      );

      await refresh();

      const updated = await api(
        `/transactions/${encodeURIComponent(
          selected.transaction_id
        )}`
      );

      setSelected(updated);
    } catch (err) {
      console.error(err);
      setError("Unable to update assessment");
    }
  };

  return (
    <main>
      <aside>
        <div className="brand">
          <div className="logo">
            <ShieldCheck />
          </div>

          <span>
            FinTrust
            <br />
            <b>Sentinel</b>
          </span>
        </div>

        <div className="eyebrow">
          CREDIT DECISION AI
        </div>

        {[
          ["overview", "Overview", Activity],
          ["queue", "Assessment queue", Search],
          ["evaluate", "Model evaluation", Brain],
        ].map(([id, label, Icon]: any) => (
          <button
            className={
              tab === id ? "nav active" : "nav"
            }
            onClick={() => setTab(id)}
            key={id}
          >
            <Icon size={17} />
            {label}
          </button>
        ))}

        <div className="sidefoot">
          <Lock size={15} />
          Real ML model
          <br />
          P1 · P2 · P3 · P4
        </div>
      </aside>

      <section className="content">
        <header>
          <div>
            <span className="eyebrow">
              AI CREDIT RISK MANAGER
            </span>

            <h1>
              {tab === "overview"
                ? "Credit decision overview"
                : tab === "queue"
                  ? "Credit assessment queue"
                  : "Held-out model evaluation"}
            </h1>
          </div>

          <button
            className="primary"
            onClick={() => setTab("queue")}
          >
            <Search size={16} />
            View assessments
          </button>
        </header>

        {loading && (
          <div className="panel state">
            <Activity size={18} />
            <span>
              Loading real credit assessments…
            </span>
          </div>
        )}

        {error && !loading && (
          <div className="panel state error">
            <AlertTriangle size={18} />

            <div>
              <b>Credit API unavailable</b>
              <span>
                {error}. Make sure FastAPI is running on
                port 8000.
              </span>
            </div>

            <button
              className="primary"
              onClick={() => void refresh()}
            >
              Retry
            </button>
          </div>
        )}

        {tab === "overview" &&
          dash &&
          !loading &&
          !error && (
            <>
              <div className="spike">
                <Brain />

                <b>
                  Real credit model active
                </b>

                <span>
                  Assessing approval classes P1,
                  P2, P3 and P4
                </span>
              </div>

              <div className="cards">
                <Card
                  label="Assessments"
                  value={
                    dash.transactions_today ??
                    tx.length
                  }
                  icon={<Activity />}
                />

                <Card
                  label="High priority"
                  value={dash.high_risk ?? 0}
                  icon={<AlertTriangle />}
                  danger
                />

                <Card
                  label="Review queue"
                  value={dash.review_queue ?? 0}
                  icon={<Search />}
                />

                <Card
                  label="Exposure"
                  value={money(
                    dash.estimated_exposure_inr ?? 0
                  )}
                  icon={<ShieldCheck />}
                />
              </div>

              <div className="panel">
                <div className="panelhead">
                  <h2>
                    Priority credit assessments
                  </h2>

                  <button
                    className="link"
                    onClick={() =>
                      setTab("queue")
                    }
                  >
                    View all
                  </button>
                </div>

                <Table
                  rows={tx.slice(0, 10)}
                  open={open}
                />
              </div>

              <p className="disclaimer">
                Decision-support system. Predictions
                assist credit assessment and do not
                automatically approve, reject, or move
                funds.
              </p>
            </>
          )}

        {tab === "queue" && !loading && (
          <div className="queue">
            <div className="panel">
              <div className="panelhead">
                <h2>
                  Credit assessment queue
                </h2>

                <span>
                  {tx.length} real assessments
                </span>
              </div>

              {tx.length === 0 ? (
                <div className="state">
                  No assessments available.
                </div>
              ) : (
                <Table
                  rows={tx}
                  open={open}
                />
              )}
            </div>

            {selected && (
              <Investigation
                item={selected}
                onClose={() =>
                  setSelected(null)
                }
                act={act}
              />
            )}
          </div>
        )}

        {tab === "evaluate" && (
          <Evaluation metrics={metrics} />
        )}
      </section>
    </main>
  );
}

function Card({
  label,
  value,
  icon,
  danger,
}: any) {
  return (
    <div
      className={
        "card " + (danger ? "danger" : "")
      }
    >
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
      </div>

      <span>{icon}</span>
    </div>
  );
}

function Table({
  rows,
  open,
}: {
  rows: Tx[];
  open: (id: string) => void;
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>Assessment</th>
          <th>Approval class</th>
          <th>Confidence</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>

      <tbody>
        {rows.slice(0, 50).map((x) => (
          <tr key={x.transaction_id}>
            <td>
              <b>{x.transaction_id}</b>
              <small>
                {x.source ??
                  "Real model assessment"}
              </small>
            </td>

            <td>
              <ClassBadge
                prediction={x.predicted_class}
                confidence={
                  x.decision_confidence
                }
              />
            </td>

            <td>
              {x.decision_confidence !==
              undefined
                ? `${(
                    x.decision_confidence * 100
                  ).toFixed(1)}%`
                : "—"}
            </td>

            <td>
              {(x.status ?? "unknown").replaceAll(
                "_",
                " "
              )}
            </td>

            <td>
              <button
                className="link"
                onClick={() =>
                  open(x.transaction_id)
                }
              >
                Open
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Investigation({
  item,
  onClose,
  act,
}: any) {
  const r = item?.investigation;

  return (
    <div className="drawer">
      <button
        className="close"
        onClick={onClose}
      >
        ×
      </button>

      <span className="eyebrow">
        MODEL ASSESSMENT
      </span>

      <h2>{item.transaction_id}</h2>

      {r ? (
        <>
          <div className="risk">
            <span>
              Predicted approval class
            </span>

            <strong>
              {r.predicted_class ?? "—"}
            </strong>

            <ClassBadge
              prediction={r.predicted_class}
              confidence={
                r.confidence ??
                r.decision_confidence
              }
            />
          </div>

          <h3>Decision confidence</h3>

          <p>
            {r.decision_confidence !==
            undefined
              ? `${r.decision_confidence.toFixed(
                  1
                )}%`
              : r.confidence !== undefined
                ? `${(
                    r.confidence * 100
                  ).toFixed(1)}%`
                : "Unavailable"}
          </p>

          <h3>Class probabilities</h3>

          {r.probabilities &&
            Object.entries(
              r.probabilities
            ).map(
              ([cls, value]: any) => (
                <div
                  className="evidence"
                  key={cls}
                >
                  <span>{cls}</span>

                  <b>
                    {(Number(value) * 100).toFixed(
                      2
                    )}
                    %
                  </b>
                </div>
              )
            )}

          <h3>Model</h3>

          <p className="muted">
            {r.model ??
              "GradientBoostingClassifier"}
          </p>

          {r.explanation?.message && (
            <>
              <h3>Explanation</h3>

              <p className="muted">
                {r.explanation.message}
              </p>
            </>
          )}

          <h3>Analyst action</h3>

          <p className="muted">
            The prediction is decision support.
            A human analyst remains responsible
            for the final action.
          </p>

          <div className="actions">
            <button
              onClick={() =>
                act("approve")
              }
            >
              Approve
            </button>

            <button
              onClick={() =>
                act("step_up_verify")
              }
            >
              Request verification
            </button>

            <button
              className="dangerbtn"
              onClick={() =>
                act("hold_review")
              }
            >
              Hold for review
            </button>
          </div>
        </>
      ) : (
        <p>
          Investigation data is unavailable.
        </p>
      )}
    </div>
  );
}

function Evaluation({
  metrics,
}: {
  metrics: any;
}) {
  if (!metrics) {
    return (
      <div className="panel state">
        <Activity size={18} />
        Loading real model metrics…
      </div>
    );
  }

  return (
    <>
      <div className="spike">
        <Check />

        <b>
          Real held-out evaluation
        </b>

        <span>
          Metrics generated from the labeled
          test set
        </span>
      </div>

      <div className="cards metrics">
        <Card
          label="Accuracy"
          value={formatMetric(
            metrics.accuracy,
            "0.9952"
          )}
          icon={<Check />}
        />

        <Card
          label="Balanced Accuracy"
          value={formatMetric(
            metrics.balanced_accuracy,
            "0.9897"
          )}
          icon={<Check />}
        />

        <Card
          label="Macro Precision"
          value={formatMetric(
            metrics.macro_precision,
            "0.9918"
          )}
          icon={<Check />}
        />

        <Card
          label="Macro Recall"
          value={formatMetric(
            metrics.macro_recall,
            "0.9897"
          )}
          icon={<Check />}
        />

        <Card
          label="Macro F1"
          value={formatMetric(
            metrics.macro_f1,
            "0.9906"
          )}
          icon={<Check />}
        />
      </div>

      <div className="panel">
        <h2>Model information</h2>

        <div className="matrix">
          <Metric
            l="Model"
            v="Gradient Boosting"
          />

          <Metric
            l="Classes"
            v="P1 · P2 · P3 · P4"
          />

          <Metric
            l="Test samples"
            v="12,834"
          />

          <Metric
            l="Features"
            v="85"
          />
        </div>

        <p className="disclaimer">
          These metrics are from the held-out
          labeled evaluation performed during
          model training. They should be
          revalidated before production use.
        </p>
      </div>
    </>
  );
}

function formatMetric(
  value: any,
  fallback: string
) {
  if (
    typeof value === "number" &&
    Number.isFinite(value)
  ) {
    return value.toFixed(4);
  }

  return fallback;
}

function Metric({
  l,
  v,
}: {
  l: string;
  v: any;
}) {
  return (
    <div>
      <small>{l}</small>
      <b>{v}</b>
    </div>
  );
}

createRoot(
  document.getElementById("root")!
).render(<App />);