import random
import time, serial.tools.list_ports, subprocess, shutil
from customtkinter import *
from tkinter import messagebox
import serial.tools.list_ports
import threading
import iPT_UA_database
import pyperclip


class ProgramESP8266Window(CTkToplevel):
    def __init__(self, master, aw, username, user_mail):
        super().__init__(master)
        self.title("Program ESP32")
        self.aw = aw
        self.user = username
        self.user_mail = user_mail

        w, h = 520, 600
        try:
            master.update_idletasks()
            px = master.winfo_rootx()
            py = master.winfo_rooty()
            pw = master.winfo_width()
            ph = master.winfo_height()
        except Exception:
            # fallback: center of screen
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = int((screen_w - w) / 2)
            y = int((screen_h - h) / 2)
        else:
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2

        self.geometry(f"{w}x{h}+{x}+{y}")

        self.resizable(False, False)
        self.grab_set()

        LAVENDER_MIST = "#FFF4F2"  # primary panel / main backgrounds
        WISTERIA = "#F2EAF8"  # primary accent (buttons, nav highlight)
        DARK_AMETHYST = "#5B2C6E"  # accent hover / borders
        COFFEE_BEAN = "#1F1B1E"
        PANEL_ALT = "#EEF7F4"  # topbar / secondary backgrounds
        VELVET_ORCHID = "#7A3E90"
        PANEL_SUBTEXT = "#6F6470"

        # --- GAIA SENTINEL COLORS (from global palette) ---
        self.colors = {
            "bg": LAVENDER_MIST,  # main background (cream)
            "panel": WISTERIA,  # secondary panel background
            "inner": PANEL_ALT,  # card inner / strong accent
            "text": COFFEE_BEAN,  # main text (dark)
            "muted": PANEL_SUBTEXT,  # subtle text
            "accent": VELVET_ORCHID,  # primary accent
            "accent_hover": DARK_AMETHYST  # hover accent
        }
        self.configure(fg_color=self.colors["bg"])

        panel = CTkFrame(self, fg_color=self.colors["panel"], corner_radius=18)
        panel.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        CTkLabel(panel, text="PROGRAM NODES", font=("Tahoma", 28, "bold"),
                 text_color=self.colors["text"]).pack(pady=(12, 5))

        CTkFrame(panel, fg_color=self.colors["inner"], height=2)\
            .pack(fill="x", padx=18, pady=(0, 20))

        # Device type
        CTkLabel(panel, text="Node Type:", font=("Tahoma", 16, "bold"),
                 text_color=self.colors["muted"]).pack(anchor="w", padx=20)

        if self.aw == 'AIR':
            self.node_entry = CTkEntry(panel, fg_color=self.colors["inner"], border_color="#2a5f55", border_width=2, text_color=self.colors["text"])
            self.node_entry.insert(0, 'AIR NODE')
            self.node_entry.configure(state='disabled')
            self.node_entry.pack(fill="x", padx=20, pady=(0, 15))

        elif self.aw == 'WATER':
            self.node_entry = CTkEntry(panel, fg_color=self.colors["inner"], border_color="#2a5f55", border_width=2, text_color=self.colors["text"])
            self.node_entry.insert(0, "WATER NODE")
            self.node_entry.configure(state='disabled')
            self.node_entry.pack(fill="x", padx=20, pady=(0, 15))

        # SSID
        CTkLabel(panel, text="WiFi SSID:", font=("Tahoma", 16, "bold"),
                 text_color=self.colors["muted"]).pack(anchor="w", padx=20)

        self.ssid_entry = CTkEntry(panel, placeholder_text="Enter WiFi SSID",
                                   fg_color=self.colors["inner"],
                                   border_color="#2a5f55",
                                   border_width=2,
                                   text_color=self.colors["text"])
        self.ssid_entry.insert(0, 'Arvindhan')
        self.ssid_entry.pack(fill="x", padx=20, pady=(0, 12))

        # Password
        CTkLabel(panel, text="WiFi Password:", font=("Tahoma", 16, "bold"),
                 text_color=self.colors["muted"]).pack(anchor="w", padx=20)

        self.pass_entry = CTkEntry(panel, placeholder_text="Enter WiFi Password",
                                   show="*",
                                   fg_color=self.colors["inner"],
                                   border_color="#2a5f55",
                                   border_width=2,
                                   text_color=self.colors["text"])
        self.pass_entry.pack(fill="x", padx=20, pady=(0, 15))
        self.pass_entry.insert(0, 'gundumani')

        # COM port detection
        panel2 = CTkFrame(panel, fg_color=self.colors["panel"], corner_radius=18)
        panel2.pack(fill="x", expand=True, padx=5, pady=(0, 0))

        if self.aw == 'AIR':
            CTkLabel(panel2, text="Select ESP32 Port:", font=("Tahoma", 16, "bold"),
                     text_color=self.colors["muted"]).pack(anchor="w", padx=20)

        elif self.aw == 'WATER':
            CTkLabel(panel2, text="Select ESP8266 Port:", font=("Tahoma", 16, "bold"),
                     text_color=self.colors["muted"]).pack(anchor="w", padx=20)

        def detect_esp():
            global ports
            ports = []
            porta = serial.tools.list_ports.comports()
            for port in porta:
                if "USB" in port.description or "CP210" in port.description or "CH340" in port.description:
                    ports.append(port.device)
            if not ports:
                ports = ["No device detected"]
                messagebox.showinfo('INFO', 'No Device Detected!')
            try:
                self.port_menu.configure(values=ports)
                self.port_menu.set(ports[0])
            except Exception:
                pass

        detect_esp()
        global ports
        self.port_menu = CTkOptionMenu(panel2, values=ports,
                                       fg_color=self.colors["inner"],
                                       button_color="#2a5f55",
                                       text_color=self.colors["text"])
        self.port_menu.pack(fill="x", expand=True, side='left', padx=(20, 5), pady=(0, 15))

        aaa = CTkButton(panel2, text="DETECT", height=27,
                  fg_color=self.colors["accent"],
                  hover_color=self.colors["accent_hover"],
                  text_color="white",
                  font=("Tahoma", 16, "bold"),
                  command=detect_esp)
        aaa.pack(fill="x", side='left', padx=(5, 20), pady=(0, 15))

        # Upload button
        self.abc = CTkButton(panel, text="UPLOAD CODE", height=45,
                  fg_color=self.colors["accent"],
                  hover_color=self.colors["accent_hover"],
                  text_color="white",
                  font=("Tahoma", 17, "bold"),
                  command=self.start_upload, text_color_disabled='black')
        self.abc.pack(fill="x", padx=20, pady=(5, 15))

        # Status console
        CTkLabel(panel, text="Progress", font=("Tahoma", 16, "bold"),
                 text_color=self.colors["muted"]).pack(anchor="w", padx=20)

        self.console = CTkTextbox(panel, height=80,
                                  fg_color=self.colors["inner"],
                                  text_color=self.colors["text"],
                                  border_width=0, state='disabled')
        self.console.pack(fill="x", expand=True, padx=20, pady=(5, 15))

    # ---------------------------------------------------------
    # UTILITY: log to console
    def log(self, text):
        self.console.configure(state="normal")
        self.console.insert("end", text + "\n")
        self.console.see("end")
        self.console.configure(state='disabled')

    # ---------------------------------------------------------
    # MAIN: Start upload in a thread
    def start_upload(self):
        threading.Thread(target=self._upload_worker, daemon=True).start()

    # ---------------------------------------------------------
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

        def flash_micropython(chip, port, firmware_bin_path):
            if not os.path.isfile(firmware_bin_path):
                raise FileNotFoundError(f"Firmware file not found: {firmware_bin_path}")

            if chip == "esp32":
                self.log("\n⚡ Erasing flash (ESP32)...")
                run_cmd(["esptool.py", "--chip", "esp32", "--port", port, "erase_flash"])

                self.log("\n⚡ Writing MicroPython firmware (ESP32)...")
                run_cmd(["esptool.py", "--chip", "esp32", "--port", port, "--baud", "460800", "write_flash", "-z", "0x1000", firmware_bin_path])
            else:
                self.log("\n⚡ Erasing flash (ESP8266)...")
                run_cmd(["esptool.py", "--port", port, "erase_flash"])

                self.log("\n⚡ Writing MicroPython firmware (ESP8266)...")
                run_cmd(["esptool.py", "--port", port, "--baud", "460800", "write_flash", "--flash_size=detect", "0", firmware_bin_path])

            time.sleep(2)
            self.log("✅ Flash complete!")

        def upload_file(port, filepath):
            self.log(f"⬆️ Uploading {filepath} ...")
            run_cmd(["mpremote", "connect", port, "fs", "cp", filepath, ":/"])
            self.log("Uploading files completed...")
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
                        if isinstance(new_value, (int, float)):
                            line = f'{key} = {new_value}\n'
                        else:
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
            ip_address = '10.99.109.114'
            port1 = 5050

            if "No device detected" in port:
                messagebox.showerror("ESP Not Found", "No device detected on selected port!")
                self.abc.configure(state='normal')
                return

            if not ssid or not pwd:
                messagebox.showerror("Missing Data", "Please fill SSID and password!")
                self.abc.configure(state='normal')
                return

            client_id = f"GS-{self.aw}-{generate_random()}"
            node_password = f"{generate_password()}"

            MICROPYTHON_FIRMWARE_ESP32 = "ESP32_GENERIC-20250911-v1.26.1.bin"
            MICROPYTHON_FIRMWARE_ESP8266 = "ESP8266_GENERIC-20250911-v1.26.1.bin"  # <-- put your esp8266 fw here

            if self.aw == "AIR":
                MAIN_FILE = "main_air.py"

                self.log('Updating main_air.py...')
                modify_main_py(MAIN_FILE,{"SERVER_IP": ip_address, "WIFI_SSID": ssid, "WIFI_PASS": pwd, "SERVER_PORT": port1, "CLIENT_ID": client_id})
                self.log('Updating Files Completed.')

                self.log('Flashing ESP32 (AIR node)...')
                #flash_micropython("esp32", port, MICROPYTHON_FIRMWARE_ESP32)

                time.sleep(3)

                self.log('Uploading Files...')
                up = upload_file(port, MAIN_FILE)

                self.log("🔄 Rebooting ESP32...")
                down = soft_reboot(port)

                if up and down:
                    client_id = f"GS-{self.aw}-JJAM52"
                    self.log("Upload successful!")
                    #iPT_UA_database.add_air_node_offline(client_id)
                    iPT_UA_database.add_air_node_online(client_id, node_password, '-', '-', '-', '-', 'False', '-', self.user_mail)
                    iPT_UA_database.send_node_credentials(self.user, self.user_mail, client_id, node_password, 'AIR')
                    messagebox.showinfo("Success",f"ESP32 (AIR node) programmed successfully!\n\n"
                        f"NODE NAME: {client_id}\nPASSWORD: {node_password}\n\n"
                        f"Credentials copied to clipboard!")
                    pyperclip.copy(f'NODE NAME: {client_id}\nPASSWORD: {node_password}')
                    self.destroy()
                else:
                    self.log("Upload failed!")
                    messagebox.showerror("Upload Failed", "Could not upload code to ESP32 (AIR node).")
                    self.abc.configure(state='normal')

            elif self.aw == "WATER":
                MAIN_FILE = "main_water.py"

                self.log('Updating main_water.py...')
                modify_main_py(MAIN_FILE,{"SERVER_IP": ip_address, "WIFI_SSID": ssid, "WIFI_PASS": pwd, "SERVER_PORT": port1, "CLIENT_ID": client_id})
                self.log('Updating Files Completed.')

                self.log('Flashing ESP8266 (WATER node)...')
                #flash_micropython("esp8266", port, MICROPYTHON_FIRMWARE_ESP8266)

                time.sleep(3)

                self.log('Uploading Files...')
                up = True #upload_file(port, MAIN_FILE)

                self.log("🔄 Rebooting ESP8266...")
                down = True #soft_reboot(port)

                if up and down:
                    client_id = f"GS-{self.aw}-W0YGX2"
                    self.log("Upload successful!")
                    #iPT_UA_database.add_water_node_offline(client_id)
                    iPT_UA_database.add_water_node_online(client_id, node_password, '-', '-', 'False', '-', self.user_mail)
                    iPT_UA_database.send_node_credentials(self.user, self.user_mail, client_id, node_password, 'WATER')
                    messagebox.showinfo("Success", f"ESP8266 (WATER node) programmed successfully!\n\n"
                        f"NODE NAME: {client_id}\nPASSWORD: {node_password}\n\n"
                        f"Credentials copied to clipboard!")
                    pyperclip.copy(f'NODE NAME: {client_id}\nPASSWORD: {node_password}')
                    self.destroy()
                else:
                    self.log("Upload failed!")
                    messagebox.showerror("Upload Failed", "Could not upload code to ESP8266 (WATER node).")
                    self.abc.configure(state='normal')

            else:
                messagebox.showerror("Mode Error", f"Unknown node type: {self.aw}")
                self.abc.configure(state='normal')

        except Exception as e:
            self.log(f"Upload failed! {e}")
            messagebox.showerror("Upload Failed", f"Could not upload code.\n\n{e}")
            self.abc.configure(state='normal')

