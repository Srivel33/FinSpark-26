import os
import sys
import json
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.compose import make_column_selector
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score,
    confusion_matrix, 
    classification_report
)

# ====================================================================
# CONFIGURATION
# ====================================================================

class Config:
    DATASET_PATH = "dataset/ml_training_dataset.csv"
    MODEL_OUT = "fraud_model.pkl"
    REPORT_OUT = "training_report.txt"
    METRICS_OUT = "training_metrics.json"
    TARGET_COL = "is_fraud"
    
    # Model Hyperparameters
    N_ESTIMATORS = 200
    RANDOM_STATE = 42
    CLASS_WEIGHT = "balanced"
    N_JOBS = -1
    TEST_SIZE = 0.2

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def load_data(filepath):
    print("Loading Dataset...")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Critical Error: Dataset not found at {filepath}")
    
    df = pd.read_csv(filepath)
    if df.empty:
        raise ValueError(f"Critical Error: Dataset at {filepath} is empty.")
        
    if Config.TARGET_COL not in df.columns:
        raise KeyError(f"Critical Error: Target column '{Config.TARGET_COL}' not found in dataset.")
        
    return df

def build_pipeline():
    # 1. Automatic Column Detection Setup
    # using dtype_include=np.number guarantees only numeric columns pass to the median imputer.
    num_selector = make_column_selector(dtype_include=np.number)
    cat_selector = make_column_selector(dtype_exclude=np.number)
    
    # 2. Preprocessing Steps
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median"))
    ])
    
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ])
    
    # 3. Column Transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, num_selector),
            ("cat", categorical_transformer, cat_selector)
        ],
        remainder="drop" # Safely drop anything that doesn't fit
    )
    
    # 4. Final Pipeline with Random Forest Classifier
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=Config.N_ESTIMATORS,
            random_state=Config.RANDOM_STATE,
            class_weight=Config.CLASS_WEIGHT,
            n_jobs=Config.N_JOBS
        ))
    ])
    
    return pipeline

def extract_feature_importances(pipeline, top_n=20):
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]
    
    try:
        feature_names = preprocessor.get_feature_names_out()
    except Exception as e:
        print(f"Warning: Could not extract feature names directly: {e}")
        return []

    importances = classifier.feature_importances_
    
    feat_imp = list(zip(feature_names, importances))
    feat_imp.sort(key=lambda x: x[1], reverse=True)
    
    return feat_imp[:top_n]

def save_metrics(metrics_dict, filepath):
    # Sanitize NumPy types to native Python types for JSON serialization
    sanitized_metrics = {
        "accuracy": float(metrics_dict["accuracy"]),
        "precision": float(metrics_dict["precision"]),
        "recall": float(metrics_dict["recall"]),
        "f1_score": float(metrics_dict["f1_score"]),
        "confusion_matrix": metrics_dict["confusion_matrix"].tolist(),
        "train_rows": int(metrics_dict["train_rows"]),
        "test_rows": int(metrics_dict["test_rows"]),
        "fraud_ratio": float(metrics_dict["fraud_ratio"])
    }
    
    with open(filepath, 'w') as f:
        json.dump(sanitized_metrics, f, indent=4)

def generate_report(metrics_dict, feat_importances, cat_cols, num_cols, filepath):
    with open(filepath, 'w') as f:
        f.write("========================================================\n")
        f.write("FinSpark'26 - AI Fraud Detection Training Report\n")
        f.write("========================================================\n\n")
        
        f.write("--- DATASET OVERVIEW ---\n")
        f.write(f"Dataset Shape: {metrics_dict['dataset_shape']}\n")
        f.write(f"Fraud Ratio: {metrics_dict['fraud_ratio']:.4f}\n")
        f.write(f"Total Features: {metrics_dict['feature_count']}\n\n")
        
        f.write("--- AUTOMATIC FEATURE DETECTION ---\n")
        f.write(f"Categorical Columns ({len(cat_cols)}):\n")
        for col in cat_cols:
            f.write(f"  - {col}\n")
            
        f.write(f"\nNumerical Columns ({len(num_cols)}):\n")
        for col in num_cols:
            f.write(f"  - {col}\n")
            
        f.write("\n========================================================\n")
        f.write("--- EVALUATION METRICS ---\n")
        f.write("========================================================\n")
        f.write(f"Accuracy:  {metrics_dict['accuracy']:.4f}\n")
        f.write(f"Precision: {metrics_dict['precision']:.4f}\n")
        f.write(f"Recall:    {metrics_dict['recall']:.4f}\n")
        f.write(f"F1 Score:  {metrics_dict['f1_score']:.4f}\n\n")
        
        f.write("--- CONFUSION MATRIX ---\n")
        f.write(f"{metrics_dict['confusion_matrix']}\n\n")
        
        f.write("--- CLASSIFICATION REPORT ---\n")
        f.write(f"{metrics_dict['classification_report']}\n\n")
        
        f.write("========================================================\n")
        f.write("--- TOP 20 FEATURE IMPORTANCE ---\n")
        f.write("========================================================\n")
        for rank, (feat, imp) in enumerate(feat_importances, 1):
            # Clean up the preprocessor prefixes for better readability
            clean_feat = feat.replace("num__", "").replace("cat__", "")
            f.write(f"{rank:2d}. {clean_feat:<40} {imp:.6f}\n")

# ====================================================================
# MAIN EXECUTION
# ====================================================================

def main():
    try:
        # 1. Load Data
        df = load_data(Config.DATASET_PATH)
        
        dataset_shape = df.shape
        fraud_count = df[Config.TARGET_COL].sum()
        fraud_ratio = fraud_count / len(df)
        
        print(f"Dataset Shape: {dataset_shape}")
        print(f"Fraud Count: {fraud_count} ({(fraud_ratio * 100):.2f}%)")
        
        # 2. Prepare Features and Target
        X = df.drop(columns=[Config.TARGET_COL])
        y = df[Config.TARGET_COL]
        
        # Identify columns strictly for reporting purposes
        num_cols = X.select_dtypes(include=np.number).columns.tolist()
        cat_cols = X.select_dtypes(exclude=np.number).columns.tolist()
        
        # 3. Train Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=Config.TEST_SIZE, 
            stratify=y, 
            random_state=Config.RANDOM_STATE
        )
        
        # 4. Build and Train Pipeline
        print("Training...")
        pipeline = build_pipeline()
        pipeline.fit(X_train, y_train)
        
        # 5. Evaluate
        print("Evaluating...")
        y_pred = pipeline.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)
        cr = classification_report(y_test, y_pred, zero_division=0)
        
        print(f"Accuracy: {acc:.4f} | Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f}")
        
        metrics_dict = {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "confusion_matrix": cm,
            "classification_report": cr,
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "fraud_ratio": fraud_ratio,
            "dataset_shape": dataset_shape,
            "feature_count": X.shape[1]
        }
        
        # 6. Extract Feature Importance
        feat_importances = extract_feature_importances(pipeline, top_n=20)
        
        # 7. Save Artifacts
        print("Saving Model...")
        joblib.dump(pipeline, Config.MODEL_OUT)
        save_metrics(metrics_dict, Config.METRICS_OUT)
        generate_report(metrics_dict, feat_importances, cat_cols, num_cols, Config.REPORT_OUT)
        
        print("Training Complete")

    except Exception as e:
        print(f"\nTraining Failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()