import streamlit as st
import time
import pandas as pd
from simulation_engine import DigitalTwin

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Microgrid Twin", layout="wide")
st.title("⚡ AI-Driven Smart Grid Controller")
st.markdown("### Digital Twin Simulation (Bareilly Dataset)")

# --- INITIALIZE THE BRAIN ---
if 'sim' not in st.session_state:
    try:
        st.session_state.sim = DigitalTwin()
        st.success("✅ AI Engine Loaded Successfully")
    except Exception as e:
        st.error(f"❌ Engine Failed: {e}")
        st.stop()

# Initialize data storage for graph
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Voltage', 'Net_Load'])

# --- DASHBOARD LAYOUT ---
# Top Row: Real-time Metrics
col1, col2, col3, col4 = st.columns(4)
metric_load = col1.empty()
metric_solar = col2.empty()
metric_voltage = col3.empty()
metric_action = col4.empty()

# Middle Row: Status Alert
status_box = st.empty()

# Bottom Row: Live Graphs
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.subheader("Grid Voltage (V)")
    voltage_chart = st.empty()
with chart_col2:
    st.subheader("Net Load (kW)")
    load_chart = st.empty()

# --- SIMULATION LOOP ---
start_btn = st.button("▶️ Start Simulation")

if start_btn:
    # Run for 50 steps (approx 12 hours of simulation data)
    for i in range(50):
        # 1. Get Simulation Step
        data = st.session_state.sim.run_step()
        
        # 2. Update Metrics
        metric_load.metric("Predicted Load", f"{data['Load_Pred']} kW")
        metric_solar.metric("Solar Gen", f"{data['Solar_Real']} kW")
        metric_voltage.metric("Grid Voltage", f"{data['Grid_Voltage']} V")
        metric_action.metric("Tap Action", data['Action'])
        
        # 3. Visual Status
        if data['LED'] == "RED":
            status_box.error(f"⚠️ CRITICAL: {data['Action']} Triggered at {data['Time']}")
        elif data['LED'] == "GREEN":
            status_box.success(f"✅ SYSTEM STABLE at {data['Time']}")
        else:
            status_box.warning(f"⚖️ BALANCING GRID at {data['Time']}")

        # 4. Update Graphs
        new_row = pd.DataFrame({
            'Time': [data['Time']], 
            'Voltage': [data['Grid_Voltage']], 
            'Net_Load': [data['Net_Load']]
        })
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
        
        # Show last 40 points to keep graph moving
        chart_data = st.session_state.history.tail(40).set_index("Time")
        
        voltage_chart.line_chart(chart_data['Voltage'])
        load_chart.line_chart(chart_data['Net_Load'])
        
        # 5. Speed Control (Adjust for demo speed)
        time.sleep(0.2)