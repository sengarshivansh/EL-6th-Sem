# FILE: simulation_engine_v2.py
import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
from tensorflow.keras.models import load_model

class DigitalTwinV2:
    def __init__(self, solar_path="clean_solar_15min.csv", load_path="BR02_final_data.csv"):
        # 1. Load the CLEAN 15-min Solar Data
        self.solar_data = pd.read_csv(solar_path)
        self.solar_data['timestamp'] = pd.to_datetime(self.solar_data['timestamp'])
        
        # 2. Load the Energy Data (For Load History)
        self.load_data = pd.read_csv(load_path)
        
        # 3. Load BRAIN #1: House Load (LSTM)
        # Note: We reuse the same LSTM model from V1
        self.load_model = load_model("lstm_model.h5", compile=False)
        self.load_scaler = joblib.load("scaler.pkl")
        
        # 4. Load BRAIN #2: Solar Gen (XGBoost) - NEW!
        self.solar_model = joblib.load("solar_xgb_model.pkl")
        
        # 5. Settings
        self.look_back = 96 
        # Start at 10:00 AM (Step 40)
        self.current_step = 96 + 40 
        self.base_voltage = 230.0
        
    def run_step(self):
        # A. Safety Reset
        if self.current_step >= len(self.solar_data):
            self.current_step = self.look_back

        # ================================
        # PART 1: PREDICT LOAD (LSTM)
        # ================================
        # Ensure we don't go out of bounds if files have different lengths
        load_idx = self.current_step % len(self.load_data)
        if load_idx < self.look_back: load_idx = self.look_back
            
        past_load = self.load_data['energy_kwh'].values[load_idx-self.look_back : load_idx]
        
        # Reshape & Predict
        load_input = self.load_scaler.transform(past_load.reshape(-1, 1)).reshape(1, 96, 1)
        pred_load_scaled = self.load_model.predict(load_input, verbose=0)
        pred_load = self.load_scaler.inverse_transform(pred_load_scaled)[0][0]

        # ================================
        # PART 2: PREDICT SOLAR (XGBoost)
        # ================================
        past_solar = self.solar_data['Solar_Gen'].values[self.current_step-self.look_back : self.current_step]
        
        # Reverse array for XGBoost (Newest -> Oldest)
        xgb_input = past_solar[::-1].reshape(1, -1)
        
        # Create DataFrame with correct column names
        cols = [f'lag_{i}' for i in range(1, 97)]
        xgb_input_df = pd.DataFrame(xgb_input, columns=cols)
        
        # Predict
        pred_solar = self.solar_model.predict(xgb_input_df)[0]
        if pred_solar < 0: pred_solar = 0.0

        # ================================
        # PART 3: PHYSICS & CONTROL
        # ================================
        net_load = pred_load - pred_solar
        
        # Voltage Simulation
        simulated_voltage = self.base_voltage - (0.1 * net_load) + np.random.uniform(-0.2, 0.2)
        
        # Tap Changer Logic
        if simulated_voltage < 220:
            action = "TAP UP (+5V)"
            led_color = "RED"
        elif simulated_voltage > 240:
            action = "TAP DOWN (-5V)"
            led_color = "RED"
        else:
            action = "HOLD"
            led_color = "GREEN"
            
        # Get Timestamp
        timestamp = self.solar_data.iloc[self.current_step]['timestamp']
        self.current_step += 1
        
        return {
            "Time": str(timestamp),
            "Load_Pred": round(float(pred_load), 2),
            "Solar_Pred": round(float(pred_solar), 2),
            "Net_Load": round(float(net_load), 2),
            "Grid_Voltage": round(float(simulated_voltage), 2),
            "Action": action,
            "LED": led_color
        }