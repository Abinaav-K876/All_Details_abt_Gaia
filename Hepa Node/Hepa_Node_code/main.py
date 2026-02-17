import network
import usocket as socket
import time
import machine
import gc
from machine import Pin, I2C
import sys
import time

# ---------------- CONFIG ----------------
SERVER_IP = "35.207.232.203"
SERVER_PORT = 5050
CLIENT_ID = "GS-AIR-JJAM52"

GAS_LIMIT = 1800
mq135_baseline = 500.0
mq7_baseline = 500.0
mq2_baseline = 500.0
mq4_baseline = 500.0
mq6_baseline = 500.0
CALIBRATION_TIME = 15
BEEP_DURATION_MS = 30000
REPEAT_INTERVAL_MS = 900000
LOOP_INTERVAL = 3  # 3 second data frequency

# ---------------- HARDWARE ----------------
led_red = machine.Pin(14, machine.Pin.OUT)
led_green = machine.Pin(27, machine.Pin.OUT)
buzzer = machine.Pin(26, machine.Pin.OUT)


def init_adc(pin_no):
    adc = machine.ADC(machine.Pin(pin_no))
    adc.atten(machine.ADC.ATTN_11DB)
    return adc


mq135 = init_adc(34)
mq7 = init_adc(35)
mq2 = init_adc(32)
mq4 = init_adc(33)
mq6 = init_adc(39)

# ---------------- STATE ----------------
last_beep_start = 0
last_interval_start = 0
is_beeping = False


def green_blink(times=1):
    for _ in range(times):
        led_green.value(1)
        time.sleep(0.3)
        led_green.value(0)
        time.sleep(0.1)


def calibrate_all_sensors():
    global mq135_baseline, mq7_baseline, mq2_baseline, mq4_baseline, mq6_baseline
    sensors = [
        (mq135, "MQ135"),
        (mq7, "MQ7"),
        (mq2, "MQ2"),
        (mq4, "MQ4"),
        (mq6, "MQ6")
    ]
    baselines = []

    print("Calibrating All Gas Sensors...")

    for sensor, name in sensors:
        print(f"{name} Calibrating...")
        total = 0
        for i in range(CALIBRATION_TIME):
            # Toggle LEDs during calibration
            led_green.value(i % 2)
            led_red.value(1 - (i % 2))

            val = sensor.read()
            if i > 5:
                total += val
            time.sleep(1)

        baseline = total / (CALIBRATION_TIME - 5)
        baselines.append(baseline)
        print(f"{name} Baseline Set: {baseline}")

    mq135_baseline = baselines[0]
    mq7_baseline = baselines[1]
    mq2_baseline = baselines[2]
    mq4_baseline = baselines[3]
    mq6_baseline = baselines[4]

    led_red.value(0)
    led_green.value(0)
    green_blink(3)


# ---------------- SENSOR LOGIC ----------------
def read_gas_sensors():
    gas_data = []
    sensors = [mq135, mq7, mq2, mq4, mq6]
    for s in sensors:
        samples = []
        for _ in range(20):
            samples.append(s.read())
            time.sleep_ms(2)
        avg = sum(samples) // 20
        gas_data.append(avg)
    return gas_data


def calculate_temp_hum(mq135_val, mq7_val, mq2_val, mq4_val, mq6_val):
    # Simulate temperature based on average gas readings (higher pollution = higher temp)
    avg_gas = (mq135_val + mq7_val + mq2_val + mq4_val + mq6_val) / 5
    temp = 22.0 + (avg_gas / 200.0)  # Base 22°C + increase based on gas levels
    temp = min(max(temp, 18.0), 45.0)  # Clamp between 18-45°C

    # Simulate humidity inversely related to gas (higher pollution = lower humidity)
    hum = 65.0 - (avg_gas / 100.0)
    hum = min(max(hum, 30.0), 85.0)  # Clamp between 30-85%

    return round(temp, 1), round(hum, 1)


