# 🥭 Low-Cost IoT Blockchain Nodes for Farm-to-Fork Traceability

## SIH26232

A low-cost IoT-based traceability prototype for monitoring environmental conditions during the farm-to-fork journey of agricultural products.

## Problem

Agricultural products such as mangoes require suitable environmental conditions during transportation and storage.

Network interruptions and lack of continuous monitoring can result in:

- Loss of sensor data
- Difficulty in monitoring environmental conditions
- Difficulty in verifying data integrity

## Proposed Solution

Our system uses an ESP32-based IoT sensor node to collect environmental data such as:

- Temperature
- Humidity
- Gas/VOC

The system generates SHA-256 hashes for sensor records and uses previous-hash linking to provide tamper-evident data integrity.

When network connectivity is unavailable, sensor records are stored locally on an SD card and can be synchronized when connectivity is restored.

## System Architecture

```text
DHT22 + Gas/VOC Sensor
          ↓
        ESP32
          ↓
    SHA-256 Hashing
          ↓
     Wi-Fi / Internet
          ↓
      Flask API
          ↓
    Web Dashboard
          ↓
 Blockchain-inspired
      Ledger
