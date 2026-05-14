# =============================================================
#  realtime_v3/esp32_reader.py
#  Reads live PZEM-004T data sent by the ESP32 over serial.
#
#  ESP32 sends one JSON line every 15 seconds:
#    {"voltage":231.4,"current":1.23,"power":0.284,"energy":0.001,"frequency":50.02}
#
#  This module exposes a single function: get_load_reading()
#  Returns a dict with those fields, or dummy data in DEMO_MODE.
# =============================================================

import json
import serial
import serial.tools.list_ports
from datetime import datetime
from config import SERIAL_PORT, BAUD_RATE, DEMO_MODE, DEMO_LOAD_KW


# ─────────────────────────────────────────────────────────────
#  Serial connection (lazy — opens only when first called)
# ─────────────────────────────────────────────────────────────
_ser = None

def _get_serial() -> serial.Serial:
    global _ser
    if _ser is None or not _ser.is_open:
        _ser = serial.Serial(
            port     = SERIAL_PORT,
            baudrate = BAUD_RATE,
            timeout  = 3          # seconds to wait for a line
        )
        print(f"[ESP32Reader] Connected on {SERIAL_PORT} @ {BAUD_RATE} baud")
    return _ser


def _read_line() -> dict:
    """Read one JSON line from the serial port."""
    ser  = _get_serial()
    raw  = ser.readline().decode("utf-8", errors="ignore").strip()
    if not raw:
        raise ValueError("Empty line received from ESP32")
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────
#  Demo / fallback data
# ─────────────────────────────────────────────────────────────
import math

def _demo_reading() -> dict:
    """
    Generates realistic dummy load data when DEMO_MODE=True
    or when ESP32 is not connected.
    Follows a typical residential daily load curve.
    """
    hour = datetime.now().hour + datetime.now().minute / 60
    # Residential pattern: morning peak, midday dip, evening peak
    base   = 0.5
    morn   = 1.5 * math.exp(-((hour - 7.5) ** 2) / 2)
    eve    = 2.0 * math.exp(-((hour - 19.0) ** 2) / 3)
    power  = round(base + morn + eve, 3)

    return {
        "voltage"   : round(230.0 + (hash(str(datetime.now().minute)) % 5 - 2), 2),
        "current"   : round(power / 0.23, 3),
        "power"     : power,
        "energy"    : round(power * 0.25 / 1000, 6),  # kWh per 15-min step
        "frequency" : 50.02,
        "source"    : "demo"
    }


# ─────────────────────────────────────────────────────────────
#  PUBLIC API — this is what other modules import
# ─────────────────────────────────────────────────────────────
def get_load_reading() -> dict:
    """
    Returns latest PZEM-004T reading as a dict:
    {
        "voltage"   : float  (V)
        "current"   : float  (A)
        "power"     : float  (kW)
        "energy"    : float  (kWh)
        "frequency" : float  (Hz)
        "source"    : str    ("esp32" | "demo" | "fallback")
    }
    Falls back to demo data if ESP32 is unreachable.
    """
    if DEMO_MODE:
        return _demo_reading()

    try:
        data = _read_line()
        data["source"] = "esp32"
        # PZEM-004T reports power in Watts → convert to kW
        if data.get("power", 0) > 100:
            data["power"] = data["power"] / 1000.0
        return data

    except serial.SerialException as e:
        print(f"[ESP32Reader] Serial error: {e} — using demo data")
        d = _demo_reading()
        d["source"] = "fallback"
        return d

    except (json.JSONDecodeError, ValueError) as e:
        print(f"[ESP32Reader] Parse error: {e} — using demo data")
        d = _demo_reading()
        d["source"] = "fallback"
        return d


def list_available_ports() -> list[str]:
    """Helper to find your ESP32's COM port."""
    return [p.device for p in serial.tools.list_ports.comports()]


# ─────────────────────────────────────────────────────────────
#  Quick self-test  →  python esp32_reader.py
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Available ports:", list_available_ports())
    print("\nReading from ESP32 (or demo)...")
    reading = get_load_reading()
    for k, v in reading.items():
        print(f"  {k:12s}: {v}")