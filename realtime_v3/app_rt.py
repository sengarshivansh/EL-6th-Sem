# =============================================================
#  realtime_v3/app_rt.py
#  Streamlit real-time dashboard
#  Run: python -m streamlit run app_rt.py --server.port 8502
# =============================================================

import time
import pandas as pd
import streamlit as st
from simulation_engine_rt import DigitalTwinRT
from config import REFRESH_INTERVAL_S, CHART_HISTORY, DASHBOARD_PORT

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title = "CORTEX — Real-Time Grid Controller",
    page_icon  = "⚡",
    layout     = "wide"
)

st.title("⚡ CORTEX — Real-Time AI Voltage Controller (V3)")

# ── Source status badges ──────────────────────────────────────
badge_col1, badge_col2, badge_col3 = st.columns(3)
solar_badge  = badge_col1.empty()
load_badge   = badge_col2.empty()
buffer_badge = badge_col3.empty()

# ── Initialize engine ────────────────────────────────────────
if "engine" not in st.session_state:
    st.session_state.engine  = DigitalTwinRT()
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        "Time", "Voltage", "Live_Voltage", "Net_Load",
        "Load_Pred", "Solar_Pred", "Action"
    ])
if "tap_log" not in st.session_state:
    st.session_state.tap_log = []

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.header("Testing Console")
force_sag  = st.sidebar.checkbox("🔴 Simulate Voltage Sag  (Heavy Load)")
force_swell = st.sidebar.checkbox("🔵 Simulate Voltage Swell (Peak Solar)")
st.sidebar.markdown("---")
st.sidebar.markdown("**Model status**")
st.sidebar.success("LSTM loaded")
st.sidebar.success("XGBoost loaded")
st.sidebar.markdown(f"Refresh: every {REFRESH_INTERVAL_S}s")

# ── Main KPI row ──────────────────────────────────────────────
kpi_row          = st.empty()

# ── Alert box ─────────────────────────────────────────────────
alert_box        = st.empty()

# ── Charts ────────────────────────────────────────────────────
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.subheader("Grid Voltage (V)")
    voltage_chart = st.empty()
with chart_col2:
    st.subheader("Net Load (kW)")
    load_chart    = st.empty()

# ── Tap log ───────────────────────────────────────────────────
st.subheader("Tap Action Log")
tap_log_box = st.empty()

# ── Start button ─────────────────────────────────────────────
start = st.button("▶ Start Real-Time Monitoring")

if start:
    while True:
        # ── Get live data ─────────────────────────────────────
        data = st.session_state.engine.run_step()

        # ── Demo overrides ────────────────────────────────────
        if force_sag:
            data["Load_Pred"]    = 50.0
            data["Solar_Pred"]   = 0.0
            data["Net_Load"]     = 50.0
            data["Grid_Voltage"] = 230.0 - (2.0 * 50.0)
            data["Action"]       = "TAP UP (+5V)"
            data["LED"]          = "RED"

        if force_swell:
            data["Load_Pred"]    = 0.5
            data["Solar_Pred"]   = 300.0
            data["Net_Load"]     = -299.5
            data["Grid_Voltage"] = 261.0
            data["Action"]       = "TAP DOWN (-5V)"
            data["LED"]          = "RED"

        # ── Source badges ─────────────────────────────────────
        src_color = "green" if data["Solar_Source"] == "api" else "orange"
        solar_badge.markdown(
            f"Solar source: :{src_color}[{data['Solar_Source'].upper()}]"
        )
        pzem_color = "green" if data["PZEM_Source"] == "esp32" else "orange"
        load_badge.markdown(
            f"Load source: :{pzem_color}[{data['PZEM_Source'].upper()}]"
        )
        buf_pct = data["Load_Buffer_Pct"]
        buf_color = "green" if buf_pct == 100 else "orange"
        buffer_badge.markdown(
            f"Load buffer: :{buf_color}[{buf_pct}%]"
        )

        # ── KPI metrics ───────────────────────────────────────
        with kpi_row.container():
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Time",           data["Time"].split(" ")[1])
            c2.metric("Load (LSTM)",    f"{data['Load_Pred']} kW")
            c3.metric("Solar (XGB)",    f"{data['Solar_Pred']:.1f} W/m²")
            c4.metric("Predicted V",    f"{data['Grid_Voltage']} V")
            c5.metric("Live V (PZEM)",  f"{data['Live_Voltage']} V")
            c6.metric("Tap Action",     data["Action"])

        # ── Alert ─────────────────────────────────────────────
        if data["LED"] == "RED":
            if "UP" in data["Action"]:
                alert_box.error(f"⚠️ LOW VOLTAGE — {data['Action']} issued")
            else:
                alert_box.error(f"⚠️ HIGH VOLTAGE — {data['Action']} issued")
        else:
            alert_box.success("✅ SYSTEM STABLE — HOLD")

        # ── History & charts ─────────────────────────────────
        new_row = pd.DataFrame([{
            "Time"        : data["Time"],
            "Voltage"     : data["Grid_Voltage"],
            "Live_Voltage": data["Live_Voltage"],
            "Net_Load"    : data["Net_Load"],
            "Load_Pred"   : data["Load_Pred"],
            "Solar_Pred"  : data["Solar_Pred"],
            "Action"      : data["Action"],
        }])
        st.session_state.history = pd.concat(
            [st.session_state.history, new_row], ignore_index=True
        )
        hist = st.session_state.history.tail(CHART_HISTORY).set_index("Time")
        voltage_chart.line_chart(hist[["Voltage", "Live_Voltage"]])
        load_chart.area_chart(hist["Net_Load"])

        # ── Tap log ──────────────────────────────────────────
        if data["Action"] != "HOLD":
            st.session_state.tap_log.append(
                f"{data['Time']}  →  {data['Action']}  "
                f"(V={data['Grid_Voltage']})"
            )
        log_text = "\n".join(st.session_state.tap_log[-15:]) or "No tap actions yet."
        tap_log_box.code(log_text)

        time.sleep(REFRESH_INTERVAL_S)