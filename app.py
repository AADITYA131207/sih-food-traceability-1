from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime
import random
import hashlib
import json

app = Flask(__name__)

# --------------------------------------------------
# BATCH INFORMATION
# --------------------------------------------------

batch = {
    "id": "MANGO-M001",
    "product": "Mango",
    "quantity": "100 kg",
    "origin": "Farm F01"
}

# --------------------------------------------------
# SUPPLY CHAIN
# --------------------------------------------------

stages = [
    {
        "name": "FARM",
        "icon": "🌱",
        "location": "Farm F01",
        "time": None
    },
    {
        "name": "TRANSPORT",
        "icon": "🚚",
        "location": "Cold-chain Transport",
        "time": None
    },
    {
        "name": "COLD STORAGE",
        "icon": "❄️",
        "location": "Storage Facility S01",
        "time": None
    },
    {
        "name": "PROCESSING",
        "icon": "🏭",
        "location": "Processing Unit P01",
        "time": None
    },
    {
        "name": "RETAIL",
        "icon": "🏪",
        "location": "Retail Outlet R01",
        "time": None
    }
]

current_stage = 0
stages[0]["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --------------------------------------------------
# SYSTEM DATA
# --------------------------------------------------

readings = []
network_online = True
previous_hash = "GENESIS"
last_sync_time = None
blockchain = []

# --------------------------------------------------
# HASHING
# --------------------------------------------------

def calculate_hash(record, prev_hash_val):
    data = {
        "timestamp": record["timestamp"],
        "temperature": record["temperature"],
        "humidity": record["humidity"],
        "ethylene": record.get("ethylene", 0),
        "gas_raw": record.get("gas_raw", 0),
        "previous_hash": prev_hash_val
    }
    encoded = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()

def calculate_block_hash(block):
    data = {
        "index": block["index"],
        "timestamp": block["timestamp"],
        "transactions": block["transactions"],
        "previous_hash": block["previous_hash"]
    }
    encoded = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()

# --------------------------------------------------
# GENESIS BLOCK
# --------------------------------------------------

def create_genesis_block():
    genesis = {
        "index": 0,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transactions": [
            {
                "batch_id": "SYSTEM",
                "event": "GENESIS"
            }
        ],
        "previous_hash": "0"
    }
    genesis["hash"] = calculate_block_hash(genesis)
    blockchain.append(genesis)

create_genesis_block()

# --------------------------------------------------
# SENSOR SIMULATION
# --------------------------------------------------

def generate_sensor_reading():
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": round(random.uniform(7.5, 10.5), 2),
        "humidity": round(random.uniform(65, 80), 2),
        "gas_raw": random.randint(2500, 4000)
    }

# --------------------------------------------------
# BLOCK CREATION
# --------------------------------------------------

def add_block(record):
    previous_block = blockchain[-1]
    transaction = {
        "batch_id": batch["id"],
        "event": "SENSOR_DATA",
        "timestamp": record["timestamp"],
        "temperature": record["temperature"],
        "humidity": record["humidity"],
        "gas_raw": record.get("gas_raw", 0),
        "data_hash": record["hash"]
    }
    block = {
        "index": len(blockchain),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transactions": [transaction],
        "previous_hash": previous_block["hash"]
    }
    block["hash"] = calculate_block_hash(block)
    blockchain.append(block)
    return block

# --------------------------------------------------
# STAGE BLOCK
# --------------------------------------------------

def add_stage_block(stage):
    previous_block = blockchain[-1]
    transaction = {
        "batch_id": batch["id"],
        "event": "SUPPLY_CHAIN_STAGE",
        "stage": stage["name"],
        "location": stage["location"],
        "timestamp": stage["time"]
    }
    block = {
        "index": len(blockchain),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transactions": [transaction],
        "previous_hash": previous_block["hash"]
    }
    block["hash"] = calculate_block_hash(block)
    blockchain.append(block)

# --------------------------------------------------
# SENSOR SYNC
# --------------------------------------------------

def synchronize_buffered_records():
    global last_sync_time
    synced_count = 0
    for record in readings:
        if record["status"] == "BUFFERED":
            record["status"] = "SYNCED"
            add_block(record)
            synced_count += 1
    if synced_count > 0:
        last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return synced_count

# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")

# --------------------------------------------------
# SENSOR SIMULATION
# --------------------------------------------------

@app.route("/generate", methods=["POST"])
def generate():
    global previous_hash, last_sync_time
    reading = generate_sensor_reading()
    status = "SYNCED" if network_online else "BUFFERED"
    
    reading["status"] = status
    reading["previous_hash"] = previous_hash
    reading["hash"] = calculate_hash(reading, previous_hash)
    previous_hash = reading["hash"]
    readings.append(reading)

    if network_online:
        add_block(reading)
        last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "success": True,
        "reading": reading,
        "network_online": network_online,
        "total_records": len(readings),
        "last_sync_time": last_sync_time
    })

# --------------------------------------------------
# REAL WOKWI ESP32 SENSOR API
# --------------------------------------------------

