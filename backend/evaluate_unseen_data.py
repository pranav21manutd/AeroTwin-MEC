import os
import sys
import site
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support, confusion_matrix

# Ensure local site packages are available
user_site = site.USER_SITE
if os.path.exists(user_site) and user_site not in sys.path:
    sys.path.insert(0, user_site)

def evaluate_on_unseen_data(csv_path: str = None, num_samples: int = 1000):
    print("=" * 75)
    print(" >>>  DEMONSTRATION: UNSEEN TELEMETRY EVALUATION FOR JUDGES <<<")
    print("=" * 75)


    model_path = os.path.join(os.path.dirname(__file__), "app", "ml_layer", "saved_models", "fault_classifier.joblib")
    if not os.path.exists(model_path):
        print(f"[-] Error: Trained model not found at {model_path}")
        print("Please run `py backend/train_model.py` first to train the model!")
        return

    # 1. Load Trained Model
    model = joblib.load(model_path)
    print(f"[+] Loaded Trained Classifier: {type(model).__name__}")
    print(f"[+] Target Model Classes: {list(model.classes_)}")

    # 2. Acquire Unseen Test Dataset
    if csv_path and os.path.exists(csv_path):
        print(f"\n[*] Loading Unseen Telemetry Dataset from file: {csv_path}")
        df = pd.read_csv(csv_path)
    else:
        print(f"\n[*] Synthesizing {num_samples} fresh UNSEEN test flight telemetry samples (Seed=2026)...")
        np.random.seed(2026) # Fresh seed different from training seed (42)
        
        data = []
        fault_labels = [
            "NORMAL_OPERATION",
            "Coding degradation",
            "Lubrication issues",
            "Sensor drift / failure",
            "Combustion instability",
            "Overheating trends",
            "Abnormal vibration patterns"
        ]

        for _ in range(num_samples):
            label = np.random.choice(fault_labels, p=[0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
            rpm = np.random.normal(3500, 400)
            cht = np.random.normal(135, 10)
            egt = np.random.normal(650, 25)
            oil_p = np.random.normal(45, 4)
            oil_t = np.random.normal(85, 5)
            fuel_flow = np.random.normal(8.5, 0.8)
            vibration = np.random.normal(0.85, 0.15)
            voltage = np.random.normal(48.2, 0.5)

            exp_cht = 25.0 + 105.0 * (60.0 / 100.0)**1.2 + (rpm / 6000.0) * 42.0
            exp_egt = 460.0 + 310.0 * (60.0 / 100.0)**0.9
            exp_oil_p = 25.0 + (rpm / 6000.0) * 45.0

            if label == "Lubrication issues":
                oil_p -= np.random.uniform(18, 30)
                oil_t += np.random.uniform(25, 45)
                vibration += np.random.uniform(0.5, 1.5)
            elif label == "Combustion instability":
                egt += np.random.uniform(60, 120) * np.random.choice([-1, 1])
                cht += np.random.uniform(15, 30)
                fuel_flow *= np.random.uniform(1.2, 1.4)
            elif label == "Sensor drift / failure":
                cht += np.random.uniform(40, 70)
            elif label == "Overheating trends":
                cht += np.random.uniform(50, 90)
                oil_t += np.random.uniform(20, 40)
                egt += np.random.uniform(40, 80)
            elif label == "Abnormal vibration patterns":
                vibration += np.random.uniform(2.5, 4.5)
            elif label == "Coding degradation":
                fuel_flow *= np.random.uniform(1.25, 1.5)
                egt += np.random.uniform(30, 60)

            res_cht = cht - exp_cht
            res_egt = egt - exp_egt
            res_oil_p = oil_p - exp_oil_p

            data.append({
                "piston_rpm": rpm,
                "cht_deg_c": cht,
                "egt_deg_c": egt,
                "oil_pressure_psi": oil_p,
                "oil_temp_deg_c": oil_t,
                "fuel_flow_lph": fuel_flow,
                "vibration_g": vibration,
                "bus_voltage": voltage,
                "res_cht": res_cht,
                "res_egt": res_egt,
                "res_oil_pressure": res_oil_p,
                "label": label
            })
        df = pd.DataFrame(data)

    feature_cols = [
        "piston_rpm", "cht_deg_c", "egt_deg_c", "oil_pressure_psi", 
        "oil_temp_deg_c", "fuel_flow_lph", "vibration_g", "bus_voltage",
        "res_cht", "res_egt", "res_oil_pressure"
    ]

    X_unseen = df[feature_cols]
    y_true = df["label"]

    # 3. Model Inference on Unseen Data
    y_pred = model.predict(X_unseen)
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted')

    # 4. Print Executive Evaluation Table for SIH Judges
    print("\n+" + "-" * 73 + "+")
    print("|                      EVALUATION SUMMARY METRICS                      |")
    print("+" + "-" * 73 + "+")
    print(f"|  OVERALL ACCURACY       : {acc * 100:.2f}%                                      |")
    print(f"|  WEIGHTED PRECISION     : {precision * 100:.2f}%                                      |")
    print(f"|  WEIGHTED RECALL        : {recall * 100:.2f}%                                      |")
    print(f"|  WEIGHTED F1-SCORE      : {f1 * 100:.2f}%                                      |")
    print(f"|  TOTAL UNSEEN SAMPLES   : {len(df)} flight records                            |")
    print("+" + "-" * 73 + "+\n")


    print("DETAILED PER-CLASS EVALUATION METRICS:")
    print("-" * 75)
    print(classification_report(y_true, y_pred, digits=4))

    print("\nCONFUSION MATRIX (True vs Predicted):")
    cm = confusion_matrix(y_true, y_pred, labels=model.classes_)
    cm_df = pd.DataFrame(cm, index=model.classes_, columns=model.classes_)
    print(cm_df.to_string())
    print("=" * 75)

if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    evaluate_on_unseen_data(csv_path=filepath)
