import streamlit as st
import time
import pandas as pd
from simulation_engine_v2 import DigitalTwinV2

# Setup Page
st.set_page_config(page_title="Smart Grid AI (Dual-Brain)", layout="wide")
st.title("⚡ AI-Driven Microgrid Controller (V2: Hybrid AI)")

# Initialize Logic
if 'sim' not in st.session_state:
    st.session_state.sim = DigitalTwinV2()
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Voltage', 'Net_Load'])

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Testing Console")
# Add a button to force a Voltage Sag
force_sag = st.sidebar.checkbox("🔴 Simulate Heavy Load (Force SAG)")

# --- LAYOUT ---
dashboard_placeholder = st.empty()
status_box = st.empty()

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.subheader("Grid Voltage History")
    voltage_chart = st.empty()
with chart_col2:
    st.subheader("Net Load (kW)")
    load_chart = st.empty()

# Run Button
start_btn = st.button("Start Simulation")

if start_btn:
    for i in range(100):
        # 1. Get Data from Engine
        data = st.session_state.sim.run_step()
        
        # 2. OVERRIDE FOR DEMO (If checkbox is clicked)
        # 2. OVERRIDE FOR DEMO (If checkbox is clicked)
        if force_sag:
            # SCENARIO: Massive Load + No Solar (e.g., Night time surge)
            data['Load_Pred'] = 50.00 
            
            # CRITICAL FIX: Temporarily force Solar to 0 to ensure Net Load is POSITIVE
            data['Solar_Pred'] = 0.00  
            
            # Now Net Load = 50 - 0 = +50 kW (Consumption)
            data['Net_Load'] = 50.00 
            
            # Recalculate Voltage (Impedance * Positive Load = Voltage DROP)
            # V = 230 - (2.0 * 50) = 130V
            data['Grid_Voltage'] = 230.0 - (2.0 * data['Net_Load'])
            
            # Recalculate Logic
            if data['Grid_Voltage'] < 220:
                data['Action'] = "TAP UP (+5V)"
                data['LED'] = "RED"
            elif data['Grid_Voltage'] > 240:
                data['Action'] = "TAP DOWN (-5V)"
                data['LED'] = "RED"
            else:
                data['Action'] = "HOLD"
                data['LED'] = "GREEN"
        # 3. Update Dashboard
        with dashboard_placeholder.container():
            kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
            kpi1.metric("Time", data['Time'].split(' ')[1])
            kpi2.metric("Load (LSTM)", f"{data['Load_Pred']} kW")
            kpi3.metric("Solar (XGB)", f"{data['Solar_Pred']} kW")
            kpi4.metric("Grid Voltage", f"{round(data['Grid_Voltage'], 2)} V")
            kpi5.metric("Tap Action", data['Action'])

        # 4. Status Alert
        if data['LED'] == "RED":
            if "TAP UP" in data['Action']:
                status_box.error(f"⚠️ LOW VOLTAGE DETECTED! {data['Action']}")
            else:
                status_box.error(f"⚠️ HIGH VOLTAGE DETECTED! {data['Action']}")
        else:
            status_box.success(f"✅ SYSTEM STABLE")
            
        # 5. Graphs
        new_row = pd.DataFrame({
            'Time': [data['Time']], 
            'Voltage': [data['Grid_Voltage']], 
            'Net_Load': [data['Net_Load']]
        })
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
        
        chart_data = st.session_state.history.tail(50).set_index("Time")
        voltage_chart.line_chart(chart_data['Voltage'])
        load_chart.area_chart(chart_data['Net_Load'])
        
        time.sleep(0.3)