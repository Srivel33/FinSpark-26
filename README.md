# VeriFusion AI
### Correlating Banking Transactions with Cybersecurity Intelligence

VeriFusion AI is an AI-powered Banking Threat Correlation Platform developed for **FinSpark'26**. The project enhances fraud detection by correlating banking transaction data with cybersecurity telemetry before performing AI-based fraud prediction.

Unlike traditional fraud detection systems that rely only on transaction data, VeriFusion AI combines transaction behaviour with security signals such as login location, IP address, VPN usage, device information, password reset events, failed login attempts, and session details to generate contextual and explainable fraud predictions.

---

## Problem Statement

**AI-Driven Correlation of Cybersecurity Telemetry & Transaction Behaviour**

---

## Key Features

- AI-powered fraud prediction using Random Forest
- Correlation Engine for transaction and cybersecurity telemetry
- Real-time transaction monitoring dashboard
- Risk Score and Confidence Score
- Explainable AI predictions
- Live Detection History
- Interactive Analytics Dashboard
- Synthetic Banking Dataset

---

## Technology Stack

| Category | Technology |
|----------|------------|
| Language | Python |
| Dashboard | Streamlit |
| Machine Learning | Scikit-learn (Random Forest) |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly |
| Model Storage | Joblib |
| IDE | VS Code |

---

## Project Structure

```
VeriFusion-AI/
│
├── dataset/
│   ├── customer_profile.csv
│   ├── transactions.csv
│   ├── security_logs.csv
│   └── ml_training_dataset.csv
│
├── app.py
├── generate_dataset.py
├── train_model.py
├── fraud_model.pkl
├── training_metrics.json
├── requirements.txt
├── README.md
```

---

## Workflow

```
Customer Transaction
        │
        ▼
Cybersecurity Telemetry
        │
        ▼
Correlation Engine
        │
        ▼
Feature Engineering
        │
        ▼
Random Forest AI Model
        │
        ▼
Risk Prediction
        │
        ▼
Recommendation
        │
        ▼
Live Monitoring Dashboard
```

---

## Machine Learning Performance

| Metric | Score |
|---------|------:|
| Accuracy | 98.5% |
| Precision | 100% |
| Recall | 86.36% |
| F1 Score | 92.68% |

---

## How to Run

### Clone the repository

```bash
git clone https://github.com/your-username/VeriFusion-AI.git
cd VeriFusion-AI
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the dashboard

```bash
streamlit run app.py
```

---

## Future Enhancements

- Real-time Banking API Integration
- Kafka-based Transaction Streaming
- Cloud Deployment
- SIEM Integration
- Graph AI for Fraud Detection
- Post-Quantum Cryptography Integration

---

## Team

- Syed Mohammed Shahith S
- Srivel T
- R.K. Mithul Sankar
- Sanjay B

---

## Developed for

**FinSpark'26 – National Banking Cybersecurity Innovation Challenge**

---

## License

This project was developed as a prototype for the FinSpark'26 Hackathon and is intended for educational and demonstration purposes.
