from flask import Flask, render_template, jsonify, request
import json
import sqlite3
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

class GuardianDashboard:
    def __init__(self, db_path="blockchain_logs.db"):
        self.db_path = db_path
        self.stats = {
            "total_anomalies": 0,
            "water_anomalies": 0,
            "fund_anomalies": 0,
            "critical_count": 0,
            "last_update": datetime.utcnow().isoformat()
        }
        self.update_stats()
    
    def update_stats(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM blocks")
            self.stats["total_anomalies"] = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM blocks WHERE data_type='WATER_ANOMALY'")
            self.stats["water_anomalies"] = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM blocks WHERE data_type='FUND_ANOMALY'")
            self.stats["fund_anomalies"] = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM blocks WHERE severity='CRITICAL'")
            self.stats["critical_count"] = cursor.fetchone()[0] or 0
            
            self.stats["last_update"] = datetime.utcnow().isoformat()
            
            conn.close()
        except:
            pass
    
    def get_recent_alerts(self, limit=20):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, data_type, sensor_id, fund_id, anomaly_type, severity 
                FROM blocks 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            alerts = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "timestamp": alert[0],
                    "type": alert[1],
                    "sensor_id": alert[2],
                    "fund_id": alert[3],
                    "anomaly": alert[4],
                    "severity": alert[5],
                    "icon": "💧" if alert[1] == "WATER_ANOMALY" else "💰"
                }
                for alert in alerts
            ]
        except:
            return []
    
    def get_system_health(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp FROM blocks ORDER BY timestamp DESC LIMIT 1")
            last_entry = cursor.fetchone()
            conn.close()
            
            if last_entry:
                last_time = datetime.fromisoformat(last_entry[0])
                time_diff = (datetime.utcnow() - last_time).total_seconds()
                status = "HEALTHY" if time_diff < 300 else "STALE"
            else:
                status = "NO_DATA"
            
            return {
                "status": status,
                "last_data": last_entry[0] if last_entry else "Never",
                "uptime": "100%" if status == "HEALTHY" else "Warning"
            }
        except:
            return {"status": "ERROR", "last_data": "Unknown", "uptime": "0%"}

dashboard = GuardianDashboard()

def background_updater():
    while True:
        dashboard.update_stats()
        time.sleep(60)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    return jsonify(dashboard.stats)

@app.route('/api/alerts')
def get_alerts():
    limit = request.args.get('limit', 20, type=int)
    alerts = dashboard.get_recent_alerts(limit)
    return jsonify({"alerts": alerts, "count": len(alerts)})

@app.route('/api/health')
def get_health():
    return jsonify(dashboard.get_system_health())

@app.route('/api/blockchain/verify')
def verify_blockchain():
    try:
        conn = sqlite3.connect(dashboard.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM blocks")
        block_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM blocks b1
            JOIN blocks b2 ON b1.id = b2.id - 1
            WHERE b1.current_hash != b2.previous_hash
        """)
        integrity_issues = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            "block_count": block_count,
            "integrity_issues": integrity_issues,
            "chain_valid": integrity_issues == 0,
            "timestamp": datetime.utcnow().isoformat()
        })
    except:
        return jsonify({"error": "Database unavailable"})

@app.route('/api/simulate/anomaly')
def simulate_anomaly():
    from datetime import datetime
    import random
    
    anomaly_types = ["WATER_ANOMALY", "FUND_ANOMALY"]
    anomaly_type = random.choice(anomaly_types)
    
    simulated_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": anomaly_type,
        "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
        "message": "Simulated anomaly for testing",
        "sensor_id": f"NODE_{random.randint(100, 999)}" if anomaly_type == "WATER_ANOMALY" else None,
        "fund_id": f"FUND_{random.randint(1000, 9999)}" if anomaly_type == "FUND_ANOMALY" else None,
        "value": random.uniform(0.1, 100.0)
    }
    
    return jsonify({
        "simulated": True,
        "data": simulated_data,
        "note": "This is a simulation - not saved to blockchain"
    })

if __name__ == '__main__':
    updater_thread = threading.Thread(target=background_updater, daemon=True)
    updater_thread.start()
    
    print("🚀 Decentralized Guardian Dashboard")
    print("📊 Dashboard available at: http://localhost:5000")
    print("📈 API endpoints:")
    print("   • /api/stats - System statistics")
    print("   • /api/alerts - Recent alerts")
    print("   • /api/health - System health")
    print("   • /api/blockchain/verify - Blockchain integrity")
    print("   • /api/simulate/anomaly - Test anomaly simulation")
    print("\n⚡ Starting server...")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
