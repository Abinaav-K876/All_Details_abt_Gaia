# main.py  -- MicroPython (ESP32)
import network
import socket
import time
from machine import Pin, ADC
import dht

# ------ CONFIG (fill these) ------
SERVER_IP = "192.168.1.7"
SERVER_PORT = "5050"
WIFI_SSID = "Kamesh S"
WIFI_PASS = "Abinaav@09"
CLIENT_ID = "GS-AIR-ZAKHDB"

RECONNECT_DELAY = 5      # seconds between WiFi retries
SEND_INTERVAL   = 1      # seconds between sends

# ------ PIN MAPPING (change if needed) ------
# Use ADC-capable pins for MQ135/MQ7 (e.g. 32–39 on most ESP32 dev boards)
MQ135_PIN = 32   # Left side ADC pin
MQ7_PIN   = 33   # Left side ADC pin
DHT_PIN   = 34

# ------ SENSOR SETUP ------
mq135 = ADC(Pin(MQ135_PIN))
mq7   = ADC(Pin(MQ7_PIN))

# 12-bit resolution (0–4095) and highest range (0–3.3V approx)
mq135.atten(ADC.ATTN_11DB)
mq7.atten(ADC.ATTN_11DB)
mq135.width(ADC.WIDTH_12BIT)
mq7.width(ADC.WIDTH_12BIT)

dht_sensor = dht.DHT11(Pin(DHT_PIN))


# -------------------- WIFI --------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        # wait up to ~15 seconds
        for _ in range(30):
            if wlan.isconnected():
                break
            time.sleep(0.5)
        if not wlan.isconnected():
            raise RuntimeError("WiFi connection failed")
    print("WiFi connected, IP:", wlan.ifconfig()[0])
    return wlan


# -------------------- ONE SEND --------------------
def send_hello_once():
    s = None
    try:
        # ----- read sensors -----
        # MQ135 / MQ7 raw values (0–4095)
        mq135_val = mq135.read()
        mq7_val   = mq7.read()

        # DHT11
        try:
            dht_sensor.measure()
            temp_c = dht_sensor.temperature()
            hum    = dht_sensor.humidity()
        except OSError as e:
            print("DHT11 read error:", e)
            temp_c = None
            hum    = None

        # ----- open socket -----
        addr = (SERVER_IP, SERVER_PORT)
        s = socket.socket()
        s.settimeout(5)
        print("Connecting to server", addr)
        s.connect(addr)

        # ----- build message -----
        # You can change this format to whatever your server expects
        msg = (
            f"HELLO {CLIENT_ID} "
            f"MQ135={mq135_val} "
            f"MQ7={mq7_val} "
            f"TEMP={temp_c} "
            f"HUM={hum}\n"
        )

        print("Sending:", msg.strip())
        s.send(msg.encode("utf-8"))

        # wait for ack (one line)
        try:
            data = s.recv(512)
            if data:
                print("Server replied:", data.decode("utf-8").strip())
            else:
                print("No reply from server.")
        except OSError:
            print("No response (recv timeout).")

    except Exception as e:
        print("Socket/send error:", e)
    finally:
        if s is not None:
            try:
                s.close()
            except Exception:
                pass


# -------------------- MAIN LOOP --------------------
def main_loop():
    while True:
        try:
            connect_wifi()
        except Exception as e:
            print("WiFi error:", e)
            time.sleep(RECONNECT_DELAY)
            continue

        try:
            send_hello_once()
        except Exception as e:
            print("Send error:", e)

        time.sleep(SEND_INTERVAL)


if __name__ == "__main__":
    main_loop()
