import network
import usocket as socket
import time
import machine
import gc
from machine import Pin, I2C
import sys

# ---------------- CONFIG ----------------
SERVER_IP = "35.207.232.203"
SERVER_PORT = 5050
CLIENT_ID = "GS-GENESIS-KVKHGSV"

# Genesis-specific thresholds
GAS_LIMIT_BEFORE = 1800
mq135_before_baseline = 500.0
mq135_after_baseline = 500.0
CALIBRATION_TIME = 15
LOOP_INTERVAL = 3

# ---------------- HARDWARE ----------------
led_red = machine.Pin(14, machine.Pin.OUT)
led_green = machine.Pin(27, machine.Pin.OUT)

# Relay for pump - Always ON
relay_pump = machine.Pin(25, machine.Pin.OUT)
relay_pump.on()
print("Pump activated and running continuously")


# ADC for MQ135 sensors
def init_adc(pin_no):
    adc = machine.ADC(machine.Pin(pin_no))
    adc.atten(machine.ADC.ATTN_11DB)
    return adc


mq135_before = init_adc(34)
mq135_after = init_adc(35)

# I2C Bus (shared by BH1750 and LCD)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)


# ---------------- LCD API CLASS ----------------
class LcdApi:
    """Base LCD API class"""
    LCD_CLR = 0x01
    LCD_HOME = 0x02
    LCD_ENTRY_MODE = 0x04
    LCD_ENTRY_INC = 0x02
    LCD_ENTRY_SHIFT = 0x01
    LCD_ON_CTRL = 0x08
    LCD_ON_DISPLAY = 0x04
    LCD_ON_CURSOR = 0x02
    LCD_ON_BLINK = 0x01
    LCD_MOVE = 0x10
    LCD_MOVE_DISP = 0x08
    LCD_MOVE_RIGHT = 0x04
    LCD_FUNCTION = 0x20
    LCD_FUNCTION_8BIT = 0x10
    LCD_FUNCTION_2LINES = 0x08
    LCD_FUNCTION_10DOTS = 0x04
    LCD_CGRAM = 0x40
    LCD_DDRAM = 0x80
    LCD_ROW_OFFSETS = [0x00, 0x40, 0x14, 0x54]

    def __init__(self, num_lines, num_columns):
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.cursor_x = 0
        self.cursor_y = 0
        self.backlight = True
        self.display_off()
        self.backlight_on()
        self.clear()
        self.hal_write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)
        self.hide_cursor()
        self.display_on()

    def clear(self):
        self.hal_write_command(self.LCD_CLR)
        self.hal_write_command(self.LCD_HOME)
        self.cursor_x = 0
        self.cursor_y = 0

    def show_cursor(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR)

    def hide_cursor(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def blink_cursor_on(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR | self.LCD_ON_BLINK)

    def blink_cursor_off(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR)

    def display_on(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def display_off(self):
        self.hal_write_command(self.LCD_ON_CTRL)

    def backlight_on(self):
        self.backlight = True
        self.hal_backlight_on()

    def backlight_off(self):
        self.backlight = False
        self.hal_backlight_off()

    def move_to(self, cursor_x, cursor_y):
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        addr = cursor_x + self.LCD_ROW_OFFSETS[cursor_y]
        self.hal_write_command(self.LCD_DDRAM | addr)

    def putchar(self, char):
        if char != '\n':
            self.hal_write_data(ord(char))
            self.cursor_x += 1
        if self.cursor_x >= self.num_columns or char == '\n':
            self.cursor_x = 0
            self.cursor_y += 1
            if self.cursor_y >= self.num_lines:
                self.cursor_y = 0
            self.move_to(self.cursor_x, self.cursor_y)

    def putstr(self, string):
        for char in string:
            self.putchar(char)

    def hal_backlight_on(self):
        pass

    def hal_backlight_off(self):
        pass

    def hal_write_command(self, cmd):
        raise NotImplementedError

    def hal_write_data(self, data):
        raise NotImplementedError


# ---------------- I2C LCD CLASS ----------------
class I2cLcd(LcdApi):
    """I2C LCD implementation"""
    MASK_RS = 0x01
    MASK_RW = 0x02
    MASK_E = 0x04
    SHIFT_BACKLIGHT = 3
    SHIFT_DATA = 4

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.i2c.writeto(self.i2c_addr, bytes([0]))
        time.sleep_ms(20)
        time.sleep_ms(50)
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(5)
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(5)
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(1)
        self.hal_write_init_nibble(0x02)
        LcdApi.__init__(self, num_lines, num_columns)
        cmd = self.LCD_FUNCTION | self.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)

    def hal_write_init_nibble(self, nibble):
        byte = ((nibble >> 0) & 0x0f) << self.SHIFT_DATA
        self.i2c.writeto(self.i2c_addr, bytes([byte | self.MASK_E]))
        time.sleep_ms(1)
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        time.sleep_ms(1)

    def hal_backlight_on(self):
        self.i2c.writeto(self.i2c_addr, bytes([1 << self.SHIFT_BACKLIGHT]))

    def hal_backlight_off(self):
        self.i2c.writeto(self.i2c_addr, bytes([0]))

    def hal_write_command(self, cmd):
        byte = ((self.backlight << self.SHIFT_BACKLIGHT) | (((cmd >> 4) & 0x0f) << self.SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | self.MASK_E]))
        time.sleep_ms(1)
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        time.sleep_ms(1)
        byte = ((self.backlight << self.SHIFT_BACKLIGHT) | (((cmd >> 0) & 0x0f) << self.SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | self.MASK_E]))
        time.sleep_ms(1)
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        time.sleep_ms(1)
        if cmd <= 3:
            time.sleep_ms(5)

    def hal_write_data(self, data):
        byte = (self.MASK_RS | (self.backlight << self.SHIFT_BACKLIGHT) | (((data >> 4) & 0x0f) << self.SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | self.MASK_E]))
        time.sleep_ms(1)
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        time.sleep_ms(1)
        byte = (self.MASK_RS | (self.backlight << self.SHIFT_BACKLIGHT) | (((data >> 0) & 0x0f) << self.SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | self.MASK_E]))
        time.sleep_ms(1)
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        time.sleep_ms(1)


