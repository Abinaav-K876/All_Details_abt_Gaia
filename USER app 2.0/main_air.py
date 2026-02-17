# main.py  -- MicroPython (ESP32)
import network
import socket
import time
from machine import Pin, ADC
import utime
import dht

SERVER_IP = "10.99.109.114"
WIFI_SSID = "Arvindhan"
WIFI_PASS = "gundumani"
CLIENT_ID = "GS-AIR-NMMOPX"
SERVER_PORT = 5050

RECONNECT_DELAY = 5
SEND_INTERVAL   = 2

MQ135_PIN = 34
MQ7_PIN   = 35
DHT_PIN   = 12

mq135 = ADC(Pin(MQ135_PIN))
mq7   = ADC(Pin(MQ7_PIN))

mq135.atten(ADC.ATTN_11DB)
mq7.atten(ADC.ATTN_11DB)
mq135.width(ADC.WIDTH_12BIT)
mq7.width(ADC.WIDTH_12BIT)

dht_sensor = dht.DHT11(Pin(DHT_PIN, Pin.IN))

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)

        for _ in range(30):
            if wlan.isconnected():
                break
            time.sleep(0.5)

        if not wlan.isconnected():
            raise RuntimeError("WiFi connection failed")

    return wlan


# -------------------- ONE SEND --------------------
def send_hello_once():
    s = None
    try:
        mq135_val = mq135.read()
        mq7_val   = mq7.read()

        try:
            dht_sensor.measure()
            temp_c = dht_sensor.temperature()
            hum    = dht_sensor.humidity()
        except OSError as e:
            print("DHT11 read error:", e)
            temp_c = dht_sensor.temperature()
            hum    = dht_sensor.humidity()

        addr = (SERVER_IP, SERVER_PORT)
        s = socket.socket()
        s.settimeout(5)
        print("Connecting to server", addr)
        s.connect(addr)

        msg = f"HELLO {CLIENT_ID} MQ135={mq135_val} MQ7={mq7_val} TEMP={temp_c} HUM={hum}\n"

        print("Sending:", msg.strip())
        s.send(msg.encode("utf-8"))

        try:
            data = s.recv(512)
            if data:
                print("Server replied:", data.decode("utf-8").strip())
            else:
                pass
        except OSError:
            pass

    except Exception as e:
        pass
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
            time.sleep(RECONNECT_DELAY)
            continue

        try:
            send_hello_once()
        except Exception as e:
            pass

        time.sleep(SEND_INTERVAL)


if __name__ == "__main__":
    main_loop()
