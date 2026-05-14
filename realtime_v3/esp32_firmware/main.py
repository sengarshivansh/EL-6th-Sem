# =============================================================
#  realtime_v3/esp32_firmware/main.py
#  MicroPython — flash this onto the ESP32
#
#  What this does:
#    1. Connects to WiFi (optional)
#    2. Reads PZEM-004T every 15 seconds
#    3. Sends JSON over serial (or UDP)
#    4. Receives tap command from PC
#    5. Activates correct relay + LED
# =============================================================

import ujson
import utime
from machine import UART, Pin
from config import (
    WIFI_SSID, WIFI_PASSWORD, COMM_MODE,
    PC_IP, PC_PORT,
    PZEM_TX_PIN, PZEM_RX_PIN,
    RELAY_TAP1, RELAY_TAP2, RELAY_TAP3, RELAY_TAP4,
    LED_GREEN, LED_RED, LED_BLUE, LED_YELLOW,
    READ_INTERVAL_MS
)

# ── UART for PZEM-004T ────────────────────────────────────────
pzem_uart = UART(2, baudrate=9600, tx=PZEM_TX_PIN, rx=PZEM_RX_PIN)

# ── Relays ────────────────────────────────────────────────────
relay = {
    1: Pin(RELAY_TAP1, Pin.OUT, value=0),
    2: Pin(RELAY_TAP2, Pin.OUT, value=0),
    3: Pin(RELAY_TAP3, Pin.OUT, value=0),
    4: Pin(RELAY_TAP4, Pin.OUT, value=0),
}

# ── LEDs ──────────────────────────────────────────────────────
led = {
    "green"  : Pin(LED_GREEN,  Pin.OUT, value=0),
    "red"    : Pin(LED_RED,    Pin.OUT, value=0),
    "blue"   : Pin(LED_BLUE,   Pin.OUT, value=0),
    "yellow" : Pin(LED_YELLOW, Pin.OUT, value=0),
}

# ── Current tap state ─────────────────────────────────────────
current_tap = 2    # start on nominal tap


# ─────────────────────────────────────────────────────────────
#  PZEM-004T protocol (Modbus RTU, simplified read)
# ─────────────────────────────────────────────────────────────
PZEM_READ_CMD = bytes([
    0x01,        # slave address
    0x04,        # function: read input registers
    0x00, 0x00,  # start register
    0x00, 0x0A,  # read 10 registers
    0x70, 0x0D   # CRC
])

def _read_pzem_raw() -> dict | None:
    """Send read command and parse PZEM response."""
    pzem_uart.write(PZEM_READ_CMD)
    utime.sleep_ms(200)

    if pzem_uart.any() < 25:
        return None

    raw = pzem_uart.read(25)
    if raw is None or len(raw) < 25:
        return None

    # Parse registers (big-endian, 2 bytes each)
    def reg(offset):
        return (raw[offset] << 8) | raw[offset + 1]

    voltage   = reg(3)  / 10.0          # V
    current   = ((reg(5) << 16) | reg(7)) / 1000.0   # A
    power     = ((reg(9) << 16) | reg(11)) / 10.0    # W
    energy    = ((reg(13) << 16) | reg(15))           # Wh
    frequency = reg(17) / 10.0          # Hz

    return {
        "voltage"   : round(voltage, 2),
        "current"   : round(current, 3),
        "power"     : round(power / 1000.0, 4),   # convert W → kW
        "energy"    : round(energy / 1000.0, 4),  # convert Wh → kWh
        "frequency" : round(frequency, 2),
    }


def get_pzem_data() -> dict:
    """Read PZEM or return zeros on failure."""
    data = _read_pzem_raw()
    if data is None:
        return {"voltage": 0.0, "current": 0.0,
                "power": 0.0, "energy": 0.0, "frequency": 50.0}
    return data


# ─────────────────────────────────────────────────────────────
#  Relay + LED control
# ─────────────────────────────────────────────────────────────
def all_relays_off():
    for r in relay.values():
        r.value(0)

def all_leds_off():
    for l in led.values():
        l.value(0)

def activate_tap(tap_num: int, action: str):
    """
    tap_num : 1-4
    action  : "TAP UP (+5V)" | "TAP DOWN (-5V)" | "HOLD"
    """
    global current_tap
    all_relays_off()
    all_leds_off()

    tap_num = max(1, min(4, tap_num))
    relay[tap_num].value(1)
    current_tap = tap_num

    if action == "HOLD":
        led["green"].value(1)
    elif "UP" in action:
        led["red"].value(1)
        led["yellow"].value(1)
    elif "DOWN" in action:
        led["red"].value(1)
        led["blue"].value(1)


def action_to_tap(action: str) -> int:
    """Convert action string to tap number."""
    global current_tap
    if "UP" in action:
        return min(current_tap + 1, 4)
    elif "DOWN" in action:
        return max(current_tap - 1, 1)
    else:
        return current_tap


# ─────────────────────────────────────────────────────────────
#  Communication
# ─────────────────────────────────────────────────────────────
def send_data(payload: dict):
    """Send JSON over serial."""
    print(ujson.dumps(payload))   # serial output read by PC


def receive_command() -> str | None:
    """
    Check if PC sent a tap command over serial.
    PC sends: "TAP UP (+5V)\n" or "TAP DOWN (-5V)\n" or "HOLD\n"
    """
    import sys
    import select
    if select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline().strip()
        return line if line else None
    return None


# ─────────────────────────────────────────────────────────────
#  Startup
# ─────────────────────────────────────────────────────────────
def startup():
    """Flash all LEDs once to confirm firmware is running."""
    for l in led.values():
        l.value(1)
    utime.sleep_ms(500)
    all_leds_off()
    activate_tap(2, "HOLD")    # start on nominal tap
    print('{"status":"CORTEX firmware ready"}')


# ─────────────────────────────────────────────────────────────
#  Main loop
# ─────────────────────────────────────────────────────────────
def main():
    startup()
    last_read = utime.ticks_ms()

    while True:
        now = utime.ticks_ms()

        # ── Send PZEM data every READ_INTERVAL_MS ─────────────
        if utime.ticks_diff(now, last_read) >= READ_INTERVAL_MS:
            data = get_pzem_data()
            send_data(data)
            last_read = utime.ticks_ms()

        # ── Check for incoming tap command from PC ─────────────
        cmd = receive_command()
        if cmd:
            tap_num = action_to_tap(cmd)
            activate_tap(tap_num, cmd)

        utime.sleep_ms(100)


main()