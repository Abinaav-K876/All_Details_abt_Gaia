import network
import usocket as socket
import time
import machine
import ubinascii
import gc

# ---------------- CONFIG ----------------
SERVER_IP   = "10.17.13.168"
SERVER_PORT = 10000
WIFI_SSID   = "Kamesh S"
WIFI_PASS   = "Abinaav@09"
CLIENT_ID   = "GS-WATER-W0YGX2"

RECONNECT_DELAY = 5
SEND_INTERVAL   = 3
WIFI_CONNECT_TIMEOUT = 25

# ---------------- ALERT SETTINGS ----------------
TDS_LIMIT = 800
TEMP_LIMIT = 40
BUZZ_DURATION = 5

# ---------------- HARDWARE ----------------
adc = machine.ADC(0)     # TDS on A0
led = machine.Pin(2, machine.Pin.OUT)   # onboard LED
buzzer = machine.Pin(14, machine.Pin.OUT)  # CHANGE PIN IF NEEDED

# ---------------- HELPERS ----------------
def blink_led(times=2):
    for _ in range(times):
        led.off()
        time.sleep(0.2)
        led.on()
        time.sleep(0.2)

def get_device_id():
    return CLIENT_ID or "ESP-" + ubinascii.hexlify(machine.unique_id()).decode()

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return wlan

    print("Connecting to WiFi...")
    wlan.connect(WIFI_SSID, WIFI_PASS)

    start = time.time()
    while not wlan.isconnected():
        led.value((time.time() * 2) % 1 > 0.5)  # blink while connecting
        if time.time() - start > WIFI_CONNECT_TIMEOUT:
            raise RuntimeError("WiFi timeout")
        time.sleep(0.5)

    led.off()
    print("Connected:", wlan.ifconfig())
    return wlan

def read_tds_filtered(samples=10):
    total = 0
    for _ in range(samples):
        val = adc.read()
        total += val
        time.sleep_ms(20)
    avg = total / samples
    return int((avg / 1023) * 1200)  # calibration curve approx.

def read_temp():
    return 0  # placeholder until DS18B20 is connected

def send_packet(tds, temp):
    msg = "DATA {} TDS={} TEMP={}\n".format(get_device_id(), tds, temp)
    print("Sending:", msg.strip())

    s = socket.socket()
    s.settimeout(5)

    try:
        s.connect((SERVER_IP, SERVER_PORT))
        s.send(msg.encode())
        reply = s.recv(200)
        print("Server:", reply.decode(errors="ignore"))
        blink_led(1)
        return True
    except Exception as e:
        print("SEND ERROR:", e)
        return False
    finally:
        s.close()
        gc.collect()

def buzzer_alert():
    print("⚠ ALERT: Poor water quality, buzzer ON")
    buzzer.on()
    time.sleep(BUZZ_DURATION)
    buzzer.off()

# ---------------- MAIN LOOP ----------------
def main():
    fail_count = 0

    while True:
        try:
            connect_wifi()
        except Exception as e:
            print("WiFi Error:", e)
            led.on()
            time.sleep(RECONNECT_DELAY)
            continue

        tds = read_tds_filtered()
        temp = read_temp()

        print("TDS:", tds, "ppm | Temp:", temp, "°C")

        ok = send_packet(tds, temp)

        if ok:
            fail_count = 0
        else:
            fail_count += 1
            if fail_count > 3:
                print("Restarting WiFi...")
                network.WLAN(network.STA_IF).disconnect()
                fail_count = 0

        if tds > TDS_LIMIT or temp > TEMP_LIMIT:
            buzzer_alert()

        time.sleep(SEND_INTERVAL)

# ---------------- RUN ----------------
try:
    main()
except KeyboardInterrupt:
    print("Stopped by user")
