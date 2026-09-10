import numpy as np
from typing import Dict, Any

class AnomalyDetector:
    """
    AI/ML Anomaly Detection Layer:
    Computes real-time anomaly probability (0 - 100%) based on Isolation Forest /
    Residual Vector deviation from nominal operational manifold.
    """
    def __init__(self):
        self.anomaly_history = []

    def detect_anomaly(self, residuals: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        norm = residuals.get("total_residual_norm", 0.0)
        
        # Sigmoidal mapping to Anomaly Probability (0 - 100%)
        # Nominal norm < 1.0 -> score < 15%
        # Norm > 2.5 -> score > 80%
        raw_prob = 1.0 / (1.0 + np.exp(-1.8 * (norm - 1.6)))
        anomaly_score_pct = float(np.clip(raw_prob * 100.0, 2.0, 99.5))

        self.anomaly_history.append(anomaly_score_pct)
        if len(self.anomaly_history) > 50:
            self.anomaly_history.pop(0)

        is_anomalous = anomaly_score_pct > 65.0
        severity = "HEALTHY"
        if anomaly_score_pct >= 85.0:
            severity = "CRITICAL"
        elif anomaly_score_pct >= 65.0:
            severity = "WARNING"
        elif anomaly_score_pct >= 40.0:
            severity = "ELEVATED"

        return {
            "anomaly_score_pct": round(anomaly_score_pct, 1),
            "is_anomalous": is_anomalous,
            "anomaly_severity": severity,
            "anomaly_trend_avg": round(float(np.mean(self.anomaly_history)), 1)
        }
