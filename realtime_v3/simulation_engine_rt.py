# =============================================================
#  realtime_v3/simulation_engine_rt.py
#  DigitalTwinRT — real-time version of DigitalTwinV2
#
#  What changes vs the original simulation_engine_v2.py:
#    - Load data   : PZEM-004T via ESP32  (not CSV)
#    - Solar data  : Open-Meteo API       (not CSV)
#    - Solar buffer: SolarBuffer class    (not sequential index)
#    - Output dict : same structure as v2 (dashboard compatible)
# =============================================================

import numpy as np
import joblib
import pandas as pd
from tensorflow.keras.models import load_model
from collections import deque

from config import (
    LSTM_MODEL_PATH, SCALER_PATH, XGB_MODEL_PATH,
    VOLTAGE_NOMINAL, VOLTAGE_LOW, VOLTAGE_HIGH,
    IMPEDANCE, LOOK_BACK
)
from solar_api    import get_solar_irradiance
from solar_buffer import SolarBuffer
from esp32_reader import get_load_reading


class DigitalTwinRT:
    """
    Real-time digital twin.
    run_step() returns same dict structure as DigitalTwinV2.run_step()
    so app_rt.py stays nearly identical to app_v2.py.
    """

    def __init__(self):
        print("[DigitalTwinRT] Loading models...")

        # Brain 1: LSTM load forecaster
        self.load_model  = load_model(LSTM_MODEL_PATH, compile=False)
        self.load_scaler = joblib.load(SCALER_PATH)

        # Brain 2: XGBoost solar forecaster
        self.solar_model = joblib.load(XGB_MODEL_PATH)

        # Rolling window of past 96 load readings (kWh per 15 min)
        self.load_buffer = deque(maxlen=LOOK_BACK)

        # Solar buffer — pre-filled from CSV so XGB is ready instantly
        self.solar_buf   = SolarBuffer()

        # Track tap history for the dashboard
        self.tap_count   = 0
        self.step_count  = 0

        print("[DigitalTwinRT] Ready.")

    # ── Internal helpers ─────────────────────────────────────
    def _predict_load(self, current_kwh: float) -> float:
        """
        Push latest reading into load buffer, run LSTM.
        Falls back to current reading if buffer not full yet.
        """
        self.load_buffer.append(current_kwh)

        if len(self.load_buffer) < LOOK_BACK:
            # Buffer still filling — use current reading directly
            return current_kwh

        arr = np.array(list(self.load_buffer)).reshape(-1, 1)
        scaled   = self.load_scaler.transform(arr).reshape(1, LOOK_BACK, 1)
        pred_s   = self.load_model.predict(scaled, verbose=0)
        pred_kwh = self.load_scaler.inverse_transform(pred_s)[0][0]
        return max(0.0, float(pred_kwh))

    def _predict_solar(self, irradiance: float) -> float:
        """
        Push latest irradiance into solar buffer, run XGBoost.
        Falls back to raw irradiance if buffer not ready.
        """
        self.solar_buf.push(irradiance)

        if not self.solar_buf.is_ready():
            return irradiance

        xgb_df = self.solar_buf.get_xgb_input()
        pred   = self.solar_model.predict(xgb_df)[0]
        return max(0.0, float(pred))

    def _tap_logic(self, voltage: float) -> tuple[str, str]:
        """Returns (action, led_color)."""
        if voltage < VOLTAGE_LOW:
            return "TAP UP (+5V)", "RED"
        elif voltage > VOLTAGE_HIGH:
            return "TAP DOWN (-5V)", "RED"
        else:
            return "HOLD", "GREEN"

    # ── Public API ───────────────────────────────────────────
    def run_step(self) -> dict:
        """
        One complete control cycle:
          1. Read live load from ESP32
          2. Fetch live solar from Open-Meteo (or formula)
          3. Run LSTM → predicted load
          4. Run XGBoost → predicted solar
          5. Compute net load & simulated voltage
          6. Apply tap logic
          7. Return result dict (same keys as DigitalTwinV2)
        """
        self.step_count += 1

        # ── Step 1: Live sensing ─────────────────────────────
        pzem          = get_load_reading()
        irradiance, solar_source = get_solar_irradiance()

        live_kwh      = pzem["power"]          # kW (converted in reader)
        live_voltage  = pzem["voltage"]        # V  (actual measured)

        # ── Step 2: AI forecasting ───────────────────────────
        pred_load  = self._predict_load(live_kwh)
        pred_solar = self._predict_solar(irradiance)

        # ── Step 3: Physics ──────────────────────────────────
        net_load   = pred_load - pred_solar
        sim_voltage = (
            VOLTAGE_NOMINAL
            - (IMPEDANCE * net_load)
            + np.random.uniform(-0.2, 0.2)
        )

        # ── Step 4: Control ──────────────────────────────────
        action, led = self._tap_logic(sim_voltage)
        if action != "HOLD":
            self.tap_count += 1

        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            # Same keys as DigitalTwinV2 (dashboard compatible)
            "Time"        : timestamp,
            "Load_Pred"   : round(pred_load,   3),
            "Solar_Pred"  : round(pred_solar,  3),
            "Net_Load"    : round(net_load,    3),
            "Grid_Voltage": round(sim_voltage, 2),
            "Action"      : action,
            "LED"         : led,

            # Extra fields only in RT version
            "Live_Voltage"  : round(live_voltage, 2),
            "Live_Load_kW"  : round(live_kwh,     3),
            "Solar_Source"  : solar_source,          # "api" or "formula"
            "PZEM_Source"   : pzem["source"],        # "esp32", "demo", "fallback"
            "Tap_Count"     : self.tap_count,
            "Step"          : self.step_count,
            "Load_Buffer_Pct": round(len(self.load_buffer) / LOOK_BACK * 100),
        }