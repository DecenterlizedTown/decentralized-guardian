import json
import numpy as np
from datetime import datetime
import hashlib
import pickle
import os
from collections import deque

class AnomalyDetector:
    def __init__(self, model_path=None):
        self.water_thresholds = {
            "pH_low": 6.5,
            "pH_high": 8.5,
            "turbidity_high": 80,
            "contaminant_zero_tolerance": True
        }
        self.fund_thresholds = {
            "discrepancy_ratio": 0.3,
            "utilization_low": 0.4,
            "utilization_high": 1.1,
            "rapid_change": 0.5
        }
        self.history = deque(maxlen=100)
        self.model = self.load_model(model_path) if model_path else None
    
    def load_model(self, path):
        try:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    return pickle.load(f)
        except:
            pass
        return None
    
    def detect_water_anomaly(self, water_data):
        anomalies = []
        
        if water_data['water_pH'] < self.water_thresholds['pH_low']:
            anomalies.append(("LOW_PH", water_data['water_pH'], "pH below safe limit"))
        elif water_data['water_pH'] > self.water_thresholds['pH_high']:
            anomalies.append(("HIGH_PH", water_data['water_pH'], "pH above safe limit"))
        
        if water_data['water_turbidity'] > self.water_thresholds['turbidity_high']:
            anomalies.append(("HIGH_TURBIDITY", water_data['water_turbidity'], "water cloudy/contaminated"))
        
        if water_data['contaminants_detected'] and self.water_thresholds['contaminant_zero_tolerance']:
            anomalies.append(("CONTAMINANTS", True, "harmful substances detected"))
        
        if self.model:
            features = np.array([[water_data['water_pH'], water_data['water_turbidity']]])
            prediction = self.model.predict(features)
            if prediction[0] == 1:
                anomalies.append(("ML_ANOMALY", "model_flag", "AI detected unusual pattern"))
        
        return {
            "sensor_id": water_data['sensor_id'],
            "timestamp": water_data['timestamp'],
            "anomalies": anomalies,
            "severity": "HIGH" if len(anomalies) > 1 else "MEDIUM" if anomalies else "LOW",
            "data_hash": self.hash_data(water_data)
        }
    
    def detect_fund_anomaly(self, fund_data):
        anomalies = []
        
        if fund_data['discrepancy'] > 0:
            ratio = fund_data['discrepancy'] / fund_data['allocated_amount']
            if ratio > self.fund_thresholds['discrepancy_ratio']:
                anomalies.append(("HIGH_DISCREPANCY", ratio, f"{ratio:.1%} funds unaccounted"))
        
        utilization = fund_data['utilized_amount'] / fund_data['allocated_amount']
        if utilization < self.fund_thresholds['utilization_low']:
            anomalies.append(("LOW_UTILIZATION", utilization, f"only {utilization:.1%} funds used"))
        elif utilization > self.fund_thresholds['utilization_high']:
            anomalies.append(("OVER_UTILIZATION", utilization, f"{utilization:.1%} exceeds allocation"))
        
        self.history.append(fund_data)
        if len(self.history) > 10:
            recent = list(self.history)[-10:]
            avg_discrepancy = np.mean([f['discrepancy'] for f in recent])
            if fund_data['discrepancy'] > avg_discrepancy * 2:
                anomalies.append(("SPIKE_DISCREPANCY", fund_data['discrepancy'], "sudden increase in discrepancies"))
        
        return {
            "fund_id": fund_data['fund_id'],
            "department": fund_data['department'],
            "timestamp": fund_data['timestamp'],
            "anomalies": anomalies,
            "severity": "HIGH" if fund_data['fraud_flag'] else "MEDIUM" if anomalies else "LOW",
            "allocated": fund_data['allocated_amount'],
            "discrepancy": fund_data['discrepancy'],
            "data_hash": self.hash_data(fund_data)
        }
    
    def hash_data(self, data):
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def analyze_stream(self, sensor_stream):
        for data_packet in sensor_stream:
            water_result = self.detect_water_anomaly(data_packet['water_reading'])
            fund_result = self.detect_fund_anomaly(data_packet['fund_reading'])
            
            yield {
                "timestamp": datetime.utcnow().isoformat(),
                "water_anomaly": water_result,
                "fund_anomaly": fund_result,
                "combined_severity": "CRITICAL" if water_result['severity'] == "HIGH" and fund_result['severity'] == "HIGH"
                                     else water_result['severity'] if water_result['severity'] != "LOW" else fund_result['severity']
            }

def test_detection():
    detector = AnomalyDetector()
    
    water_data = {
        "sensor_id": "test_sensor",
        "timestamp": datetime.utcnow().isoformat(),
        "water_pH": 5.8,
        "water_turbidity": 95,
        "contaminants_detected": True,
        "temperature_c": 22.5,
        "flow_rate_lps": 2.3,
        "anomaly_flag": True
    }
    
    fund_data = {
        "fund_id": "FUND_4567",
        "department": "Water",
        "allocated_amount": 25000,
        "utilized_amount": 12000,
        "discrepancy": 10000,
        "timestamp": datetime.utcnow().isoformat(),
        "fraud_flag": True,
        "location": "test_location"
    }
    
    print("🧪 Testing Anomaly Detector")
    print("💧 Water Analysis:", detector.detect_water_anomaly(water_data))
    print("💰 Fund Analysis:", detector.detect_fund_anomaly(fund_data))
    print("✅ Test completed")

if __name__ == "__main__":
    test_detection()