# ---------------- BH1750 LUX SENSOR CLASS ----------------
class BH1750:
    """Driver for BH1750 ambient light sensor"""
    POWER_DOWN = 0x00
    POWER_ON = 0x01
    RESET = 0x07
    CONT_HIRES_1 = 0x10

    def __init__(self, bus, addr=0x23):
        self.bus = bus
        self.addr = addr
        self.power_on()
        self.set_mode(self.CONT_HIRES_1)

    def power_on(self):
        self.bus.writeto(self.addr, bytes([self.POWER_ON]))

    def power_down(self):
        self.bus.writeto(self.addr, bytes([self.POWER_DOWN]))

    def reset(self):
        self.power_on()
        self.bus.writeto(self.addr, bytes([self.RESET]))

    def set_mode(self, mode):
        self.mode = mode
        self.bus.writeto(self.addr, bytes([self.mode]))

    def luminance(self, mode=None):
        if mode is None:
            mode = self.mode
        self.set_mode(mode)
        time.sleep_ms(180)
        data = self.bus.readfrom(self.addr, 2)
        lux = (data[0] << 8 | data[1]) / 1.2
        return lux


# Initialize I2C devices
print("Scanning I2C devices...")
devices = i2c.scan()
if devices:
    print("I2C devices found:", [hex(d) for d in devices])
else:
    print("No I2C devices found")

# Initialize LCD
lcd = None
for lcd_addr in [0x27, 0x3F]:
    if lcd_addr in devices:
        try:
            lcd = I2cLcd(i2c, lcd_addr, 2, 16)
            print(f"LCD initialized at {hex(lcd_addr)}")
            lcd.putstr("GENESIS NODE")
            time.sleep(1)
            break
        except Exception as e:
            print(f"LCD init failed at {hex(lcd_addr)}: {e}")

if lcd is None:
    print("LCD not detected - continuing without display")

# Initialize BH1750
lux_sensor = None
if 0x23 in devices or 0x5C in devices:
    try:
        addr = 0x23 if 0x23 in devices else 0x5C
        lux_sensor = BH1750(bus=i2c, addr=addr)
        print(f"BH1750 initialized at {hex(addr)}")
    except Exception as e:
        print("BH1750 Init Failed:", e)
else:
    print("BH1750 not detected")


# ---------------- UTILITY FUNCTIONS ----------------
def green_blink(times=1):
    for _ in range(times):
        led_green.value(1)
        time.sleep(0.3)
        led_green.value(0)
        time.sleep(0.1)


def calibrate_sensors():
    global mq135_before_baseline, mq135_after_baseline

    print("Calibrating Genesis Node Sensors...")
    if lcd:
        lcd.clear()
        lcd.putstr("Calibrating...")

    # Calibrate MQ135 Before
    print("MQ135-BEFORE Calibrating...")
    total_before = 0
    for i in range(CALIBRATION_TIME):
        led_green.value(i % 2)
        led_red.value(1 - (i % 2))
        val = mq135_before.read()
        if i > 5:
            total_before += val
        time.sleep(1)

    mq135_before_baseline = total_before / (CALIBRATION_TIME - 5)
    print(f"MQ135-BEFORE Baseline: {mq135_before_baseline}")

    # Calibrate MQ135 After
    print("MQ135-AFTER Calibrating...")
    total_after = 0
    for i in range(CALIBRATION_TIME):
        led_green.value(i % 2)
        led_red.value(1 - (i % 2))
        val = mq135_after.read()
        if i > 5:
            total_after += val
        time.sleep(1)

    mq135_after_baseline = total_after / (CALIBRATION_TIME - 5)
    print(f"MQ135-AFTER Baseline: {mq135_after_baseline}")

    led_red.value(0)
    led_green.value(0)
    green_blink(3)

    if lcd:
        lcd.clear()
        lcd.putstr("Ready!")
        time.sleep(1)


