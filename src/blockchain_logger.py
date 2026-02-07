import hashlib
import json
import time
from datetime import datetime
import sqlite3
import os

class BlockchainLogger:
    def __init__(self, db_path="blockchain_logs.db"):
        self.db_path = db_path
        self.init_db()
        self.chain = self.load_chain()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                previous_hash TEXT,
                current_hash TEXT UNIQUE,
                timestamp TEXT,
                data_type TEXT,
                sensor_id TEXT,
                fund_id TEXT,
                anomaly_type TEXT,
                severity TEXT,
                data TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def load_chain(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blocks ORDER BY id DESC LIMIT 1")
        last_block = cursor.fetchone()
        conn.close()
        return last_block or None
    
    def create_block(self, data_type, sensor_id=None, fund_id=None, anomaly_type=None, severity="LOW", data=None):
        timestamp = datetime.utcnow().isoformat()
        
        previous_hash = self.chain[2] if self.chain else "0" * 64
        
        block_data = {
            "previous_hash": previous_hash,
            "timestamp": timestamp,
            "data_type": data_type,
            "sensor_id": sensor_id,
            "fund_id": fund_id,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "data": data
        }
        
        block_string = json.dumps(block_data, sort_keys=True)
        current_hash = hashlib.sha256(block_string.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO blocks 
            (previous_hash, current_hash, timestamp, data_type, sensor_id, fund_id, anomaly_type, severity, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (previous_hash, current_hash, timestamp, data_type, sensor_id, fund_id, anomaly_type, severity, json.dumps(data)))
        conn.commit()
        conn.close()
        
        self.chain = (cursor.lastrowid, previous_hash, current_hash)
        
        return {
            "block_id": cursor.lastrowid,
            "previous_hash": previous_hash,
            "current_hash": current_hash,
            "timestamp": timestamp,
            "integrity": "VERIFIED"
        }
    
    def log_water_anomaly(self, anomaly_data):
        return self.create_block(
            data_type="WATER_ANOMALY",
            sensor_id=anomaly_data.get("sensor_id"),
            anomaly_type=anomaly_data.get("anomalies", [{}])[0][0] if anomaly_data.get("anomalies") else None,
            severity=anomaly_data.get("severity", "LOW"),
            data=anomaly_data
        )
    
    def log_fund_anomaly(self, anomaly_data):
        return self.create_block(
            data_type="FUND_ANOMALY",
            fund_id=anomaly_data.get("fund_id"),
            anomaly_type=anomaly_data.get("anomalies", [{}])[0][0] if anomaly_data.get("anomalies") else None,
            severity=anomaly_data.get("severity", "LOW"),
            data=anomaly_data
        )
    
    def verify_chain(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blocks ORDER BY id")
        blocks = cursor.fetchall()
        conn.close()
        
        if not blocks:
            return {"status": "EMPTY_CHAIN", "valid": True}
        
        for i in range(1, len(blocks)):
            prev_block = blocks[i-1]
            curr_block = blocks[i]
            
            if curr_block[1] != prev_block[2]:
                return {
                    "status": "INVALID_CHAIN",
                    "block_id": curr_block[0],
                    "expected_previous": prev_block[2],
                    "actual_previous": curr_block[1],
                    "valid": False
                }
        
        return {"status": "VALID_CHAIN", "block_count": len(blocks), "valid": True}
    
    def get_recent_logs(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blocks ORDER BY id DESC LIMIT ?", (limit,))
        logs = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": log[0],
                "previous_hash": log[1],
                "current_hash": log[2],
                "timestamp": log[3],
                "data_type": log[4],
                "sensor_id": log[5],
                "fund_id": log[6],
                "anomaly_type": log[7],
                "severity": log[8]
            }
            for log in logs
        ]

def test_blockchain():
    logger = BlockchainLogger("test_logs.db")
    
    print("⛓️ Testing Blockchain Logger")
    
    water_anomaly = {
        "sensor_id": "node_001",
        "timestamp": datetime.utcnow().isoformat(),
        "anomalies": [("LOW_PH", 5.8, "pH below limit")],
        "severity": "HIGH"
    }
    
    fund_anomaly = {
        "fund_id": "FUND_7890",
        "timestamp": datetime.utcnow().isoformat(),
        "anomalies": [("HIGH_DISCREPANCY", 0.45, "45% discrepancy")],
        "severity": "CRITICAL"
    }
    
    block1 = logger.log_water_anomaly(water_anomaly)
    print(f"✅ Water anomaly logged: {block1['current_hash'][:16]}...")
    
    block2 = logger.log_fund_anomaly(fund_anomaly)
    print(f"✅ Fund anomaly logged: {block2['current_hash'][:16]}...")
    
    verification = logger.verify_chain()
    print(f"🔗 Chain verification: {verification}")
    
    logs = logger.get_recent_logs(5)
    print(f"📜 Recent logs: {len(logs)} entries")
    
    os.remove("test_logs.db")
    print("🧹 Test database cleaned")

if __name__ == "__main__":
    test_blockchain()
