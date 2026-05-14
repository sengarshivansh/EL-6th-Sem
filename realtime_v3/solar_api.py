# =============================================================
#  realtime_v3/solar_api.py
#  Gets solar irradiance (W/m²) without any hardware
#  Primary  : Open-Meteo API  (free, no key, 15-min updates)
#  Fallback : Astronomical formula (works fully offline)
# =============================================================

import math
import requests
from datetime import datetime
from config import LATITUDE, LONGITUDE, SOLAR_API_TIMEOUT_S


# ─────────────────────────────────────────────────────────────
#  PRIMARY: Open-Meteo (real-time, free, no API key needed)
# ─────────────────────────────────────────────────────────────
def _fetch_openmeteo(lat: float, lon: float) -> float:
    """
    Calls Open-Meteo forecast API and returns current-hour
    shortwave radiation in W/m².
    Same unit as NASA ALLSKY_SFC_SW_DWN used in training.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=shortwave_radiation"
        f"&forecast_days=1"
        f"&timezone=Asia%2FKolkata"
    )
    resp = requests.get(url, timeout=SOLAR_API_TIMEOUT_S)
    resp.raise_for_status()

    data = resp.json()
    hour = datetime.now().hour
    irradiance = data["hourly"]["shortwave_radiation"][hour]
    return max(0.0, float(irradiance))


# ─────────────────────────────────────────────────────────────
#  FALLBACK: Astronomical clear-sky formula (offline safe)
# ─────────────────────────────────────────────────────────────
def _formula_solar(lat: float) -> float:
    """
    Estimates clear-sky irradiance from sun position.
    Accurate enough for XGBoost lag-feature inputs.
    Returns W/m².
    """
    now        = datetime.now()
    hour       = now.hour + now.minute / 60.0
    doy        = now.timetuple().tm_yday          # day of year 1-365

    # Solar declination angle (degrees)
    declination = 23.45 * math.sin(math.radians(360 / 365 * (doy - 81)))

    # Hour angle (15° per hour, noon = 0°)
    hour_angle  = 15.0 * (hour - 12.0)

    # Solar elevation angle
    lat_r  = math.radians(lat)
    dec_r  = math.radians(declination)
    ha_r   = math.radians(hour_angle)

    sin_elev = (
        math.sin(lat_r) * math.sin(dec_r)
        + math.cos(lat_r) * math.cos(dec_r) * math.cos(ha_r)
    )
    elevation_deg = math.degrees(math.asin(max(0.0, sin_elev)))

    # Clear-sky irradiance (simple sinusoidal model, max ~1000 W/m²)
    irradiance = 1000.0 * math.sin(math.radians(elevation_deg)) if elevation_deg > 0 else 0.0
    return round(max(0.0, irradiance), 2)


# ─────────────────────────────────────────────────────────────
#  PUBLIC API — this is what other modules import
# ─────────────────────────────────────────────────────────────
def get_solar_irradiance(lat: float = LATITUDE, lon: float = LONGITUDE) -> tuple[float, str]:
    """
    Returns (irradiance_W_per_m2, source_label).
    source_label is "api" or "formula" — shown in the dashboard.

    Usage:
        irradiance, source = get_solar_irradiance()
    """
    try:
        value = _fetch_openmeteo(lat, lon)
        return value, "api"
    except Exception:
        value = _formula_solar(lat)
        return value, "formula"


# ─────────────────────────────────────────────────────────────
#  Quick self-test  →  python solar_api.py
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    irr, src = get_solar_irradiance()
    print(f"Solar irradiance : {irr:.2f} W/m²")
    print(f"Source           : {src}")
    print(f"Time             : {datetime.now().strftime('%H:%M:%S')}")