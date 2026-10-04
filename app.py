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
st.markdown("Advanced LP optimization dashboard for co-optimized battery energy storage dispatch across energy and reserve markets.")

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
    with st.spinner("Solving LP co-optimization model for Day-Ahead and aFRR markets..."):
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
        eta_f = float(eta)

        # 1. Safest Variable Generation (Only defining names, NO attribute setting)
        P_charge, P_discharge, R_afrr, SOC = {}, {}, {}, {}

        for t in T:
            P_charge[t] = pulp.LpVariable(f"P_charge_{t}")
            P_discharge[t] = pulp.LpVariable(f"P_discharge_{t}")
            R_afrr[t] = pulp.LpVariable(f"R_afrr_{t}")
            SOC[t] = pulp.LpVariable(f"SOC_{t}")

        # 2. Objective Function via Low-Level API Dictionary (Zero operator overloading)
        obj_dict = {}
        for t in T:
            # Objective: Maximize (P_discharge - P_charge) * da_price + R_afrr * afrr_price - 1.2 * (P_charge + P_discharge + R_afrr)
            obj_dict[P_discharge[t]] = float(da_prices[t]) - 1.2
            obj_dict[P_charge[t]] = -float(da_prices[t]) - 1.2
            obj_dict[R_afrr[t]] = float(afrr_prices[t]) - 1.2
            
        constant_term = sum(float(solar_profile[t]) * float(da_prices[t]) for t in T)
        model.objective = pulp.LpAffineExpression(obj_dict, constant=constant_term)

        # 3. Constraints via Low-Level API (sense: 1 is >=, -1 is <=, 0 is ==)
        model += pulp.LpConstraint(pulp.LpAffineExpression({SOC[0]: 1.0}), sense=0, rhs=init_s)

        for t in T:
            # Bounds enforced purely through constraints
            model += pulp.LpConstraint(pulp.LpAffineExpression({P_charge[t]: 1.0}), sense=1, rhs=0.0)
            model += pulp.LpConstraint(pulp.LpAffineExpression({P_charge[t]: 1.0}), sense=-1, rhs=bp)
            
            model += pulp.LpConstraint(pulp.LpAffineExpression({P_discharge[t]: 1.0}), sense=1, rhs=0.0)
            model += pulp.LpConstraint(pulp.LpAffineExpression({P_discharge[t]: 1.0}), sense=-1, rhs=bp)
            
            model += pulp.LpConstraint(pulp.LpAffineExpression({R_afrr[t]: 1.0}), sense=1, rhs=0.0)
            model += pulp.LpConstraint(pulp.LpAffineExpression({R_afrr[t]: 1.0}), sense=-1, rhs=bp)
            
            model += pulp.LpConstraint(pulp.LpAffineExpression({SOC[t]: 1.0}), sense=1, rhs=0.5)
            model += pulp.LpConstraint(pulp.LpAffineExpression({SOC[t]: 1.0}), sense=-1, rhs=be)

            # Operational constraints
            model += pulp.LpConstraint(pulp.LpAffineExpression({P_charge[t]: 1.0, R_afrr[t]: 1.0}), sense=-1, rhs=bp)
            model += pulp.LpConstraint(pulp.LpAffineExpression({P_discharge[t]: 1.0, R_afrr[t]: 1.0}), sense=-1, rhs=bp)
            
            if t > 0:
                # SOC[t] - SOC[t-1] - eta * P_charge[t] + (1/eta) * P_discharge[t] == 0
                model += pulp.LpConstraint(
                    pulp.LpAffineExpression({
                        SOC[t]: 1.0,
                        SOC[t-1]: -1.0,
                        P_charge[t]: -eta_f,
                        P_discharge[t]: 1.0 / eta_f
                    }), 
                    sense=0, rhs=0.0
                )

        # Solve
        model.solve(pulp.PULP_CBC_CMD(msg=False))

        results = []
        for t in T:
            results.append({
                'hour': t,
                'da_price_eur': float(da_prices[t]),
                'afrr_price_eur': float(afrr_prices[t]),
                'solar_mw': float(solar_profile[t]),
                'charge_mw': P_charge[t].varValue or 0.0,
                'discharge_mw': P_discharge[t].varValue or 0.0,
                'afrr_mw': R_afrr[t].varValue or 0.0,
                'soc_mwh': SOC[t].varValue or 0.0
            })

        df_opt = pd.DataFrame(results)
        
        # Calculate optimal revenue dynamically to avoid value extraction bugs
        total_rev = sum(
            (float(da_prices[t]) - 1.2) * (P_discharge[t].varValue or 0.0) +
            (-float(da_prices[t]) - 1.2) * (P_charge[t].varValue or 0.0) +
            (float(afrr_prices[t]) - 1.2) * (R_afrr[t].varValue or 0.0) +
            (float(solar_profile[t]) * float(da_prices[t]))
            for t in T
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Optimization Status", pulp.LpStatus[model.status])
        col2.metric("Total Optimal Revenue", f"€{total_rev:,.2f}")
        col3.metric("Peak aFRR Reserve", f"{max([R_afrr[t].varValue or 0.0 for t in T]):.2f} MW")

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