# ---------------- SENSOR LOGIC ----------------
def read_mq135_sensor(sensor):
    """Read MQ135 with averaging"""
    samples = []
    for _ in range(20):
        samples.append(sensor.read())
        time.sleep_ms(2)
    return sum(samples) // 20


def read_lux():
    """Read BH1750 lux sensor"""
    if lux_sensor is None:
        return -1
    try:
        lux = lux_sensor.luminance(BH1750.CONT_HIRES_1)
        return round(lux, 2)
    except Exception as e:
        print("Lux read error:", e)
        return -1


def update_lcd(before_ppm, after_ppm, lux_val):
    """Update LCD display with sensor data"""
    if lcd is None:
        return

    try:
        lcd.clear()
        # Line 1: Before and After MQ values
        lcd.move_to(0, 0)
        lcd.putstr(f"B:{before_ppm:4d} A:{after_ppm:4d}")

        # Line 2: Lux value
        lcd.move_to(0, 1)
        if lux_val >= 0:
            lcd.putstr(f"Lux: {lux_val:.1f}")
        else:
            lcd.putstr("Lux: N/A")
    except Exception as e:
        print("LCD update error:", e)


def update_json(MQ135_BEFORE, MQ135_AFTER, LUX):
    """Always update JSON for localhost website"""
    try:
        with open("genesis_data.json.tmp", "w") as f:
            f.write(f'{{"MQ135_BEFORE": {MQ135_BEFORE}, "MQ135_AFTER": {MQ135_AFTER}, "LUX": {LUX}}}')
        import os
        os.rename("genesis_data.json.tmp", "genesis_data.json")
    except Exception as e:
        print("JSON update failed:", e)


def check_wifi():
    """Check if WiFi is connected (assumes boot.py handles connection)"""
    wlan = network.WLAN(network.STA_IF)
    return wlan.active() and wlan.isconnected()


# ---------------- MAIN ----------------
def main():
    # Get WiFi status
    wlan = network.WLAN(network.STA_IF)

    # Calibrate sensors
    calibrate_sensors()

    print("--- GAIA SENTINEL: GENESIS NODE ACTIVE ---")
    print(f"Device ID: {CLIENT_ID}")
    print("Pump: ALWAYS ON")
    print("Note: WiFi connection managed by boot.py")

    while True:
        # 1. CHECK WIFI STATUS
        wifi_connected = check_wifi()

        if not wifi_connected:
            # Blink red LED to indicate no WiFi
            led_red.on()
            time.sleep_ms(100)
            led_red.off()
            time.sleep_ms(100)
            print("WiFi NOT Connected - Continuing with local logging only")

        # 2. DATA ACQUISITION (always happens regardless of WiFi)
        mq135_before_raw = read_mq135_sensor(mq135_before)
        mq135_after_raw = read_mq135_sensor(mq135_after)
        lux_value = read_lux()

        # Calculate PPM values
        mq135_before_ppm = int((mq135_before_raw / mq135_before_baseline) * 40)
        mq135_after_ppm = int((mq135_after_raw / mq135_after_baseline) * 40)

        print("\n[GENESIS DATA]")
        print(f"  MQ135-BEFORE: {mq135_before_ppm} PPM")
        print(f"  MQ135-AFTER: {mq135_after_ppm} PPM")
        print(f"  LUX: {lux_value}")
        print(f"  WiFi: {'Connected' if wifi_connected else 'Disconnected'}")

        # 3. Update LCD (always)
        update_lcd(mq135_before_ppm, mq135_after_ppm, lux_value)

        # 4. VISUAL ALERT for gas levels
        if mq135_before_ppm > GAS_LIMIT_BEFORE:
            if wifi_connected:
                led_red.on()
            print("  STATUS: HIGH POLLUTION")
        else:
            if wifi_connected:
                led_red.off()
            print("  STATUS: NORMAL")

        # 5. Update local JSON (ALWAYS - for localhost website)
        update_json(mq135_before_ppm, mq135_after_ppm, lux_value)

        # 6. DATA TRANSMISSION TO SERVER (only if WiFi connected)
        if wifi_connected:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect((SERVER_IP, SERVER_PORT))

                led_green.on()

                msg = "DATA {} AQI_INPUT={} AQI_OUTPUT={} LUX={}\n".format(
                    CLIENT_ID, mq135_before_ppm, mq135_after_ppm, lux_value
                )
                s.send(msg.encode())
                print("  Data sent to server successfully")

                time.sleep_ms(200)
                led_green.off()
                s.close()

            except Exception as e:
                print("Socket Error:", str(e))
                # Brief red blink for socket error
                for _ in range(2):
                    led_red.on()
                    time.sleep_ms(100)
                    led_red.off()
                    time.sleep_ms(100)
        else:
            print("  Skipping server transmission - WiFi not connected")

        time.sleep(LOOP_INTERVAL)
        gc.collect()


if __name__ == "__main__":
    main()
