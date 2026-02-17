# main.py  -- MicroPython (ESP32) AIR NODE
import network
import socket
import time
from machine import Pin, ADC
import dht

# --------------------------------------------------------------------
# CONFIG (EDIT THESE FOR YOUR SETUP)
# --------------------------------------------------------------------
SERVER_IP   = "192.168.1.7"
SERVER_PORT = 5050
WIFI_SSID   = "Kamesh S"
WIFI_PASS   = "Abinaav@09"
CLIENT_ID   = "GS-AIR-JJAM52"

RECONNECT_DELAY = 5      # seconds between WiFi retries
SEND_INTERVAL   = 2      # seconds between uploads

# --- Sensor pins (change if wired differently) ---
MQ135_PIN = 34   # ADC1 (recommended: input-only pin OK)
MQ7_PIN   = 35   # ADC1
MQ2_PIN   = 32   # ADC1
MQ4_PIN   = 33   # ADC1
MQ6_PIN   = 39   # <--- CHANGED: MQ6 now on GPIO 39 (ADC1)
DHT_PIN   = 12   # DHT22 data pin

# --- LEDs & buzzer pins (digital outputs) ---
LED_RED_PIN    = 14
LED_GREEN_PIN  = 27
BUZZER_PIN     = 26

# --------------------------------------------------------------------
# ALERT THRESHOLDS (TUNE FOR YOUR CALIBRATION)
# These are raw ADC values 0..4095 and °C / %RH
# --------------------------------------------------------------------
MQ135_LIMIT = 2000
MQ7_LIMIT   = 1500
MQ2_LIMIT   = 1500
MQ4_LIMIT   = 1500
MQ6_LIMIT   = 1500

TEMP_LIMIT  = 40.0   # °C
HUM_HIGH    = 80.0   # %RH (optional; set high humidity alert)

ALERT_INTERVAL = 15 * 60   # 15 minutes between long alerts
BUZZ_DURATION  = 30        # seconds buzzer ON when alert triggers

# --------------------------------------------------------------------
# HARDWARE INIT
# --------------------------------------------------------------------

# LEDs & buzzer
led_red   = Pin(LED_RED_PIN,   Pin.OUT, value=0)
led_green = Pin(LED_GREEN_PIN, Pin.OUT, value=0)
buzzer    = Pin(BUZZER_PIN,    Pin.OUT, value=0)

# Gas sensors (ADC)
def _make_adc(pin_no):
    adc = ADC(Pin(pin_no))
    adc.atten(ADC.ATTN_11DB)        # 0..3.3V
    adc.width(ADC.WIDTH_12BIT)      # 0..4095
    return adc

mq135 = _make_adc(MQ135_PIN)
mq7   = _make_adc(MQ7_PIN)
mq2   = _make_adc(MQ2_PIN)
mq4   = _make_adc(MQ4_PIN)
mq6   = _make_adc(MQ6_PIN)

# DHT22 (temperature + humidity)
dht_sensor = dht.DHT22(Pin(DHT_PIN, Pin.IN))

# Alert state
_last_alert_ts = 0     # last time we started a long buzzer alert
_buzzer_until  = 0     # timestamp when buzzer should turn off (0 = no active alert)

# For “last known” temp/hum if DHT fails
_last_temp = 0.0
_last_hum  = 0.0


# --------------------------------------------------------------------
# LED / BUZZER HELPERS
# --------------------------------------------------------------------
def green_on():
    led_green.value(1)


def green_off():
    led_green.value(0)


def red_on():
    led_red.value(1)


def red_off():
    led_red.value(0)


def buzzer_on():
    buzzer.value(1)


def buzzer_off():
    buzzer.value(0)


def blink_red_once(duration=0.15):
    """Short blink for normal events (like successful send)."""
    red_on()
    time.sleep(duration)
    red_off()


def blink_red_error(pattern_count=3, on_time=0.12, off_time=0.12):
    """Error pattern: multiple quick red blinks + short buzzer chirp."""
    for _ in range(pattern_count):
        red_on()
        buzzer_on()
        time.sleep(on_time)
        red_off()
        buzzer_off()
        time.sleep(off_time)


# --------------------------------------------------------------------
# WIFI
# --------------------------------------------------------------------
def connect_wifi():
    """Connect to Wi-Fi, blinking green LED while trying."""
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)

    if wlan.isconnected():
        green_on()
        return wlan

    print("Connecting to WiFi...")
    wlan.connect(WIFI_SSID, WIFI_PASS)

    start = time.time()
    timeout = 20  # seconds

    while not wlan.isconnected() and (time.time() - start) < timeout:
        # blink green at ~1 Hz while connecting
        led_green.value(1)
        time.sleep(0.5)
        led_green.value(0)
        time.sleep(0.5)

    if not wlan.isconnected():
        green_off()
        print("WiFi connection failed")
        raise RuntimeError("WiFi connection failed")

    print("WiFi connected:", wlan.ifconfig())
    green_on()
    return wlan


