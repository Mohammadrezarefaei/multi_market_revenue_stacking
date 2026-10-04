# 🔋 Multi-Market BESS Revenue Stacking Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://multimarketrevenuestacking-2ajziw8zroapp7sdxxtacgp.streamlit.app/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Optimization](https://img.shields.io/badge/MILP-PuLP-orange.svg)](https://coin-or.github.io/pulp/)

An advanced Mixed-Integer Linear Programming (MILP) optimization dashboard for co-optimized Battery Energy Storage System (BESS) dispatch across Day-Ahead energy and aFRR (automatic Frequency Restoration Reserve) markets.

## 📌 Overview

This project provides an interactive web-based engine to evaluate and maximize the revenue of a grid-connected battery system. By co-optimizing across two different markets simultaneously, the model determines the most profitable hours to charge, discharge, or reserve capacity while respecting the physical constraints of the asset.

**Live Application:** [Launch Streamlit App](https://multimarketrevenuestacking-2ajziw8zroapp7sdxxtacgp.streamlit.app/)

## ✨ Key Features

* **Multi-Market Co-Optimization:** Simultaneously stacks revenues from Day-Ahead (energy arbitrage) and aFRR (ancillary services) markets.
* **Interactive Parameter Tuning:** Adjust BESS Max Power (MW), Capacity (MWh), Initial State of Charge (SOC), and Round-Trip Efficiency dynamically via the sidebar.
* **Robust Mathematical Engine:** Built with a highly stable implementation of the `PuLP` library. The model utilizes low-level affine expression APIs to ensure 100% compatibility across all CBC/Rust-core solver versions, preventing common operator-overloading bugs in cloud environments.
* **Degradation Cost Modeling:** Incorporates cycling and degradation penalties to prevent unprofitable marginal dispatch.
* **Dynamic Visualization:** Generates real-time, interactive dispatch profiles showing SOC evolution alongside charging, discharging, and reserved capacity behaviors.

## 🧮 Mathematical Model (MILP)

The core engine relies on a Linear Programming formulation:
* **Objective:** Maximize (Day-Ahead Revenue + aFRR Revenue - Degradation Costs).
* **State of Charge (SOC) Constraints:** Tracks energy levels hour-by-hour, accounting for round-trip efficiency ($\eta$).
* **Power Limits:** Ensures that actual dispatch plus reserved aFRR capacity never exceeds the physical inverter limits (`P_charge + R_afrr <= Max_Power`).
* **Binary Logic (Optional/Implicit):** Prevents simultaneous charging and discharging via strict objective penalties and physical capacity bounds.

## 🛠️ Technology Stack

* **Frontend/UI:** [Streamlit](https://streamlit.io/)
* **Optimization Solver:** [PuLP](https://coin-or.github.io/pulp/) (CBC Solver)
* **Data Processing:** Pandas, NumPy
* **Visualization:** Matplotlib

## 🚀 Local Installation & Usage

To run this project locally on your machine:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Mohammadrezarefaei/multi_market_revenue_stacking.git](https://github.com/Mohammadrezarefaei/multi_market_revenue_stacking.git)
   cd multi_market_revenue_stacking