@app.route("/api/sensor", methods=["POST"])
def receive_sensor_data():
    global previous_hash, last_sync_time
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No JSON data received"
        }), 400

    temperature = data.get("temperature")
    humidity = data.get("humidity")
    gas_raw = data.get("gas_raw", 0)

    if temperature is None or humidity is None:
        return jsonify({
            "success": False,
            "message": "Temperature and humidity are required"
        }), 400

    reading = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": round(float(temperature), 2),
        "humidity": round(float(humidity), 2),
        "gas_raw": int(gas_raw),
        "status": "SYNCED",
        "source": "WOKWI_ESP32",
        "previous_hash": previous_hash
    }

    reading["hash"] = calculate_hash(reading, previous_hash)
    previous_hash = reading["hash"]
    readings.append(reading)
    add_block(reading)

    last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "success": True,
        "message": "ESP32 sensor data received",
        "reading": reading,
        "blockchain_block": blockchain[-1]["index"],
        "last_sync_time": last_sync_time
    })

# --------------------------------------------------
# NETWORK
# --------------------------------------------------

@app.route("/network/<status>", methods=["POST"])
def network(status):
    global network_online
    if status == "on":
        network_online = True
        synced = synchronize_buffered_records()
    else:
        network_online = False
        synced = 0

    return jsonify({
        "network_online": network_online,
        "synced": synced,
        "last_sync_time": last_sync_time
    })

# --------------------------------------------------
# MOVE SUPPLY CHAIN STAGE
# --------------------------------------------------

@app.route("/next-stage", methods=["POST"])
def next_stage():
    global current_stage
    if current_stage < len(stages) - 1:
        current_stage += 1
        stages[current_stage]["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_stage_block(stages[current_stage])

        return jsonify({
            "success": True,
            "stage": stages[current_stage],
            "current_stage": current_stage
        })

    return jsonify({
        "success": False,
        "message": "Batch has reached retail.",
        "current_stage": current_stage
    })

# --------------------------------------------------
# RESET BATCH (RE-RUN FROM FARM)
# --------------------------------------------------

@app.route("/reset-batch", methods=["POST"])
def reset_batch():
    global current_stage
    current_stage = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Reset stage times
    for i in range(len(stages)):
        stages[i]["time"] = None
    stages[0]["time"] = now_str

    # Add Stage Reset Block to Blockchain
    add_stage_block(stages[0])

    return jsonify({
        "success": True,
        "message": "Batch restarted at FARM stage.",
        "current_stage": current_stage,
        "stage": stages[0]
    })

# --------------------------------------------------
# SENSOR INTEGRITY
# --------------------------------------------------

@app.route("/verify", methods=["GET", "POST"])
@app.route("/verify_integrity", methods=["GET", "POST"])
def verify():
    if not readings:
        return jsonify({
            "verified": True,
            "message": "No sensor records generated yet. Ledger is clean."
        })

    previous = "GENESIS"
    for idx, record in enumerate(readings):
        expected_hash = calculate_hash(record, previous)
        if expected_hash != record.get("hash"):
            return jsonify({
                "verified": False,
                "message": f"Sensor tampering detected at record #{idx + 1} (Timestamp: {record.get('timestamp')})",
                "record": record.get("timestamp")
            })
        previous = record["hash"]

    return jsonify({
        "verified": True,
        "message": f"All {len(readings)} sensor records cryptographically verified."
    })

# --------------------------------------------------
# BLOCKCHAIN INTEGRITY
# --------------------------------------------------

@app.route("/verify-blockchain", methods=["GET", "POST"])
def verify_blockchain():
    for i in range(len(blockchain)):
        block = blockchain[i]
        expected_hash = calculate_block_hash(block)
        if expected_hash != block["hash"]:
            return jsonify({
                "verified": False,
                "message": f"Block #{block['index']} has been altered."
            })

        if i > 0:
            previous_block = blockchain[i - 1]
            if block["previous_hash"] != previous_block["hash"]:
                return jsonify({
                    "verified": False,
                    "message": f"Blockchain link broken at block #{block['index']}."
                })

    return jsonify({
        "verified": True,
        "message": f"Blockchain ledger verified ({len(blockchain)} blocks intact)."
    })

# --------------------------------------------------
# TRACEABILITY PAGE
# --------------------------------------------------

@app.route("/trace/<batch_id>")
def trace(batch_id):
    if batch_id != batch["id"]:
        return "Batch not found", 404
    return render_template("trace.html")

# --------------------------------------------------
# ALL DATA
# --------------------------------------------------

@app.route("/data")
def data():
    buffered = sum(1 for record in readings if record["status"] == "BUFFERED")
    synced = sum(1 for record in readings if record["status"] == "SYNCED")

    return jsonify({
        "batch": batch,
        "readings": readings,
        "network_online": network_online,
        "buffered": buffered,
        "synced": synced,
        "last_sync_time": last_sync_time,
        "blockchain": blockchain,
        "stages": stages,
        "current_stage": current_stage
    })

# --------------------------------------------------
# START
# --------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)