# --------------------------------------------------------------------
# SENSOR READING
# --------------------------------------------------------------------
def read_sensors():
    """
    Read all gas sensors + DHT22.
    Returns:
        mq135_val, mq7_val, mq2_val, mq4_val, mq6_val, temp_c, hum
    """
    global _last_temp, _last_hum

    # ADC gas readings (raw)
    mq135_val = mq135.read()
    mq7_val   = mq7.read()
    mq2_val   = mq2.read()
    mq4_val   = mq4.read()
    mq6_val   = mq6.read()

    # DHT22 temperature & humidity
    temp_c = _last_temp
    hum    = _last_hum

    try:
        dht_sensor.measure()
        temp_c = float(dht_sensor.temperature())
        hum    = float(dht_sensor.humidity())
        _last_temp = temp_c
        _last_hum  = hum
    except Exception as e:
        # Use last known values and log once
        print("DHT22 read error:", e)

    return mq135_val, mq7_val, mq2_val, mq4_val, mq6_val, temp_c, hum


# --------------------------------------------------------------------
# ALERT LOGIC (BUZZER)
# --------------------------------------------------------------------
def check_alerts(mq135_val, mq7_val, mq2_val, mq4_val, mq6_val, temp_c, hum):
    """
    Non-blocking buzzer logic based on thresholds and a cool-down.
    Called once per loop.
    """
    global _last_alert_ts, _buzzer_until

    now = time.time()

    # If buzzer currently active, keep it on until time is up
    if _buzzer_until > 0:
        if now < _buzzer_until:
            buzzer_on()
        else:
            buzzer_off()
            _buzzer_until = 0
        return

    # Decide if conditions are bad enough
    exceed = False

    if mq135_val > MQ135_LIMIT:
        exceed = True
    if mq7_val   > MQ7_LIMIT:
        exceed = True
    if mq2_val   > MQ2_LIMIT:
        exceed = True
    if mq4_val   > MQ4_LIMIT:
        exceed = True
    if mq6_val   > MQ6_LIMIT:
        exceed = True

    if temp_c > TEMP_LIMIT:
        exceed = True
    if hum > HUM_HIGH:
        exceed = True

    if not exceed:
        buzzer_off()
        return

    # Enough time since last alert?
    if (now - _last_alert_ts) >= ALERT_INTERVAL:
        print("ALERT: thresholds exceeded -> buzzer ON for", BUZZ_DURATION, "seconds")
        _last_alert_ts = now
        _buzzer_until  = now + BUZZ_DURATION
        buzzer_on()


# --------------------------------------------------------------------
# SOCKET SEND
# --------------------------------------------------------------------
def send_reading(mq135_val, mq7_val, mq2_val, mq4_val, mq6_val, temp_c, hum):
    """
    Send one reading to the server.
    Returns True on success, False on failure.
    """
    s = None
    try:
        msg = (
            "HELLO {cid} "
            "MQ135={mq135} MQ7={mq7} TEMP={temp:.1f} HUM={hum:.1f} "
            "MQ2={mq2} MQ4={mq4} MQ6={mq6}\n"
        ).format(
            cid=CLIENT_ID,
            mq135= mq135_val,
            mq7=   mq7_val,
            temp=  temp_c,
            hum=   hum,
            mq2=   mq2_val,
            mq4=   mq4_val,
            mq6=   mq6_val,
        )

        addr = (SERVER_IP, SERVER_PORT)
        s = socket.socket()
        s.settimeout(5)
        print("Connecting to server", addr)
        s.connect(addr)

        print("Sending:", msg.strip())
        s.send(msg.encode("utf-8"))

        try:
            data = s.recv(256)
            if data:
                print("Server replied:", data.decode("utf-8").strip())
            else:
                print("No reply from server (empty).")
        except Exception:
            print("No reply from server (timeout).")

        blink_red_once()
        return True

    except Exception as e:
        print("Send error:", e)
        blink_red_error()
        return False

    finally:
        if s is not None:
            try:
                s.close()
            except Exception:
                pass


# --------------------------------------------------------------------
# MAIN LOOP
# --------------------------------------------------------------------
def main_loop():
    while True:
        # 1) Ensure Wi-Fi
        try:
            connect_wifi()
        except Exception as e:
            print("WiFi error:", e)
            green_off()
            blink_red_error()
            time.sleep(RECONNECT_DELAY)
            continue

        # 2) Read sensors
        try:
            (
                mq135_val,
                mq7_val,
                mq2_val,
                mq4_val,
                mq6_val,
                temp_c,
                hum,
            ) = read_sensors()

            print(
                "MQ135={:4d} MQ7={:4d} MQ2={:4d} MQ4={:4d} MQ6={:4d} "
                "TEMP={:.1f} HUM={:.1f}".format(
                    mq135_val, mq7_val, mq2_val, mq4_val, mq6_val, temp_c, hum
                )
            )

        except Exception as e:
            print("Sensor read error:", e)
            blink_red_error()
            continue

        # 3) Send to server
        ok = send_reading(mq135_val, mq7_val, mq2_val, mq4_val, mq6_val, temp_c, hum)

        # 4) Alert / buzzer logic (non-blocking)
        check_alerts(mq135_val, mq7_val, mq2_val, mq4_val, mq6_val, temp_c, hum)

        # 5) Wait until next cycle
        time.sleep(SEND_INTERVAL)


# --------------------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------------------
if __name__ == "__main__":
    main_loop()
