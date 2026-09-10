import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

print("=" * 60)
print("   UAV PROPULSION DIGITAL TWIN - AI/ML MODEL TRAINING SCRIPT")
print("=" * 60)

# ---------------------------------------------------------
# STEP 1: Generate Realistic Training Dataset
# ---------------------------------------------------------
print("\n[*] Step 1: Generating synthetic engine telemetry training dataset...")
np.random.seed(42)
num_samples = 5000

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
    # Choose a random fault state
    label = np.random.choice(fault_labels, p=[0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
    
    # Nominal baseline sensor readings
    rpm = np.random.normal(3500, 400)
    cht = np.random.normal(135, 10)
    egt = np.random.normal(650, 25)
    oil_p = np.random.normal(45, 4)
    oil_t = np.random.normal(85, 5)
    fuel_flow = np.random.normal(8.5, 0.8)
    vibration = np.random.normal(0.85, 0.15)
    voltage = np.random.normal(48.2, 0.5)

    # Physics Twin Expectations
    exp_cht = 25.0 + 105.0 * (60.0 / 100.0)**1.2 + (rpm / 6000.0) * 42.0
    exp_egt = 460.0 + 310.0 * (60.0 / 100.0)**0.9
    exp_oil_p = 25.0 + (rpm / 6000.0) * 45.0

    # Inject Physical Fault Signatures into Sensors & Residuals
    if label == "Lubrication issues":
        oil_p -= np.random.uniform(18, 30)   # Oil pressure drop
        oil_t += np.random.uniform(25, 45)   # Temp runaway
        vibration += np.random.uniform(0.5, 1.5)

    elif label == "Combustion instability":
        egt += np.random.uniform(60, 120) * np.random.choice([-1, 1]) # Fluctuation
        cht += np.random.uniform(15, 30)
        fuel_flow *= np.random.uniform(1.2, 1.4)

    elif label == "Sensor drift / failure":
        cht += np.random.uniform(40, 70)      # High CHT without oil temp correlation

    elif label == "Overheating trends":
        cht += np.random.uniform(50, 90)
        oil_t += np.random.uniform(20, 40)
        egt += np.random.uniform(40, 80)

    elif label == "Abnormal vibration patterns":
        vibration += np.random.uniform(2.5, 4.5) # Mechanical bearing/prop imbalance

    elif label == "Coding degradation":
        fuel_flow *= np.random.uniform(1.25, 1.5)
        egt += np.random.uniform(30, 60)

    # Compute Physics Residual Vectors (Actual - Expected)
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
print(f"[+] Dataset created with {len(df)} samples!")
print("\nDataset Class Distribution:")
print(df["label"].value_counts())

# ---------------------------------------------------------
# STEP 2: Separate Features (X) and Labels (y)
# ---------------------------------------------------------
feature_cols = [
    "piston_rpm", "cht_deg_c", "egt_deg_c", "oil_pressure_psi", 
    "oil_temp_deg_c", "fuel_flow_lph", "vibration_g", "bus_voltage",
    "res_cht", "res_egt", "res_oil_pressure"
]

X = df[feature_cols]
y = df["label"]

# Split into 80% Training Data and 20% Testing Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ---------------------------------------------------------
# STEP 3: Train Random Forest Fault Classifier
# ---------------------------------------------------------
print("\n[*] Step 2: Training Random Forest Fault Classifier...")
classifier = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
classifier.fit(X_train, y_train)

# Evaluate Accuracy
y_pred = classifier.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\n[+] Model Accuracy: {accuracy * 100:.2f}%")
print("\nDetailed Classification Report:")
print(classification_report(y_test, y_pred))

# ---------------------------------------------------------
# STEP 4: Train Isolation Forest Anomaly Detector
# ---------------------------------------------------------
print("\n[*] Step 3: Training Isolation Forest Anomaly Detector...")
# Train only on nominal healthy data
X_healthy = X[y == "NORMAL_OPERATION"]
anomaly_model = IsolationForest(contamination=0.05, random_state=42)
anomaly_model.fit(X_healthy)

# ---------------------------------------------------------
# STEP 5: Save Models to Disk (.joblib files)
# ---------------------------------------------------------
models_dir = os.path.join(os.path.dirname(__file__), "app", "ml_layer", "saved_models")
os.makedirs(models_dir, exist_ok=True)

classifier_path = os.path.join(models_dir, "fault_classifier.joblib")
anomaly_path = os.path.join(models_dir, "anomaly_detector.joblib")

joblib.dump(classifier, classifier_path)
joblib.dump(anomaly_model, anomaly_path)

print(f"\n[+] SUCCESS! Models trained & saved to:")
print(f" -> Classifier: {classifier_path}")
print(f" -> Anomaly Detector: {anomaly_path}")
print("=" * 60)
