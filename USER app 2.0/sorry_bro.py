def _upload_worker(self):
    def run_cmd(cmd_list, capture_output=False):
        try:
            if capture_output:
                return subprocess.run(cmd_list, check=True, text=True, capture_output=True)
            else:
                return subprocess.run(cmd_list, check=True)
        except FileNotFoundError as e:
            prog = cmd_list[0]
            basename = os.path.basename(prog).lower()
            if "esptool" in basename:
                alt = [sys.executable, "-m", "esptool"] + cmd_list[1:]
                self.log(f"⚠️ '{prog}' not found — trying: {' '.join(alt)}")
                return run_cmd(alt, capture_output=capture_output)
            elif "mpremote" in basename or "mpremote.exe" in basename:
                alt = [sys.executable, "-m", "mpremote"] + cmd_list[1:]
                self.log(f"⚠️ '{prog}' not found — trying: {' '.join(alt)}")
                return run_cmd(alt, capture_output=capture_output)
            else:
                found = shutil.which(prog)
                if found:
                    cmd_list[0] = found
                    return run_cmd(cmd_list, capture_output=capture_output)
                raise FileNotFoundError(f"Command '{prog}' not found. Install it or ensure it's on PATH.") from e
        except subprocess.CalledProcessError as e:
            raise

    def flash_micropython(port, firmware_bin_path):
        if not os.path.isfile(firmware_bin_path):
            raise FileNotFoundError(f"Firmware file not found: {firmware_bin_path}")

        self.log("\n⚡ Erasing flash (ESP32)...")
        run_cmd([
            "esptool.py",
            "--chip", "esp32",
            "--port", port,
            "erase_flash"
        ])

        self.log("\n⚡ Writing MicroPython firmware (ESP32)...")
        run_cmd([
            "esptool.py",
            "--chip", "esp32",
            "--port", port,
            "--baud", "460800",
            "write_flash",
            "-z",
            "0x1000",
            firmware_bin_path
        ])

        time.sleep(2)
        self.log("✅ Flash complete!")

    def upload_file(port, filepath):
        self.log(f"⬆️ Uploading {filepath} ...")
        run_cmd(["mpremote", "connect", port, "fs", "cp", filepath, ":/"])
        self.log("Uploading files to ESP32 completed...")
        return True

    def soft_reboot(port):
        run_cmd(["mpremote", "connect", port, "reset"])
        return True

    def modify_main_py(path, replacements):
        with open(path, "r", encoding="utf-8") as f:
            content = f.readlines()

        new_lines = []
        for line in content:
            changed = False
            for key, new_value in replacements.items():
                if line.strip().startswith(key + " "):
                    line = f'{key} = "{new_value}"\n'
                    changed = True
                    break
            new_lines.append(line)

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    def generate_random(length=6):
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_password(length=6):
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
        return ''.join(random.choice(chars) for _ in range(length))

    try:
        self.abc.configure(state='disabled')

        ssid = self.ssid_entry.get().strip()
        pwd = self.pass_entry.get().strip()
        port = self.port_menu.get().strip()
        ip_address = '192.168.1.7'
        port1 = 5050
        # check if user id available

        client_id = f"GS-{self.aw}-{generate_random()}"
        node_password = f"{generate_password()}"

        MICROPYTHON_FIRMWARE = "C:\\Users\\123\\PycharmProjects\\PythonProject\\ipropler technologies\\USER app\\ESP32_GENERIC-20250911-v1.26.1.bin"  # Download from micropython.org

        if "No device" in port:
            messagebox.showerror("ESP Not Found", "No ESP8266 detected!")
            self.abc.configure(state='normal')
            return

        if not ssid or not pwd:
            messagebox.showerror("Missing Data", "Please fill all fields!")
            self.abc.configure(state='normal')
            return

        if self.aw == "AIR":
            MAIN_FILE = "C:\\Users\\123\\PycharmProjects\\PythonProject\\ipropler technologies\\USER app\\main_air.py"

            # Modify File
            self.log('Updating Files...')
            modify_main_py(MAIN_FILE,
                           {"SERVER_IP": str(ip_address), "WIFI_SSID": ssid, "WIFI_PASS": pwd, 'SERVER_PORT': port1,
                            'CLIENT_ID': client_id})
            self.log('Updating Files Completed...')

            # Flash ESP8266
            self.log('Flashing ESP32...')
            # flash_micropython(port, MICROPYTHON_FIRMWARE)

            # Wait for reboot
            time.sleep(3)

            # Step 2: Upload code
            self.log('Uploading Files...')
            up = upload_file(port, MAIN_FILE)

            # Step 3: Reboot board
            self.log("🔄 Rebooting ESP32...")
            down = soft_reboot(port)

            # Check if the process is successful or not
            if up == True and down == True:
                self.log("Upload successful!")
                iPT_UA_database.add_air_node_online(client_id, node_password, 0, 0, 0, 0, 'False', 0, 'True')
                messagebox.showinfo("Success",
                                    f"ESP32 programmed successfully! \n\n NODE NAME: {client_id} \n PASSWORD: {node_password} \n\n Credentials Copied to Clipboard!")
                pyperclip.copy(f'NODE NAME: {client_id} \n PASSWORD: {node_password}')
                self.destroy()
            else:
                self.log("Upload failed!")
                messagebox.showerror("Upload Failed", "Could not upload code to ESP8266.")
                self.destroy()

        elif self.aw == 'WATER':
            MAIN_FILE = "C:\\Users\\123\\PycharmProjects\\PythonProject\\ipropler technologies\\USER app\\main_water.py"

            # Modify File
            self.log('Updating Files...')
            modify_main_py(MAIN_FILE,
                           {"SERVER_IP": str(ip_address), "WIFI_SSID": ssid, "WIFI_PASS": pwd, 'SERVER_PORT': port1,
                            'CLIENT_ID': client_id})
            self.log('Updating Files Completed...')

            # Flash ESP8266
            self.log('Flashing ESP8266...')
            # flash_micropython(port, MICROPYTHON_FIRMWARE)

            # Wait for reboot
            time.sleep(3)

            # Step 2: Upload code
            self.log('Uploading Files...')
            up = upload_file(port, MAIN_FILE)

            # Step 3: Reboot board
            self.log("🔄 Rebooting ESP8266...")
            down = soft_reboot(port)

            # Check if the process is successful or not
            if up == True and down == True:
                self.log("Upload successful!")
                iPT_UA_database.add_water_node_online(client_id, node_password, 0, 0, 'False', 0, 'True')
                messagebox.showinfo("Success",
                                    f"ESP8266 programmed successfully! \n\n NODE NAME: {client_id} \n PASSWORD: {node_password} \n\n Credentials Copied to Clipboard!")
                pyperclip.copy(f'NODE NAME: {client_id} \n PASSWORD: {node_password}')
                self.destroy()
            else:
                self.log("Upload failed!")
                messagebox.showerror("Upload Failed", "Could not upload code to ESP8266.")
                self.destroy()

    except Exception as e:
        self.log(f"Upload failed! {e}")
        messagebox.showerror("Upload Failed", "Could not upload code to ESP8266.")
        self.destroy()

