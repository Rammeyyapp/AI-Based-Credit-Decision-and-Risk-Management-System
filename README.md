# AI-Based Credit Decision and Risk Management System

An AI-powered credit decision support system that analyzes internal bank credit-tradeline data and external CIBIL information to predict customer approval classes (P1, P2, P3, and P4).

The system combines a trained Gradient Boosting multiclass classifier with a FastAPI backend and React/Vite web dashboard to provide credit decision predictions, confidence scores, class probabilities, model evaluation results, and out-of-sample predictions.

---

## Project Overview

Financial institutions need to evaluate large numbers of customer credit applications using information such as:

- Credit score
- Income
- Loan and tradeline history
- Delinquencies
- Credit enquiries
- Credit utilization
- Employment information
- Demographic information
- Secured and unsecured credit exposure

Manually analyzing all these attributes for every customer can be time-consuming and difficult to scale.

This project provides an AI-assisted approach that learns patterns from historical labeled credit records and predicts the customer's observed approval class.

### Prediction Classes

The target variable is:

`Approved_Flag`

The model predicts four classes:

- P1
- P2
- P3
- P4

The system does not assume or fabricate business meanings for these labels. They are the actual classes present in the dataset.

---

## Key Features

### 1. Credit Decision Prediction

The trained Gradient Boosting classifier predicts the customer's approval class:

```text
Customer Credit Data
        ↓
Data Preprocessing
        ↓
Gradient Boosting Classifier
        ↓
P1 / P2 / P3 / P4
````

### 2. Decision Confidence

The system uses the model's probability output to display the confidence associated with the predicted class.

Example:

```text
Predicted Class: P2
Confidence: 99.99%
```

The displayed confidence is derived from the model's `predict_proba()` output.

### 3. Class Probabilities

The system exposes the probability distribution across all four classes.

Example:

```text
P1 → 0.01%
P2 → 99.99%
P3 → 0.00%
P4 → 0.00%
```

### 4. Interactive Web Dashboard

The React/Vite frontend provides:

* Credit assessment overview
* Assessment queue
* Predicted approval class
* Decision confidence
* Class probabilities
* Individual assessment investigation
* Model evaluation
* Analyst workflow actions

### 5. Human-in-the-Loop Workflow

The prediction is used as decision support.

An analyst can review an assessment and perform bounded workflow actions such as:

* Approve
* Request verification
* Hold for review

The system does not automatically move money or perform irreversible financial actions.

### 6. Model Evaluation

The application exposes the real held-out model evaluation results, including:

* Accuracy
* Balanced Accuracy
* Macro Precision
* Macro Recall
* Macro F1
* Weighted F1
* Classification report
* Confusion matrix

---

# Dataset

The project uses three datasets.

## 1. Internal Bank Dataset

`Internal_Bank_Dataset.xlsx`

Contains customer-level internal credit-tradeline information such as:

* Active tradelines
* Closed tradelines
* Recently opened/closed tradelines
* Secured loans
* Unsecured loans
* Credit history information
* Loan/tradeline statistics

## 2. External CIBIL Dataset

`External_Cibil_Dataset.xlsx`

Contains customer credit and demographic information such as:

* Credit Score
* Delinquency information
* Credit enquiries
* Credit utilization
* Income
* Age
* Employment duration
* Education
* Gender
* Marital status
* Credit product information
* `Approved_Flag`

## 3. Unseen Dataset

`Unseen_Dataset.xlsx`

Contains 100 customer records without the target label.

It is used for genuine out-of-sample prediction.

Because these records do not contain `Approved_Flag`, they are not used to calculate accuracy or other evaluation metrics.

---

# Data Integration

The internal bank and CIBIL datasets are joined using:

```text
PROSPECTID
```

`PROSPECTID` is used only as an identifier for joining records and is not used as a machine-learning feature.

The resulting customer profile combines internal banking information with external credit information.

---

# Machine Learning Pipeline

The project uses a reproducible machine-learning pipeline.

## Preprocessing

### Numerical Features

* Missing values are handled using median imputation.
* Dataset missing-value sentinels such as `-99999` are converted to missing values.

### Categorical Features

Categorical attributes are handled using:

* Most-frequent imputation
* One-hot encoding
* Unknown-category handling

### Model

The final classifier is:

```text
GradientBoostingClassifier
```

with:

```text
learning_rate = 0.05
n_estimators = 150
random_state = 42
```

The complete preprocessing and model pipeline is stored in:

```text
backend/outputs/credit_model.joblib
```

---

# Model Training and Evaluation

The labeled dataset contains:

```text
Total records: 51,336
```

Target distribution:

```text
P2    32,199
P3     7,452
P4     5,882
P1     5,803
```

The dataset was divided into:

```text
Training samples: 38,502
Testing samples : 12,834
```

The model was evaluated only on the held-out test set.

## Held-Out Results

| Metric            | Result |
| ----------------- | -----: |
| Accuracy          | 99.52% |
| Balanced Accuracy | 98.97% |
| Macro Precision   | 99.18% |
| Macro Recall      | 98.97% |
| Macro F1          | 99.06% |
| Weighted F1       | 99.52% |

### Classification Performance

```text
              precision    recall  f1-score

P1                1.00      0.96      0.98
P2                1.00      1.00      1.00
P3                0.97      1.00      0.98
P4                1.00      1.00      1.00
```

### Confusion Matrix

```text
[[1395    0   56    0]
 [   0 8050    0    0]
 [   4    0 1858    1]
 [   0    0    0 1470]]
