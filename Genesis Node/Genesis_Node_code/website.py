# ═══════════════════════════════════════════════════════════════════════════════
# GAIA TITAN KERNEL v11.6 (Disconnect Feature Added)
# ═══════════════════════════════════════════════════════════════════════════════
import network, socket, time, json, machine, os, gc, ubinascii, select, _thread, micropython

micropython.alloc_emergency_exception_buf(100)

node_id = "GS-GENESIS-KVKHGS"

# ─── 1. GLOBAL CONFIGURATION ───
class Config:
    AP_SSID = node_id
    AP_PASS = "arv123456"
    AP_IP = "192.168.4.1"
    WIFI_FILE = "gaia_wifi.json"
    SENSOR_FILE = "genesis_data.json"
    HTTP_PORT = 80
    DNS_PORT = 53
    BUFFER_SIZE = 1024
    SENSOR_INTERVAL_MS = 3000
    WATCHDOG_INTERVAL_MS = 15000
    SOCKET_TIMEOUT = 4.0
    HIST_SIZE = 20


# ─── 2. FILE SYSTEM MANAGER ───
class FileManager:
    @staticmethod
    def read_json(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return None

    @staticmethod
    def write_json(filename, data):
        tmp_name = filename + ".tmp"
        try:
            with open(tmp_name, 'w') as f:
                json.dump(data, f)
            os.rename(tmp_name, filename)
            return True
        except:
            return False

    @staticmethod
    def get_disk_usage():
        try:
            fs = os.statvfs('/')
            return {"total": fs[0] * fs[2], "free": fs[0] * fs[3], "used": (fs[0] * fs[2]) - (fs[0] * fs[3])}
        except:
            return {"total": 0, "free": 0}


# ─── 3. SYSTEM CORE ───
class SystemCore:
    def __init__(self):
        self.sta = network.WLAN(network.STA_IF)
        self.ap = network.WLAN(network.AP_IF)
        self.start_time = time.time()
        self.node_id = "INIT"
        self.current_theme = "green"
        self.sensor_data = {"sensors": {}}
        self.history = {}
        self._init_config()

    def _init_config(self):
        cfg = FileManager.read_json(Config.WIFI_FILE)
        if cfg and "node_id" in cfg:
            self.node_id = cfg["node_id"]
        else:
            try:
                self.node_id = node_id
            except:
                self.node_id = node_id
        if cfg and "theme" in cfg: self.current_theme = cfg["theme"]
        print(f"[SYS] ID: {self.node_id}")

    def get_uptime(self):
        return time.time() - self.start_time

    def save_config(self, ssid=None, password=None, theme=None):
        data = FileManager.read_json(Config.WIFI_FILE) or {}
        if ssid: data['ssid'] = ssid
        if password: data['password'] = password
        if theme:
            data['theme'] = theme
            self.current_theme = theme
        if 'node_id' not in data: data['node_id'] = self.node_id
        FileManager.write_json(Config.WIFI_FILE, data)

    def forget_wifi(self):
        """Disconnects and removes credentials from file"""
        print("[WIFI] Forgetting network...")
        # 1. Hardware Disconnect
        if self.sta.isconnected():
            self.sta.disconnect()
        self.sta.active(False)
        time.sleep(0.5)
        self.sta.active(True)  # Ready for new scan

        # 2. File Cleanup
        data = FileManager.read_json(Config.WIFI_FILE) or {}
        if 'ssid' in data: del data['ssid']
        if 'password' in data: del data['password']
        FileManager.write_json(Config.WIFI_FILE, data)
        return True

    def start_ap_mode(self):
        self.ap.active(True)
        try:
            self.ap.ifconfig((Config.AP_IP, '255.255.255.0', Config.AP_IP, Config.AP_IP))
            self.ap.config(essid=Config.AP_SSID, password=Config.AP_PASS, authmode=3)
        except:
            self.ap.config(essid=Config.AP_SSID, authmode=0)

    def connect_wifi(self, ssid, password):
        self.sta.active(True)
        self.sta.disconnect()
        time.sleep(0.2)
        print(f"[WIFI] Connecting to {ssid}...")
        try:
            self.sta.connect(ssid, password)
            for _ in range(20):
                time.sleep(0.5)
                if self.sta.isconnected():
                    print(f"[WIFI] Connected: {self.sta.ifconfig()[0]}")
                    self.save_config(ssid=ssid, password=password)
                    return True
        except Exception as e:
            print(f"[WIFI] Error: {e}")
        self.sta.disconnect()
        return False

    def scan_networks(self):
        self.sta.active(True)
        try:
            if not self.sta.isconnected():
                self.sta.disconnect()
                time.sleep(0.1)
            raw = self.sta.scan()
            nets = {}
            for n in raw:
                ssid = n[0].decode('utf-8')
                if ssid and (ssid not in nets or n[3] > nets[ssid]['rssi']):
                    nets[ssid] = {"ssid": ssid, "rssi": n[3], "sec": n[4] > 0}
            return sorted(nets.values(), key=lambda x: x['rssi'], reverse=True)
        except:
            return []

    def get_full_status(self):
        wifi_conn = self.sta.isconnected()
        rssi = -100
        if wifi_conn:
            try:
                rssi = self.sta.status('rssi')
            except:
                pass
        return {
            "sys": {"id": self.node_id, "uptime": self.get_uptime(), "mem_free": gc.mem_free(),
                    "theme": self.current_theme},
            "wifi": {"conn": wifi_conn, "ssid": self.sta.config('essid') if wifi_conn else None,
                     "ip": self.sta.ifconfig()[0] if wifi_conn else None, "rssi": rssi},
            "sensors": self.sensor_data.get('sensors', {})
        }


# ─── 4. BACKGROUND SERVICE ───
class BackgroundService:
    def __init__(self, system):
        self.sys = system
        self.running = False

    def _update_history(self, key, val):
        if key not in self.sys.history: self.sys.history[key] = [0] * Config.HIST_SIZE
        try:
            num = float(''.join(c for c in str(val) if c.isdigit() or c == '.' or c == '-'))
        except:
            num = 0
        self.sys.history[key].append(num)
        if len(self.sys.history[key]) > Config.HIST_SIZE: self.sys.history[key].pop(0)
        return self.sys.history[key]

    def _monitor_loop(self):
        print("[BG] Service Active")
        last_check = time.ticks_ms()
        while True:
            try:
                raw = FileManager.read_json(Config.SENSOR_FILE)
                if raw:
                    processed = {}
                    for k, v in raw.items():
                        processed[k] = {"val": str(v), "hist": self._update_history(k, v)}
                    self.sys.sensor_data = {"sensors": processed}
            except:
                pass

            now = time.ticks_ms()
            if time.ticks_diff(now, last_check) > Config.WATCHDOG_INTERVAL_MS:
                # Watchdog only runs if we HAVE credentials saved
                cfg = FileManager.read_json(Config.WIFI_FILE)
                if cfg and 'ssid' in cfg and not self.sys.sta.isconnected():
                    print("[WD] Reconnecting...")
                    self.sys.sta.connect(cfg['ssid'], cfg['password'])
                last_check = now
            gc.collect()
            time.sleep_ms(Config.SENSOR_INTERVAL_MS)

    def start(self):
        if not self.running:
            _thread.start_new_thread(self._monitor_loop, ())
            self.running = True


# ─── 5. HTTP SERVER ───
class WebServer:
    def __init__(self, system):
        self.sys = system
        self.dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dns.setblocking(False)
        self.dns.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.dns.bind(('', Config.DNS_PORT))

        self.http = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.http.setblocking(False)
        self.http.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.http.bind(('', Config.HTTP_PORT))
        self.http.listen(5)
        print("[NET] Servers Ready")

    def _handle_dns(self):
        try:
            data, addr = self.dns.recvfrom(512)
            packet = data[:2] + b'\x81\x80' + data[4:6] + data[4:6] + b'\x00\x00\x00\x00' + data[12:] + \
                     b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04' + bytes(map(int, Config.AP_IP.split('.')))
            self.dns.sendto(packet, addr)
        except:
            pass

    def _handle_http(self, conn):
        try:
            conn.settimeout(Config.SOCKET_TIMEOUT)
            req = conn.recv(Config.BUFFER_SIZE).decode()

            if "GET /api/status" in req:
                self._send_json(conn, self.sys.get_full_status())
            elif "GET /api/scan" in req:
                self._send_json(conn, {"nets": self.sys.scan_networks()})

            elif "POST /connect" in req:
                try:
                    body = req.split('\r\n\r\n')[1]
                    d = json.loads(body)
                    ok = self.sys.connect_wifi(d['ssid'], d['password'])
                    if ok:
                        self._send_json(conn, {"success": True})
                    else:
                        self._send_json(conn, {"success": False})
                except:
                    self._send_json(conn, {"success": False})

            # --- DISCONNECT ENDPOINT ---
            elif "POST /api/disconnect" in req:
                self.sys.forget_wifi()
                self._send_json(conn, {"success": True})

            elif "POST /api/theme" in req:
                try:
                    body = req.split('\r\n\r\n')[1]
                    d = json.loads(body)
                    self.sys.save_config(theme=d['theme'])
                    self._send_json(conn, {"success": True})
                except:
                    self._send_json(conn, {"success": False})

            elif "POST /api/control" in req:
                if "reboot" in req:
                    self._send_json(conn, {"msg": "Rebooting..."})
                    time.sleep(0.5)
                    machine.reset()
                else:
                    self._send_json(conn, {"msg": "Unknown"})
            elif any(x in req for x in ["generate_204", "gen_204", "ncsi", "apple"]):
                conn.send(f"HTTP/1.1 302 Found\r\nLocation: http://{Config.AP_IP}/\r\n\r\n".encode())
            else:
                self._serve_file(conn, "index.html")
        except:
            pass
        finally:
            conn.close()

    def _send_json(self, conn, data, status=200):
        try:
            payload = json.dumps(data).encode()
            head = f"HTTP/1.1 {status} OK\r\nContent-Type: application/json\r\nCache-Control: no-cache\r\n\r\n"
            conn.send(head.encode())
            conn.send(payload)
        except:
            pass

    def _serve_file(self, conn, path):
        try:
            os.stat(path)
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(1024)
                    if not chunk: break
                    conn.send(chunk)
        except OSError:
            conn.send(b"HTTP/1.1 404 Not Found\r\n\r\nFile Not Found")


# ─── 6. RUN ───
def run():
    core = SystemCore()
    print(f"--- GAIA NODE: {core.node_id} ---")
    core.start_ap_mode()
    bg = BackgroundService(core)
    bg.start()

    saved = FileManager.read_json(Config.WIFI_FILE)
    if saved and 'ssid' in saved: core.connect_wifi(saved['ssid'], saved['password'])

    srv = WebServer(core)
    while True:
        try:
            r, _, _ = select.select([srv.dns, srv.http], [], [], 0.5)
            for s in r:
                if s is srv.dns:
                    srv._handle_dns()
                elif s is srv.http:
                    try:
                        conn, addr = srv.http.accept()
                        srv._handle_http(conn)
                    except OSError:
                        pass
            gc.collect()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERR] {e}")
            time.sleep(1)


if __name__ == "__main__":
    run()