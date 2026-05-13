import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model

class DigitalTwin:
    def __init__(self, csv_path="BR02_final_data.csv", model_path="lstm_model.h5"):
        # 1. Load Data
        self.data = pd.read_csv(csv_path)
        
        # Get the first column name for Timestamp
        time_col = self.data.columns[0] 
        self.data['timestamp'] = pd.to_datetime(self.data[time_col])
        
        # 2. Load AI Brain (WITH THE FIX)
        # We use compile=False to avoid the "metrics.mse" error
        self.model = load_model(model_path, compile=False)
        self.scaler = joblib.load("scaler.pkl")
        
        # 3. Settings
        self.look_back = 96 
        self.current_step = 96 + 40
        self.base_voltage = 230.0
        
    def run_step(self):
        """Simulate ONE 15-minute interval"""
        
        # A. Safety Reset (Loop back if end of data)
        if self.current_step >= len(self.data):
            self.current_step = self.look_back

        # B. Get Past Data for AI Input
        # We need the last 96 'energy_kwh' values
        past_window = self.data['energy_kwh'].values[self.current_step-self.look_back : self.current_step]
        
        # C. Predict Future Load (The AI Part)
        # Reshape to (1, 96, 1) and Scale
        input_scaled = self.scaler.transform(past_window.reshape(-1, 1))
        input_reshaped = input_scaled.reshape(1, 96, 1)
        
        prediction_scaled = self.model.predict(input_reshaped, verbose=0)
        pred_load = self.scaler.inverse_transform(prediction_scaled)[0][0]
        
        # D. Get Real Solar Data (From NASA column)
        real_solar = self.data.iloc[self.current_step]['Solar_Gen']
        
        # E. Calculate Net Load & Simulated Voltage
        net_load = pred_load - real_solar
        
        # Physics: Voltage Drops when Load is high, Rises when Solar is high
        # Formula: V = 230 - (Impedance * Net_Load)
        # We use '0.8' as a fake impedance value for the demo
        simulated_voltage = self.base_voltage - (0.1 * net_load)
        
        # Add random noise (fluctuation)
        noise = np.random.uniform(-0.5, 0.5)
        simulated_voltage += noise
        
        # F. Tap Changer Logic (The "Controller")
        if simulated_voltage < 220:
            status = "LOW VOLTAGE"
            action = "TAP UP (+5V)"
            led_color = "RED"
        elif simulated_voltage > 240:
            status = "HIGH VOLTAGE"
            action = "TAP DOWN (-5V)"
            led_color = "RED"
        else:
            status = "STABLE"
            action = "HOLD"
            led_color = "GREEN"
            
        # Move simulation forward
        timestamp = self.data.iloc[self.current_step]['timestamp'] # Or 'Datetime' column
        self.current_step += 1
        
        return {
            "Time": str(timestamp),
            "Load_Pred": round(float(pred_load), 2),
            "Solar_Real": round(float(real_solar), 2),
            "Net_Load": round(float(net_load), 2),
            "Grid_Voltage": round(float(simulated_voltage), 2),
            "Action": action,
            "LED": led_color
        }


        # ... (Your existing class code is above this) ...

# ==========================================
# TEST DRIVER (Add this to the bottom)
# ==========================================
if __name__ == "__main__":
    print("⚡ Starting Digital Twin Engine...")
    
    try:
        # 1. Initialize the Engine
        bot = DigitalTwin()
        print("✅ Model & Data Loaded Successfully!")
        
        # 2. Run a few test steps
        print("\n--- RUNNING SIMULATION TEST ---")
        for i in range(3):
            result = bot.run_step()
            print(f"Step {i+1}: {result}")
            
        print("\n✅ Test Complete. You are ready to run app.py!")
        
    except Exception as e:
        print(f"\n❌ ERROR during test: {e}")
        print("Tip: Check if 'simulation_ready_data.csv' is in the folder.")