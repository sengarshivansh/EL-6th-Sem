# =============================================================
#  realtime_v3/solar_buffer.py
#  Manages the 96-step rolling window for XGBoost input.
#
#  Problem it solves:
#    XGBoost needs 96 past solar readings before it can predict.
#    Without this, you'd wait 24 hours after startup.
#
#  Solution:
#    On startup, pre-fill the deque from clean_solar_15min.csv
#    using the current time-of-day as the reference point.
#    XGBoost is ready immediately — zero cold-start wait.
# =============================================================

import pandas as pd
import numpy as np
from collections import deque
from datetime import datetime
from config import SOLAR_CSV_PATH, LOOK_BACK


class SolarBuffer:
    """
    Rolling window of the last LOOK_BACK (96) solar irradiance
    readings. Call push() each step, get_xgb_input() to get the
    feature array ready for solar_xgb_model.predict().
    """

    def __init__(self):
        self._buf = deque(maxlen=LOOK_BACK)
        self._prefill()

    # ── Startup pre-fill ──────────────────────────────────────
    def _prefill(self):
        """
        Load clean_solar_15min.csv, find the 96 rows that match
        the current time-of-day, and use them as the initial state.
        This makes the buffer 'look like' the system has been
        running all day, so XGBoost can predict immediately.
        """
        try:
            df = pd.read_csv(SOLAR_CSV_PATH)
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            now   = datetime.now()
            # Build a fake current timestamp using today's date
            # but matching the minute resolution of the CSV
            current_minutes = now.hour * 60 + now.minute
            # Round down to nearest 15-min slot
            slot = (current_minutes // 15) * 15
            slot_hour = slot // 60
            slot_min  = slot % 60

            # Filter rows by time-of-day (hour + minute match)
            df["hour"]   = df["timestamp"].dt.hour
            df["minute"] = df["timestamp"].dt.minute

            # Find the row index closest to current time
            df["slot_min"] = df["hour"] * 60 + df["minute"]
            target_slot    = slot_hour * 60 + slot_min

            # Get the index of the matching slot in the CSV
            match_idx = df[df["slot_min"] == target_slot].index
            if len(match_idx) == 0:
                # fallback: use the first 96 rows
                seed_values = df["Solar_Gen"].values[:LOOK_BACK]
            else:
                idx = match_idx[0]
                start = max(0, idx - LOOK_BACK + 1)
                seed_values = df["Solar_Gen"].values[start : idx + 1]

            for v in seed_values:
                self._buf.append(float(v))

            print(f"[SolarBuffer] Pre-filled with {len(self._buf)} readings "
                  f"(time slot {slot_hour:02d}:{slot_min:02d})")

        except Exception as e:
            print(f"[SolarBuffer] Pre-fill failed ({e}), starting empty.")
            for _ in range(LOOK_BACK):
                self._buf.append(0.0)

    # ── Runtime ───────────────────────────────────────────────
    def push(self, irradiance: float):
        """Add a new live reading to the buffer."""
        self._buf.append(float(irradiance))

    def is_ready(self) -> bool:
        """True once 96 readings are available."""
        return len(self._buf) == LOOK_BACK

    def get_xgb_input(self) -> "pd.DataFrame":
        """
        Returns a DataFrame with columns lag_1 … lag_96,
        exactly as the XGBoost model was trained on.
        Most recent reading = lag_1, oldest = lag_96.
        """
        values = list(self._buf)          # oldest → newest
        reversed_values = values[::-1]    # newest → oldest (lag_1 first)

        cols = [f"lag_{i}" for i in range(1, LOOK_BACK + 1)]
        import pandas as pd
        return pd.DataFrame([reversed_values], columns=cols)

    def last(self) -> float:
        """Most recent irradiance reading."""
        return self._buf[-1] if self._buf else 0.0


# ─────────────────────────────────────────────────────────────
#  Quick self-test  →  python solar_buffer.py
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    buf = SolarBuffer()
    print(f"Buffer ready : {buf.is_ready()}")
    print(f"Last value   : {buf.last():.2f} W/m²")
    df = buf.get_xgb_input()
    print(f"XGB input shape : {df.shape}")
    print(f"lag_1={df['lag_1'].values[0]:.2f}  lag_96={df['lag_96'].values[0]:.2f}")