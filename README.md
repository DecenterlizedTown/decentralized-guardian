# decentralized-guardian
import random
import time
import json
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SensorSimulator:
    def __init__(self, sensor_id="guardian_node_001", location="village_center"):
        self.sensor_id = sensor_id
        self.location = location
        self.water_params = {
            "pH_range": (6.5, 8.5),
            "turbidity_range": (1, 100),
            "contamination_chance": 0.05,
            "temperature_range": (15, 35)
        }
        self.fund_params = {
            "allocated_range": (5000, 50000),
            "utilized_range": (0.6, 1.2),
            "fraud_chance": 0.03
        }
    
    def generate_water_reading(self):
        anomaly = random.random() < 0.07
        
        if anomaly:
            pH = round(random.uniform(4.0, 6.4) if random.choice([True, False]) else random.uniform(8.6, 9.5), 2)
            turbidity = random.randint(85, 200)
            contaminants = True
        else:
            pH = round(random.uniform(*self.water_params["pH_range"]), 2)
            turbidity = random.randint(*self.water_params["turbidity_range"])
            contaminants = random.random() < self.water_params["contamination_chance"]
        
        return {
            "sensor_id": self.sensor_id,
            "location": self.location,
            "timestamp": datetime.utcnow().isoformat(),
            "water_pH": pH,
            "water_turbidity": turbidity,
            "contaminants_detected": contaminants,
            "temperature_c": round(random.uniform(*self.water_params["temperature_range"]), 1),
            "flow_rate_lps": round(random.uniform(0.5, 5.0), 2),
            "anomaly_flag": anomaly
        }
    
    def generate_fund_reading(self):
        fraud = random.random() < self.fund_params["fraud_chance"]
        
        allocated = random.randint(*self.fund_params["allocated_range"])
        
        if fraud:
            utilized_ratio = random.uniform(0.2, 0.5)
            discrepancy = allocated * random.uniform(0.3, 0.7)
        else:
            utilized_ratio = random.uniform(*self.fund_params["utilized_range"])
            discrepancy = 0
        
        return {
            "fund_id": f"FUND_{random.randint(1000, 9999)}",
            "department": random.choice(["Water", "Sanitation", "Infrastructure", "Health"]),
            "allocated_amount": allocated,
            "utilized_amount": round(allocated * utilized_ratio, 2),
            "discrepancy": round(discrepancy, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "fraud_flag": fraud,
            "location": self.location
        }
    
    def stream_data(self, interval=10):
        try:
            while True:
                water_data = self.generate_water_reading()
                fund_data = self.generate_fund_reading()
                
                yield {
                    "water_reading": water_data,
                    "fund_reading": fund_data,
                    "system_timestamp": datetime.utcnow().isoformat()
                }
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nSensor stream stopped.")

def main():
    print("🚀 Decentralized Guardian - Sensor Simulator")
    print("📍 Simulating water quality and fund allocation data...")
    print("📊 Press Ctrl+C to stop\n")
    
    sensor = SensorSimulator()
    stream = sensor.stream_data(interval=5)
    
    try:
        for i, data in enumerate(stream, 1):
            print(f"\n📦 Reading #{i}")
            print(f"💧 Water: pH={data['water_reading']['water_pH']}, "
                  f"Turbidity={data['water_reading']['water_turbidity']}, "
                  f"Anomaly={data['water_reading']['anomaly_flag']}")
            print(f"💰 Funds: Allocated={data['fund_reading']['allocated_amount']}, "
                  f"Discrepancy={data['fund_reading']['discrepancy']}, "
                  f"Fraud={data['fund_reading']['fraud_flag']}")
    except KeyboardInterrupt:
        print("\n✅ Simulation ended.")

if __name__ == "__main__":
    main()
