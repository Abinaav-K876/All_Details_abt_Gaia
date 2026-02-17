import network
import socket
import time
import machine
import onewire, ds18x20
import gc

# ---------------- CONFIG ----------------
SERVER_IP = "35.207.232.203"
SERVER_PORT = 5050
CLIENT_ID = "GS-WATER-W0YGX2"

# Thresholds
TDS_LIMIT = 100
TEMP_LIMIT = 40
BEEP_DURATION_MS = 30000
REPEAT_INTERVAL_MS = 900000

# ---------------- HARDWARE INIT ----------------
time.sleep(2)

buzzer = machine.Pin(25, machine.Pin.OUT)
led_red = machine.Pin(26, machine.Pin.OUT)
led_green = machine.Pin(27, machine.Pin.OUT)

buzzer.off()
led_red.off()
led_green.off()

# DS18B20 (5V side safe pin)
ds_pin = machine.Pin(33)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

# ADC (ADC1 → WiFi safe)
adc = machine.ADC(machine.Pin(35))
adc.atten(machine.ADC.ATTN_11DB)

# Watchdog (ESP32 requires timeout)
try:
    wdt = machine.WDT(timeout=30000)
    print("Watchdog Armed")
except:
    wdt = None
    print("WDT Failed")

# ---------------- STATE ----------------
last_beep_start = 0
last_interval_start = 0
is_beeping = False
start_time = time.time()

# ---------------- UTIL ----------------
def wdt_sleep(seconds):
    for _ in range(int(seconds * 10)):
        if wdt:
            wdt.feed()
        time.sleep_ms(100)


def get_sensors():
    # 1. Temperature
    temp = 25.0
    try:
        roms = ds_sensor.scan()
        if roms:
            ds_sensor.convert_temp()
            for _ in range(8):
                if wdt: wdt.feed()
                time.sleep_ms(100)
            t = ds_sensor.read_temp(roms[0])
            if -50 < t < 125 and t != 85.0:
                temp = t
    except:
        pass

    # 2. Voltage (Using Factory Calibration)
    readings = []
    for _ in range(30):
        # read_uv() returns MICROVOLTS (e.g., 1500000 for 1.5V)
        # This uses the chip's internal calibration table.
        readings.append(adc.read_uv())
        time.sleep_ms(2)

    readings.sort()
    # Get median microvolts
    median_uv = sum(readings[10:20]) / 10.0

    # Convert Microvolts to Volts
    voltage = median_uv / 1000000.0

    # 3. Noise Gate (Low Voltage Cutoff)
    # 0.15V is a common noise floor for ESP32
    if voltage < 0.15:
        return 0, round(temp, 2)

    # 4. TDS Calculation
    comp_coeff = 1.0 + 0.02 * (temp - 25.0)
    v_comp = voltage / comp_coeff

    # TDS FACTOR
    # Start with standard 0.5. 
    # Since read_uv() is much more accurate, 0.5 might actually work now.
    # If it reads too high, lower this to 0.45 or 0.4
    tds_factor = 0.05

    tds = (133.42 * v_comp ** 3 - 255.86 * v_comp ** 2 + 857.39 * v_comp) * tds_factor

    return int(tds), round(temp, 2)

def update_json(tds, temp):
    try:
        with open("gaia_data.json.tmp", "w") as f:
            f.write('{"tds": %d, "temperature": %.2f}' % (tds, temp))
        import os
        os.rename("gaia_data.json.tmp", "gaia_data.json")
    except Exception as e:
        print("JSON update failed:", e)


# ---------------- MAIN ----------------
def main():
    global last_beep_start, last_interval_start, is_beeping

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    print("Gaia Sentinel ESP32 Online")

    while True:
        if wdt:
            wdt.feed()

        now = time.ticks_ms()
        uptime = time.time() - start_time

        # WiFi Management
        if not wlan.isconnected() and wlan.active():
            print("WiFi Lost. Reconnecting...")
            led_red.on()
            buzzer.on()

        if not is_beeping:
            buzzer.off()
            led_red.off()

        # Sensor Read
        tds, temp = get_sensors()
        print("TDS:", tds, "TEMP:", temp, "UPTIME:", uptime)

        # Alarm Logic
        if tds > TDS_LIMIT or temp > TEMP_LIMIT:
            diff = time.ticks_diff(now, last_interval_start)

            if not is_beeping and (last_interval_start == 0 or diff >= REPEAT_INTERVAL_MS):
                is_beeping = True
                last_beep_start = now
                last_interval_start = now
                buzzer.on()
                led_red.on()
                led_green.on()

            if is_beeping and time.ticks_diff(now, last_beep_start) >= BEEP_DURATION_MS:
                is_beeping = False
                buzzer.off()
                led_red.off()
                led_green.off()
        else:
            if is_beeping:
                is_beeping = False
                buzzer.off()
                led_red.off()
                led_green.off()

        # Cloud Upload
        if not is_beeping:
            try:
                s = socket.socket()
                s.settimeout(5)
                s.connect((SERVER_IP, SERVER_PORT))

                led_green.on()
                update_json(tds, temp)
                msg = "DATA {} TDS={} TEMP={} UPTIME={}\n".format(CLIENT_ID, tds, temp, uptime)
                s.send(msg.encode())
                time.sleep_ms(150)
                led_green.off()
                s.close()
                
            except Exception as e:
                print("Uplink Error:", e)
                for _ in range(3):
                    led_red.on()
                    time.sleep_ms(100)
                    led_red.off()
                    time.sleep_ms(100)

        gc.collect()
        wdt_sleep(3)

# ---------------- BOOT ----------------
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Fatal Error:", e)
        time.sleep(5)
        machine.reset()
