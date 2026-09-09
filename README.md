# Digital Twin using NVIDIA Omniverse

A real-time Digital Twin simulation developed using NVIDIA Omniverse, integrating 3D asset workflows, physics simulation, live data telemetry, and predictive maintenance diagnostics.

---

## 📹 Video Demo

Watch the project in action on LinkedIn:  
👉 **[Watch Digital Twin Video Demo](https://www.linkedin.com/feed/update/urn:li:activity:7491828146757939200/)**

---

## Overview

This project builds a physics-accurate Digital Twin environment in NVIDIA Omniverse. It bridges 3D CAD assets (conveyors, sensors, automated machinery) with live data telemetry and machine learning models to enable real-time monitoring, visual alerting, and automated maintenance diagnostics.

---

## Key Features

* **Real-time 3D Simulation:** USD-based scene management built using NVIDIA Omniverse Composer / Isaac Sim.
* **Dynamic Visual Alarms:** Real-time Python scripts that modify USD PBR material properties (e.g., color changing on conveyor belts) based on incoming PLC data.
* **Predictive AI Diagnostics:** Offline machine learning models for forecasting jam intensity, operational anomalies, and maintenance schedules.
* **Modular Architecture:** Structured separation between USD scene scripts, data generation pipelines, and machine learning models.

---

## Repository Structure

```text
Digital-Twin-using-Nvidia-Omniverse/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── ai_diagnostics/
│   ├── data/
│   │   └── olive_jam_dataset.csv
│   ├── models/
│   │   └── smart_factory_ai.pkl
│   ├── aiDataGenerator.py
│   └── aiModelCreator.py
│
└── omniverse_scripts/
    └── visual_alarms/
        └── alarmBelt.py