```

These are held-out evaluation results and should not be interpreted as a guarantee of production performance.

---

# Feature Importance

The trained Gradient Boosting model identifies the following features among the most influential:

```text
Credit_Score
NETMONTHLYINCOME
time_since_recent_payment
max_unsec_exposure_inPct
recent_level_of_deliq
enq_L3m
time_since_recent_enq
Age_Newest_TL
pct_PL_enq_L6m_of_ever
max_deliq_6mts
```

`Credit_Score` is the dominant feature in the current trained model.

This should be considered when evaluating model robustness, generalization, and potential feature leakage in future versions.

---

# Out-of-Sample Prediction

The 100 records in:

```text
Unseen_Dataset.xlsx
```

are passed through the trained model.

The resulting predictions are stored in:

```text
unseen_predictions.xlsx
```

The system reports:

* Predicted class
* Class probabilities
* Decision confidence

Since the unseen dataset does not contain ground-truth labels, these predictions are not used as model evaluation results.

---

# System Architecture

```text
                    ┌─────────────────────────┐
                    │ Internal Bank Dataset   │
                    └────────────┬────────────┘
                                 │
                                 │ PROSPECTID
                                 │
                    ┌────────────▼────────────┐
                    │ External CIBIL Dataset  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                       Data Integration
                                 │
                                 ▼
                    Feature Preprocessing
                                 │
                                 ▼
                 ┌────────────────────────────┐
                 │ Gradient Boosting Model    │
                 │                            │
                 │ P1 / P2 / P3 / P4          │
                 └─────────────┬──────────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │ FastAPI Backend     │
                    └──────────┬─────────┘
                               │ HTTP
                               ▼
                    ┌────────────────────┐
                    │ React/Vite Web App │
                    └────────────────────┘
                               │
                               ▼
                     Credit Analyst
```

---

# Technology Stack

## Machine Learning

* Python
* Pandas
* NumPy
* Scikit-learn
* Gradient Boosting
* Joblib

## Backend

* FastAPI
* Uvicorn
* Pydantic

## Frontend

* React
* TypeScript
* Vite
* CSS
* Lucide React

## Explainability

* SHAP-compatible model interpretation infrastructure

---

# Project Structure

```text
AI-Based-Credit-Decision-and-Risk-Management-System/
│
├── External_Cibil_Dataset.xlsx
├── Internal_Bank_Dataset.xlsx
├── Unseen_Dataset.xlsx
│
├── credit_model.joblib
├── model_metadata.json
├── unseen_predictions.xlsx
│
├── engine.py
├── main.py
├── models.py
├── train_model.py
├── validate_model.py
├── test_api.py
│
├── main.tsx
├── style.css
├── index.html
├── package.json
├── package-lock.json
├── vite.config.ts
├── tsconfig.json
│
└── README.md
```

---

# Running the Project Locally

## Prerequisites

* Python 3.10+
* Node.js 20+
* npm

## Backend

Open a terminal:

```powershell
cd backend

py -3.10 -m venv venv

.\venv\Scripts\python.exe -m pip install -r requirements.txt

.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

## Frontend

Open a second terminal:

```powershell
cd frontend

npm.cmd install

npm.cmd run dev
```

The frontend will run at:

```text
http://localhost:5173
```

Keep both terminals running.

---

# API Endpoints

The backend provides endpoints including:

```text
GET  /api/health
GET  /api/transactions
GET  /api/transactions/{transaction_id}
POST /api/investigate
POST /api/transactions/{transaction_id}/action
GET  /api/metrics
GET  /api/dashboard
GET  /api/audit
```

---

# Example Prediction

A customer record is submitted to the system:

```text
Credit Score              → 760
Monthly Income            → ₹65,000
Recent Delinquencies      → Low
Credit Utilization        → 25%
Recent Enquiries          → 1
Employment Duration       → 4 years
```

The trained model processes the complete feature vector.

Example output:

```text
Predicted Class: P2

Class Probabilities:
P1 → 0.01%
P2 → 99.99%
P3 → 0.00%
P4 → 0.00%

Decision Confidence:
99.99%
```

The prediction is then displayed through the web dashboard for analyst review.

---

# Responsible AI and Limitations

This system is designed as an AI-assisted decision-support prototype.

Important limitations include:

* The model should be validated on representative production data before deployment.
* Historical dataset bias can affect model predictions.
* The strong influence of Credit_Score should be investigated for robustness and potential target leakage.
* Model calibration should be evaluated before using probabilities as business confidence measures.
* Fairness and lawful-segment evaluation should be performed before production use.
* Data privacy and security controls are required for real customer data.
* P1–P4 labels should be mapped to their official business definitions by the institution using the system.
* Human review should remain available for consequential credit decisions.

The system does not automatically move money or perform irreversible financial actions.

---

# Future Enhancements

Potential future improvements include:

* SHAP-based detailed feature explanations
* Probability calibration
* Model drift monitoring
* Fairness evaluation
* Automated model retraining pipelines
* Production database integration
* Secure authentication and role-based access
* Real-time credit-event ingestion
* Model versioning
* Advanced ensemble models
* Institution-specific mapping of P1–P4 business decisions

---

# Disclaimer

This project is an AI/ML prototype for credit-decision support and research demonstration.

The predictions are generated from the provided datasets and should not be treated as financial advice or an autonomous lending decision.

Production deployment would require appropriate validation, governance, security, privacy, compliance, and human oversight.

```

### One correction before you push it, da

Your GitHub currently has the Excel datasets and the trained `.joblib` model publicly uploaded. **I strongly recommend removing those from the public repository if these are not explicitly licensed for public redistribution.** Even if they're publicly available elsewhere, you should verify their redistribution terms before putting them in your repo.

Also, your README currently says **"Python 3.11+"**, while you've actually verified the project with **Python 3.10**. The new README fixes that mismatch.

After replacing the README, commit/push it. Then your repository description will finally match the **actual application you built**, rather than the old synthetic fraud demo.
```
