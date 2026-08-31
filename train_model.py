from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import GradientBoostingClassifier


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


INTERNAL_FILE = DATA_DIR / "Internal_Bank_Dataset.xlsx"
CIBIL_FILE = DATA_DIR / "External_Cibil_Dataset.xlsx"
UNSEEN_FILE = DATA_DIR / "Unseen_Dataset.xlsx"


def clean_dataframe(df):
    """Convert dataset missing-value sentinels to actual NaN."""
    df = df.copy()
    df = df.replace([-99999, -99999.0], np.nan)
    return df


def main():
    print("=" * 70)
    print("FINTRUST SENTINEL - REAL CREDIT MODEL TRAINING")
    print("=" * 70)

    print("\nLoading datasets...")

    internal = pd.read_excel(INTERNAL_FILE)
    cibil = pd.read_excel(CIBIL_FILE)
    unseen = pd.read_excel(UNSEEN_FILE)

    print(f"Internal bank shape : {internal.shape}")
    print(f"CIBIL shape         : {cibil.shape}")
    print(f"Unseen shape        : {unseen.shape}")

    # ---------------------------------------------------------
    # Validate keys
    # ---------------------------------------------------------

    if "PROSPECTID" not in internal.columns:
        raise ValueError("PROSPECTID missing from Internal_Bank_Dataset.xlsx")

    if "PROSPECTID" not in cibil.columns:
        raise ValueError("PROSPECTID missing from External_Cibil_Dataset.xlsx")

    if "Approved_Flag" not in cibil.columns:
        raise ValueError("Approved_Flag missing from External_Cibil_Dataset.xlsx")

    print("\nChecking PROSPECTID uniqueness...")

    internal_duplicates = internal["PROSPECTID"].duplicated().sum()
    cibil_duplicates = cibil["PROSPECTID"].duplicated().sum()

    print(f"Internal duplicate IDs: {internal_duplicates}")
    print(f"CIBIL duplicate IDs   : {cibil_duplicates}")

    if internal_duplicates > 0 or cibil_duplicates > 0:
        raise ValueError(
            "PROSPECTID is not unique. Fix duplicate customer IDs before training."
        )

    # ---------------------------------------------------------
    # Clean
    # ---------------------------------------------------------

    internal = clean_dataframe(internal)
    cibil = clean_dataframe(cibil)
    unseen = clean_dataframe(unseen)

    # ---------------------------------------------------------
    # Merge
    # ---------------------------------------------------------

    print("\nMerging Internal Bank + CIBIL data...")

    merged = pd.merge(
        internal,
        cibil,
        on="PROSPECTID",
        how="inner",
        suffixes=("_internal", "_cibil"),
        validate="one_to_one",
    )

    print(f"Merged dataset shape: {merged.shape}")

    if len(merged) != len(cibil):
        raise ValueError(
            "Join coverage is incomplete. Not all CIBIL records matched."
        )

    # ---------------------------------------------------------
    # Target
    # ---------------------------------------------------------

    target = "Approved_Flag"

    print("\nTarget distribution:")
    print(merged[target].value_counts(dropna=False))

    merged = merged.dropna(subset=[target])

    # ---------------------------------------------------------
    # Remove identifiers / target
    # ---------------------------------------------------------

    X = merged.drop(columns=[target, "PROSPECTID"])
    y = merged[target].astype(str)

    # ---------------------------------------------------------
    # Identify feature types
    # ---------------------------------------------------------

    numeric_features = X.select_dtypes(
        include=["number", "bool"]
    ).columns.tolist()

    categorical_features = [
        col for col in X.columns
        if col not in numeric_features
    ]

    print("\nFeature summary:")
    print(f"Total features     : {len(X.columns)}")
    print(f"Numeric features   : {len(numeric_features)}")
    print(f"Categorical        : {len(categorical_features)}")

    # ---------------------------------------------------------
    # Train/test split
    # ---------------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    print("\nTrain/test:")
    print(f"Training samples   : {len(X_train)}")
    print(f"Testing samples    : {len(X_test)}")

    # ---------------------------------------------------------
    # Preprocessing
    # ---------------------------------------------------------

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            )
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                numeric_features,
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_features,
            ),
        ],
        remainder="drop",
    )

    # ---------------------------------------------------------
    # Model
    # ---------------------------------------------------------

    model = GradientBoostingClassifier(
        random_state=42,
        n_estimators=150,
        learning_rate=0.05,
        max_depth=3,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    print("\nTraining Gradient Boosting model...")

    pipeline.fit(X_train, y_train)

    print("Training complete.")

    # ---------------------------------------------------------
    # Evaluation
    # ---------------------------------------------------------

    print("\nEvaluating held-out test set...")

    predictions = pipeline.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    balanced_accuracy = balanced_accuracy_score(y_test, predictions)

    macro_precision = precision_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0,
    )

    macro_recall = recall_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0,
    )

    macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0,
    )

    weighted_f1 = f1_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0,
    )

    print("\n" + "=" * 70)
    print("REAL HELD-OUT METRICS")
    print("=" * 70)

    print(f"Accuracy          : {accuracy:.4f}")
    print(f"Balanced Accuracy : {balanced_accuracy:.4f}")
    print(f"Macro Precision   : {macro_precision:.4f}")
    print(f"Macro Recall      : {macro_recall:.4f}")
    print(f"Macro F1          : {macro_f1:.4f}")
    print(f"Weighted F1       : {weighted_f1:.4f}")

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    classes = list(pipeline.named_steps["model"].classes_)

    cm = confusion_matrix(
        y_test,
        predictions,
        labels=classes,
    )

    print("Confusion matrix:")
    print(cm)

    # ---------------------------------------------------------
    # Save model
    # ---------------------------------------------------------

    model_path = OUTPUT_DIR / "credit_model.joblib"

    joblib.dump(
        pipeline,
        model_path,
    )

    print(f"\nModel saved to: {model_path}")

    # ---------------------------------------------------------
    # Save metadata
    # ---------------------------------------------------------

    metadata = {
        "target": target,
        "classes": classes,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "total_labeled_samples": int(len(merged)),
        "feature_count_before_encoding": int(len(X.columns)),
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "metrics": {
            "accuracy": float(accuracy),
            "balanced_accuracy": float(balanced_accuracy),
            "macro_precision": float(macro_precision),
            "macro_recall": float(macro_recall),
            "macro_f1": float(macro_f1),
            "weighted_f1": float(weighted_f1),
        },
        "confusion_matrix": cm.tolist(),
    }

    metadata_path = OUTPUT_DIR / "model_metadata.json"

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(
            metadata,
            f,
            indent=2,
        )

    print(f"Metadata saved to: {metadata_path}")

    # ---------------------------------------------------------
    # Score unseen data
    # ---------------------------------------------------------

    print("\nScoring Unseen_Dataset.xlsx...")

    unseen_features = unseen.copy()

    if "Approved_Flag" in unseen_features.columns:
        unseen_features = unseen_features.drop(
            columns=["Approved_Flag"]
        )

    if "PROSPECTID" in unseen_features.columns:
        unseen_features = unseen_features.drop(
            columns=["PROSPECTID"]
        )

    # Make sure unseen data has every training feature.
    for column in X.columns:
        if column not in unseen_features.columns:
            unseen_features[column] = np.nan

    # Ignore columns that weren't present during training.
    unseen_features = unseen_features[
        X.columns
    ]

    unseen_predictions = pipeline.predict(
        unseen_features
    )

    unseen_probabilities = pipeline.predict_proba(
        unseen_features
    )

    unseen_confidence = unseen_probabilities.max(
        axis=1
    )

    unseen_output = unseen.copy()

    unseen_output["Predicted_Approved_Flag"] = (
        unseen_predictions
    )

    unseen_output["Prediction_Confidence"] = (
        unseen_confidence
    )

    unseen_output_path = (
        OUTPUT_DIR / "unseen_predictions.xlsx"
    )

    unseen_output.to_excel(
        unseen_output_path,
        index=False,
    )

    print(
        f"Unseen predictions saved to: "
        f"{unseen_output_path}"
    )

    print("\n" + "=" * 70)
    print("PHASE 2 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()