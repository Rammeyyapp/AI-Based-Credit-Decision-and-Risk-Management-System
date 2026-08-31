from pathlib import Path
import json
import joblib
import pandas as pd
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "outputs" / "credit_model.joblib"
METADATA_PATH = BASE_DIR / "outputs" / "model_metadata.json"
UNSEEN_PATH = BASE_DIR / "data" / "Unseen_Dataset.xlsx"


class RiskEngine:
    def __init__(self):
        self.model = None
        self.metadata = {}
        self.feature_columns = []
        self.load_model()

    def load_model(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}"
            )

        self.model = joblib.load(MODEL_PATH)

        if METADATA_PATH.exists():
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

        # Recover original model input columns
        try:
            preprocessor = self.model.named_steps["preprocessor"]

            numeric_cols = list(
                preprocessor.transformers_[0][2]
            )

            categorical_cols = list(
                preprocessor.transformers_[1][2]
            )

            self.feature_columns = (
                numeric_cols + categorical_cols
            )

        except Exception as exc:
            print(
                "Could not recover feature columns:",
                exc
            )

    def _prepare_input(self, data):
        """
        Convert incoming data into exactly the feature
        structure expected by the trained model.
        """

        row = pd.DataFrame([data])

        # Remove identifiers / transaction-only fields
        forbidden = {
            "PROSPECTID",
            "transaction_id",
            "created_at",
            "status",
            "risk_score",
            "amount",
        }

        row = row.drop(
            columns=[
                c for c in forbidden
                if c in row.columns
            ],
            errors="ignore",
        )

        # Make sure every model feature exists
        for column in self.feature_columns:
            if column not in row.columns:
                row[column] = np.nan

        # Preserve exact training feature order
        row = row[self.feature_columns]

        # Dataset uses -99999 as missing-value sentinel
        for column in row.columns:
            if pd.api.types.is_numeric_dtype(
                row[column]
            ):
                row[column] = row[column].replace(
                    [-99999, -99999.0],
                    np.nan
                )

        return row

    def predict(self, data):
        if self.model is None:
            raise RuntimeError("Model is not loaded")

        X = self._prepare_input(data)

        # REAL MODEL PREDICTION
        prediction = self.model.predict(X)[0]

        probabilities = None

        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(X)[0]

        # REAL MODEL CLASSES
        classes = list(
            getattr(
                self.model.named_steps["model"],
                "classes_",
                []
            )
        )

        probability_map = {}

        if probabilities is not None:
            probability_map = {
                str(cls): round(float(prob), 6)
                for cls, prob in zip(
                    classes,
                    probabilities
                )
            }

        # Probability remains 0-1
        confidence = (
            float(np.max(probabilities))
            if probabilities is not None
            else None
        )

        return {
            "predicted_class": str(prediction),

            # IMPORTANT:
            # Keep confidence in 0-1 format.
            # Example: 0.9999 = 99.99%
            "confidence": (
                round(confidence, 4)
                if confidence is not None
                else None
            ),

            "probabilities": probability_map,

            "model": "GradientBoostingClassifier",
        }

    def investigate(self, transaction):
        result = self.predict(transaction)

        # 0-1 confidence
        confidence = result["confidence"] or 0.0

        predicted_class = result["predicted_class"]

        # --------------------------------------------------
        # DECISION CONFIDENCE
        # Keep this in 0-1 form.
        #
        # Example:
        # 0.9999 -> frontend can display 99.99%
        # --------------------------------------------------
        decision_confidence = round(
            confidence,
            4
        )

        # Percentage version for text/explanation only
        decision_confidence_pct = round(
            confidence * 100,
            2
        )

        # --------------------------------------------------
        # Dashboard prioritisation signal
        # This is NOT fraud probability.
        # --------------------------------------------------
        class_priority = {
            "P1": 75,
            "P2": 25,
            "P3": 45,
            "P4": 15,
        }

        priority = class_priority.get(
            predicted_class,
            25
        )

        # Keep risk_score on 0-100 scale
        risk_score = round(
            (priority * 0.4)
            + (decision_confidence_pct * 0.6),
            2
        )

        if risk_score >= 65:
            level = "high"
        elif risk_score >= 35:
            level = "medium"
        else:
            level = "low"

        return {
            "risk_score": risk_score,

            "risk_level": level,

            "predicted_class": predicted_class,

            # IMPORTANT:
            # Decimal value for frontend calculations
            "decision_confidence": decision_confidence,

            # Explicit percentage value for display
            "decision_confidence_pct":
                decision_confidence_pct,

            "probabilities":
                result["probabilities"],

            "model":
                result["model"],

            "explanation": {
                "type": "model_prediction",

                "message": (
                    f"Model predicts approval class "
                    f"{predicted_class} with "
                    f"{decision_confidence_pct:.2f}% "
                    f"confidence."
                )
            }
        }

    def metrics(self, threshold=0.5):
        """
        Return the REAL held-out metrics recorded
        during Phase 2.
        """

        metrics = self.metadata.get(
            "metrics",
            {}
        )

        if not metrics:
            return {
                "status":
                    "metrics_not_found",

                "message": (
                    "Run the Phase 2 evaluation "
                    "pipeline to generate model "
                    "metrics."
                )
            }

        return metrics


ENGINE = RiskEngine()


def seeded_transactions():
    """
    Load the real unseen dataset and create dashboard
    investigation records from the model predictions.

    These are NOT fabricated fraud transactions.
    They are out-of-sample credit-decision assessments.
    """

    if not UNSEEN_PATH.exists():
        print(
            f"Unseen dataset not found: "
            f"{UNSEEN_PATH}"
        )
        return []

    df = pd.read_excel(
        UNSEEN_PATH
    )

    transactions = []

    for index, row in df.iterrows():

        data = row.to_dict()

        # Remove NaN values
        clean_data = {}

        for key, value in data.items():

            if pd.isna(value):
                continue

            if isinstance(value, np.generic):
                value = value.item()

            clean_data[key] = value

        try:

            # REAL MODEL INVESTIGATION
            investigation = ENGINE.investigate(
                clean_data
            )

            predicted_class = investigation[
                "predicted_class"
            ]

            # Use available amount if present
            amount = clean_data.get(
                "amount",
                clean_data.get(
                    "NETMONTHLYINCOME",
                    0
                )
            )

            try:
                amount = float(amount)
            except Exception:
                amount = 0.0

            transaction = {

                "transaction_id":
                    f"TXN-UNSEEN-{index + 1000:04d}",

                "amount":
                    round(amount, 2),

                "created_at":
                    pd.Timestamp.utcnow().isoformat(),

                "risk_score":
                    investigation["risk_score"],

                "status":
                    (
                        "needs_review"
                        if investigation["risk_score"] >= 65
                        else "monitored"
                        if investigation["risk_score"] >= 35
                        else "approved"
                    ),

                "predicted_class":
                    predicted_class,

                # DECIMAL 0-1
                "decision_confidence":
                    investigation[
                        "decision_confidence"
                    ],

                # PERCENTAGE 0-100
                "decision_confidence_pct":
                    investigation[
                        "decision_confidence_pct"
                    ],

                "source":
                    "Unseen_Dataset.xlsx"
            }

            transactions.append(
                transaction
            )

        except Exception as exc:

            print(
                f"Prediction failed for row "
                f"{index}: {exc}"
            )

    return transactions