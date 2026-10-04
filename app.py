import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

st.set_page_config(
    page_title="Multi-Market BESS Revenue Stacking Engine",
    page_icon="🔋",
    layout="wide"
)

st.title("🔋 Multi-Market Revenue Stacking Engine (Day-Ahead & aFRR)")
st.markdown("Advanced MILP optimization dashboard for co-optimized battery energy storage dispatch across energy and reserve markets.")

# Safely import pulp with clear error handling
try:
    import pulp
except ImportError:
    st.error("❌ The `pulp` optimization library is not installed. Please verify your `requirements.txt` file.")
    st.stop()

# Sidebar Controls
st.sidebar.header("Asset & Market Parameters")
bess_power = st.sidebar.slider("BESS Max Power (MW)", 0.5, 5.0, 2.0, 0.5)
bess_energy = st.sidebar.slider("BESS Capacity (MWh)", 1.0, 12.0, 6.0, 0.5)
initial_soc = st.sidebar.slider("Initial SOC (MWh)", 0.5, bess_energy, 3.0, 0.5)
eta = st.sidebar.slider("Round-Trip Efficiency", 0.85, 0.98, 0.95, 0.01)

if st.sidebar.button("Run Multi-Market Optimization"):
    with st.spinner("Solving MILP co-optimization model for Day-Ahead and aFRR markets..."):
        T = list(range(24))
        
        np.random.seed(42)
        da_prices = 50 + 25 * np.sin(2 * np.pi * np.array(T) / 24) + np.random.normal(0, 5, 24)
        da_prices[17:21] += 45
        afrr_prices = 15 + 8 * np.cos(2 * np.pi * np.array(T) / 24) + np.random.uniform(2, 5, 24)
        solar_profile = np.maximum(0, 3.0 * np.sin(np.pi * (np.array(T) - 6) / 12))
        solar_profile[0:6] = 0
        solar_profile[19:] = 0

        model = pulp.LpProblem("Multi_Market_Revenue_Stacking", pulp.LpMaximize)

        bp = float(bess_power)
        be = float(bess_energy)
        init_s = float(initial_soc)

        # Variable generation
        P_charge = {}
        P_discharge = {}
        R_afrr = {}
        SOC = {}
        u_charge = {}
        u_discharge = {}

        for t in T:
            P_charge[t] = pulp.LpVariable(f"P_charge_{t}")
            P_discharge[t] = pulp.LpVariable(f"P_discharge_{t}")
            R_afrr[t] = pulp.LpVariable(f"R_afrr_{t}")
            SOC[t] = pulp.LpVariable(f"SOC_{t}")
            u_charge[t] = pulp.LpVariable(f"u_charge_{t}")
            u_discharge[t] = pulp.LpVariable(f"u_discharge_{t}")

        # 100% Safe objective calculation using pure positive lpSum terms to avoid Rust core operator issues
        revenue_da = pulp.lpSum([
            (P_discharge[t] * float(da_prices[t])) - 
            (P_charge[t] * float(da_prices[t])) + 
            (float(solar_profile[t]) * float(da_prices[t]))
            for t in T
        ])
        revenue_afrr = pulp.lpSum([R_afrr[t] * float(afrr_prices[t]) for t in T])
        degradation_cost = pulp.lpSum([(P_charge[t] + P_discharge[t] + R_afrr[t]) * 1.2 for t in T])

        model += revenue_da + revenue_afrr - degradation_cost
        model += SOC[0] == init_s

        for t in T:
            # Explicit bounds and constraints
            model += P_charge[t] >= 0.0
            model += P_charge[t] <= bp
            model += P_discharge[t] >= 0.0
            model += P_discharge[t] <= bp
            model += R_afrr[t] >= 0.0
            model += R_afrr[t] <= bp
            model += SOC[t] >= 0.5
            model += SOC[t] <= be

            # Binary constraints
            model += u_charge[t] >= 0
            model += u_charge[t] <= 1
            model += u_discharge[t] >= 0
            model += u_discharge[t] <= 1

            model += u_charge[t] + u_discharge[t] <= 1
            model += P_charge[t] <= bp * u_charge[t]
            model += P_discharge[t] <= bp * u_discharge[t]
            model += P_charge[t] + R_afrr[t] <= bp
            model += P_discharge[t] + R_afrr[t] <= bp
            
            if t > 0:
                model += SOC[t] == SOC[t-1] + (float(eta) * P_charge[t] - (1.0 / float(eta)) * P_discharge[t])

        model.solve(pulp.PULP_CBC_CMD(msg=False))

        results = []
        for t in T:
            results.append({
                'hour': t,
                'da_price_eur': float(da_prices[t]),
                'afrr_price_eur': float(afrr_prices[t]),
                'solar_mw': float(solar_profile[t]),
                'charge_mw': pulp.value(P_charge[t]),
                'discharge_mw': pulp.value(P_discharge[t]),
                'afrr_mw': pulp.value(R_afrr[t]),
                'soc_mwh': pulp.value(SOC[t])
            })

        df_opt = pd.DataFrame(results)
        total_rev = pulp.value(model.objective)

        col1, col2, col3 = st.columns(3)
        col1.metric("Optimization Status", pulp.LpStatus[model.status])
        col2.metric("Total Optimal Revenue", f"€{total_rev:,.2f}")
        col3.metric("Peak aFRR Reserve", f"{max([pulp.value(R_afrr[t]) for t in T]):.2f} MW")

        st.subheader("📊 Optimized Multi-Market Dispatch Profile")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df_opt['hour'], df_opt['soc_mwh'], label='Battery SOC (MWh)', color='blue', linewidth=2)
        ax.plot(df_opt['hour'], df_opt['discharge_mw'], label='Discharge Power (MW)', color='green', linestyle='--', linewidth=2)
        ax.plot(df_opt['hour'], df_opt['afrr_mw'], label='aFRR Reserved Capacity (MW)', color='orange', linewidth=2)
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Power / Energy")
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

        st.subheader("📋 Detailed Multi-Market Dispatch Table")
        st.dataframe(df_opt, use_container_width=True)
else:
    st.info("👈 Adjust asset parameters in the sidebar and click **Run Multi-Market Optimization**.")
