import os, sys, time, serial.tools.list_ports, subprocess, shutil

# === CONFIGURATION ===
MICROPYTHON_FIRMWARE = "C:\\Users\\123\PycharmProjects\PythonProject\ipropler technologies\\USER app\ESP8266_GENERIC-20250911-v1.26.1.bin"  # Download from micropython.org
MAIN_FILE = "C:\\Users\\123\PycharmProjects\PythonProject\ipropler technologies\\USER app\main.py"  # Your ESP8266 Python program
YES_WORD = "yes"

# === HELPER FUNCTIONS ===

def detect_esp8266():
    """Detects connected ESP8266 COM port."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "USB" in port.description or "CP210" in port.description or "CH340" in port.description:
            print(f"✅ ESP8266 detected on {port.device}")
            return port.device
    print("⚠️ No ESP8266 detected.")
    return None


def run_cmd(cmd_list, capture_output=False):
    """
    Run command list. If the literal command isn't found (FileNotFoundError),
    try to run as a Python module with the current interpreter:
      python -m <module> <args...>
    Returns subprocess.CompletedProcess
    """
    try:
        if capture_output:
            return subprocess.run(cmd_list, check=True, text=True, capture_output=True)
        else:
            return subprocess.run(cmd_list, check=True)
    except FileNotFoundError as e:
        # Try fallbacks for common tools: esptool.py -> python -m esptool
        prog = cmd_list[0]
        basename = os.path.basename(prog).lower()
        # reasonable guess: if prog contains "esptool", call python -m esptool
        if "esptool" in basename:
            alt = [sys.executable, "-m", "esptool"] + cmd_list[1:]
            print(f"⚠️ '{prog}' not found — trying: {' '.join(alt)}")
            return run_cmd(alt, capture_output=capture_output)
        elif "mpremote" in basename or "mpremote.exe" in basename:
            alt = [sys.executable, "-m", "mpremote"] + cmd_list[1:]
            print(f"⚠️ '{prog}' not found — trying: {' '.join(alt)}")
            return run_cmd(alt, capture_output=capture_output)
        else:
            # last resort: try shutil.which to find an executable name without extension
            found = shutil.which(prog)
            if found:
                cmd_list[0] = found
                return run_cmd(cmd_list, capture_output=capture_output)
            # give helpful error
            raise FileNotFoundError(f"Command '{prog}' not found. Install it or ensure it's on PATH.") from e
    except subprocess.CalledProcessError as e:
        # re-raise but keep message
        raise


def flash_micropython(port, firmware_bin_path):
    """
    Erase and flash MicroPython firmware using esptool.
    This will call:
       esptool.py --port COM5 erase_flash
       esptool.py --port COM5 --baud 460800 write_flash --flash_size=detect 0 firmware.bin
    If 'esptool.py' isn't found on PATH, the code will try: python -m esptool ...
    """
    if not os.path.isfile(firmware_bin_path):
        raise FileNotFoundError(f"Firmware file not found: {firmware_bin_path}")

    print("\n⚡ Erasing flash...")
    run_cmd(["esptool.py", "--port", port, "erase_flash"])

    print("\n⚡ Writing MicroPython firmware...")
    run_cmd([
        "esptool.py", "--port", port, "--baud", "460800", "write_flash",
        "--flash_size=detect", "0", firmware_bin_path
    ])

    # small pause for the board to restart
    time.sleep(2)
    print("✅ Flash complete!")

def upload_file(port, filepath):
    """Uploads a file to ESP8266 using mpremote."""
    print(f"⬆️ Uploading {filepath} ...")
    run_cmd(["mpremote", "connect", port, "fs", "cp", filepath, ":/"])


def soft_reboot(port):
    """Soft reboots the ESP8266."""
    run_cmd(["mpremote", "connect", port, "reset"])


# === MAIN FLOW ===
if __name__ == "__main__":
    print("⚙️  Gaia Sentinel ESP8266 Auto-Programmer")
    print("This will flash MicroPython and upload your code automatically.\n")

    consent = input("Type 'yes' to start programming: ").strip().lower()
    if consent != YES_WORD:
        print("❌ Aborted.")
        sys.exit(0)

    port = detect_esp8266()
    if not port:
        print("❌ No board found. Please connect your ESP8266 via USB.")
        sys.exit(1)

    # Step 1: Flash MicroPython
    #flash_micropython(port, MICROPYTHON_FIRMWARE)

    # Wait for reboot
    print("\n⏳ Waiting for ESP8266 to reboot...")
    time.sleep(3)

    # Step 2: Upload code
    upload_file(port, MAIN_FILE)

    # Step 3: Reboot board
    print("\n🔄 Rebooting ESP8266...")
    soft_reboot(port)

    print("\n✅ Done! Your ESP8266 is fully programmed.")
