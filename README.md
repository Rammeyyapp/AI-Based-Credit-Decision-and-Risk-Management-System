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