def update_json(MQ135, MQ7, MQ2, MQ4, MQ6, TEMP, HUM):
    try:
        with open("gaia_data.json.tmp", "w") as f:
            f.write(
                f'{{"MQ135": {MQ135}, "MQ7": {MQ7}, "MQ2": {MQ2}, "MQ4": {MQ4}, "MQ6": {MQ6}, "TEMP": {TEMP}, "HUM": {HUM}}}')
        import os
        os.rename("gaia_data.json.tmp", "gaia_data.json")
    except Exception as e:
        print("JSON update failed:", e)


# ---------------- MAIN ----------------
def main():
    global last_beep_start, last_interval_start, is_beeping
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    calibrate_all_sensors()

    print("--- GAIA SENTINEL: AIR NODE ACTIVE ---")

    while True:
        current_time = time.ticks_ms()

        # 1. WIFI CHECK
        if not wlan.active() and wlan.isconnected():
            led_red.on()
            buzzer.on()
            led_green.off()
            time.sleep(2)
            continue
        else:
            if not is_beeping:
                led_red.off()
                buzzer.off()

        # 2. DATA ACQUISITION
        gas_vals = read_gas_sensors()

        print("\n[AIR DATA] MQ135:{} MQ7:{} MQ2:{} MQ4:{} MQ6:{}".format(*gas_vals))

        # 3. ALERT LOGIC - Only MQ135 triggers buzzer
        # MQ135 uses original formula (×40), others use different scaling
        mq135_aft_data = int((gas_vals[0] / mq135_baseline) * 40)  # Original formula
        mq7_aft_data = int((gas_vals[1] / mq7_baseline) * 150)  # CO scale (lower PPM)
        mq2_aft_data = int((gas_vals[2] / mq2_baseline) * 800)  # Combustible gases (higher)
        mq4_aft_data = int((gas_vals[3] / mq4_baseline) * 600)  # Methane scale
        mq6_aft_data = int((gas_vals[4] / mq6_baseline) * 250)  # LPG scale

        # Calculate simulated temp and humidity based on gas readings
        temp, hum = calculate_temp_hum(mq135_aft_data, mq7_aft_data, mq2_aft_data, mq4_aft_data, mq6_aft_data)

        print("Climate: {:.1f} C | {:.1f} % (Simulated)".format(temp, hum))

        danger = mq135_aft_data > GAS_LIMIT

        if danger:
            if not is_beeping and (last_interval_start == 0 or time.ticks_diff(current_time,
                                                                               last_interval_start) >= REPEAT_INTERVAL_MS):
                is_beeping = True
                last_beep_start = current_time
                last_interval_start = current_time
                buzzer.on()
                led_red.on()
                led_green.on()
                print("!! GAS ALERT !!")

            if is_beeping and time.ticks_diff(current_time, last_beep_start) >= BEEP_DURATION_MS:
                is_beeping = False
                buzzer.off()
                led_red.off()
                led_green.off()
        else:
            is_beeping = False
            buzzer.off()
            led_red.off()
            led_green.off()
            last_interval_start = 0

        # 4. DATA TRANSMISSION
        try:
            s = socket.socket()
            s.settimeout(3)
            s.connect((SERVER_IP, SERVER_PORT))

            led_green.on()

            update_json(mq135_aft_data, mq7_aft_data, mq2_aft_data, mq4_aft_data, mq6_aft_data, temp, hum)

            msg = "DATA {} MQ135={} MQ7={} MQ2={} MQ4={} MQ6={} TEMP={:.1f} HUM={:.1f}\n".format(CLIENT_ID,
                                                                                                 mq135_aft_data,
                                                                                                 mq7_aft_data,
                                                                                                 mq2_aft_data,
                                                                                                 mq4_aft_data,
                                                                                                 mq6_aft_data, temp,
                                                                                                 hum)
            s.send(msg.encode())

            time.sleep_ms(200)

            if not is_beeping: led_green.off()
            s.close()

        except:
            print("Socket Error: Check Server")
            if not is_beeping:
                for _ in range(3):
                    led_red.on()
                    time.sleep_ms(100)
                    led_red.off()
                    time.sleep_ms(100)

        time.sleep(LOOP_INTERVAL)
        gc.collect()


if __name__ == "__main__":
    main()
