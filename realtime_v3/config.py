# =============================================================
#  realtime_v3/config.py
#  Edit this file ONLY — everything else reads from here
# =============================================================

# ── Transformer / grid location ──────────────────────────────
LATITUDE  = 28.6   # Bareilly, UP
LONGITUDE = 79.7

# ── Serial port (ESP32 → PC) ─────────────────────────────────
# Windows : "COM3", "COM5", "COM8" etc.
# Linux   : "/dev/ttyUSB0"  or  "/dev/ttyACM0"
# Find it : Device Manager → Ports (COM & LPT)
SERIAL_PORT = "COM5"
BAUD_RATE   = 115200

# ── Model file paths (one level up — shared with original) ───
import os
_HERE        = os.path.dirname(os.path.abspath(__file__))
_ROOT        = os.path.dirname(_HERE)           # EL-6th-Sem/

LSTM_MODEL_PATH  = os.path.join(_ROOT, "lstm_model.h5")
SCALER_PATH      = os.path.join(_ROOT, "scaler.pkl")
XGB_MODEL_PATH   = os.path.join(_ROOT, "solar_xgb_model.pkl")
SOLAR_CSV_PATH   = os.path.join(_ROOT, "clean_solar_15min.csv")  # for buffer pre-fill

# ── Grid voltage limits ──────────────────────────────────────
VOLTAGE_NOMINAL = 230.0   # V
VOLTAGE_LOW     = 220.0   # V  → TAP UP
VOLTAGE_HIGH    = 240.0   # V  → TAP DOWN

# ── Simulation physics (same as original engine) ─────────────
IMPEDANCE = 0.1           # V drop per kW of net load

# ── Solar buffer ─────────────────────────────────────────────
LOOK_BACK = 96            # 96 × 15 min = 24 hours

# ── Streamlit dashboard ──────────────────────────────────────
DASHBOARD_PORT      = 8502          # won't clash with app_v2.py (8501)
REFRESH_INTERVAL_S  = 15            # seconds between live updates
CHART_HISTORY       = 50            # how many steps shown on charts

# ── Solar API ────────────────────────────────────────────────
SOLAR_API_TIMEOUT_S = 8             # seconds before fallback kicks in

# ── Demo / testing ───────────────────────────────────────────
# Set to True to run without ESP32 connected (uses dummy load data)
DEMO_MODE = False
DEMO_LOAD_KW = 2.5                  # dummy load used in demo mode
