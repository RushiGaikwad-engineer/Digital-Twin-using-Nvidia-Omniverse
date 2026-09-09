# Secure Smart Factory Digital Twin Framework for Industrial OT Edge Deployments

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Siemens](https://img.shields.io/badge/Siemens-TIA%20Portal%20V17%20%7C%20PLCSIM%20Advanced-009999?logo=siemens)](https://www.siemens.com)
[![NVIDIA](https://img.shields.io/badge/NVIDIA-Omniverse%20PhysX-76B900?logo=nvidia)](https://developer.nvidia.com/omniverse)
[![OPC UA](https://img.shields.io/badge/OPC--UA-Basic256Sha256-blue)](https://opcfoundation.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B%20%7C%20asyncua-3776AB?logo=python)](https://www.python.org/)

A high-fidelity, real-time cyber-physical **Digital Twin** framework designed to transition industrial bulk-material handling (Olive Oil Mills / *Almazaras*) from reactive control to predictive edge intelligence. 

This framework demonstrates a complete OT-to-IT integration pipeline: connecting a virtualized Siemens S7-1500 controller to an NVIDIA Omniverse OpenUSD 3D stage via an encrypted OPC UA bridge, integrated with real-time Machine Learning diagnostic models.

---🧪 Future Research Scope & Scaling
This repository represents Stage 1 (Hopper & Conveyor Belt) of an end-to-end olive processing facility.

Plant Expansion Roadmap
Stage 2: Olive Washer & De-Leafer

Stage 3: Industrial Grinder

Stage 4: Malaxation Tanks (Batidoras)

Stage 5: Decanter Centrifuge

7-Scenario Control & AI Benchmark Framework
To identify the most computationally efficient and physically safe AI co-pilot for edge deployments, future work benchmarks 7 control paradigms:

Pure Mathematical Baseline (Model Predictive Control / State-Space)

Pure Classical ML (Random Forest Regressor)

Pure Deep Learning (LSTM Time-Series Network)

Pure Reinforcement Learning (PPO Agent)

Hybrid Math + Classical Residual Model

Hybrid Math + Deep Learning (Physics-Informed Neural Network - PINN)

Hybrid Math + Physics-Guided RL

📜 Intellectual Property Notice
This repository contains the public architecture framework, data pipeline scripts, and implementation logic for academic showcase purposes. Proprietary PLC project files (.ap17), CAD geometries, full thesis datasets, and trained model weights are retained in a private repository under university academic IP guidelines.
