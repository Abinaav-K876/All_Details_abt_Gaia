import socketserver
import threading
import datetime
import time
import signal
import logging
import socket
import re
from concurrent.futures import ThreadPoolExecutor
import iPT_UA_database
import os

# ---------------- CONFIG ----------------
HOST = '0.0.0.0'
PORT = 5050

OFFLINE_TIMEOUT = 10  # seconds (node considered offline after this)
READLINE_MAX_BYTES = 4096  # max bytes accepted from a single line

# Thread pools for DB/alerts/activity
AIR_EXECUTOR = ThreadPoolExecutor(max_workers=6)
WATER_EXECUTOR = ThreadPoolExecutor(max_workers=6)
HEPA_EXECUTOR = ThreadPoolExecutor(max_workers=6)
GENESIS_EXECUTOR = ThreadPoolExecutor(max_workers=6)
ALERT_EXECUTOR = ThreadPoolExecutor(max_workers=4)
ACTIVITY_EXECUTOR = ThreadPoolExecutor(max_workers=2)
HISTORY_EXECUTOR = ThreadPoolExecutor(max_workers=4)

# ---------------- STATE ----------------
LAST_SEEN = {}  # AIR: client_id -> datetime
LAST_SEEN_WATER = {}
LAST_SEEN_HEPA = {}
LAST_SEEN_GENESIS = {}

LAST_KNOWN_STATUS_AIR = {}
LAST_KNOWN_STATUS_WATER = {}
LAST_KNOWN_STATUS_HEPA = {}
LAST_KNOWN_STATUS_GENESIS = {}

LAST_SEEN_LOCK = threading.Lock()
LAST_SEEN_WATER_LOCK = threading.Lock()
LAST_SEEN_HEPA_LOCK = threading.Lock()
LAST_SEEN_GENESIS_LOCK = threading.Lock()
LAST_KNOWN_STATUS_LOCK = threading.Lock()

# Alert spam control
_last_alert_state = {}  # (node_id, node_type) -> (last_level, last_time)
ALERT_COOLDOWN_SECONDS = 15 * 60  # 15 minutes

# Risk constants
RISK_OK = "OK"
RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"

# ---------------- THRESHOLDS ----------------
AIR_THRESHOLDS = {
    "mq135": (150, 300, 500),
    "mq7": (200, 250, 300),
    "mq2": (750, 1000, 1250),
    "mq4": (650, 850, 1000),
    "mq6": (350, 500, 700),
    "temp": (None, None, 40),
}

WATER_THRESHOLDS = {
    "tds": (50, 75, 100),
    "temp": (None, None, 40),
}

HEPA_THRESHOLDS = {
    "aqi_before": (100, 200, 300),  # Input air quality
    "aqi_after": (50, 100, 150),  # Output air quality (stricter)
}

GENESIS_THRESHOLDS = {
    "aqi_input": (100, 200, 300),
    "aqi_output": (50, 100, 200),
    "lux": (None, None, 10000),  # Very bright light
}

# ---------------- logging ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(threadName)s - %(message)s", )
logger = logging.getLogger("monitor-server")

# ---------------- utility helpers ----------------
_keyvalue_re = re.compile(r"^([^=]+)=(.*)$")


def _safe_float(v):
    try:
        return float(v)
    except Exception:
        return None


def _max_risk(a, b):
    order = {RISK_OK: 0, RISK_LOW: 1, RISK_MEDIUM: 2, RISK_HIGH: 3}
    return a if order.get(a, 0) >= order.get(b, 0) else b


def _parse_kv_tokens(tokens):
    """Parse key=value tokens into dict"""
    out = {}
    for t in tokens:
        m = _keyvalue_re.match(t)
        if not m:
            continue
        k = m.group(1).strip().lower()
        v = m.group(2).strip()
        out[k] = v
    return out


def _normalize_node_key(node_row):
    if isinstance(node_row, (list, tuple)) and len(node_row) > 0:
        return node_row[0]
    return node_row


def _parse_aqi_list(aqi_raw):
    """Parse AQI value that might be a list [before, after]"""
    aqi_before = None
    aqi_after = None

    try:
        # Try to parse as list string
        if isinstance(aqi_raw, str):
            if aqi_raw.startswith('[') and aqi_raw.endswith(']'):
                import ast
                aqi_list = ast.literal_eval(aqi_raw)
                if isinstance(aqi_list, list) and len(aqi_list) >= 2:
                    aqi_before = _safe_float(aqi_list[0])
                    aqi_after = _safe_float(aqi_list[1])
                elif isinstance(aqi_list, list) and len(aqi_list) == 1:
                    aqi_before = _safe_float(aqi_list[0])
                else:
                    aqi_before = _safe_float(aqi_raw)
            else:
                aqi_before = _safe_float(aqi_raw)
        elif isinstance(aqi_raw, list):
            if len(aqi_raw) >= 2:
                aqi_before = _safe_float(aqi_raw[0])
                aqi_after = _safe_float(aqi_raw[1])
            elif len(aqi_raw) == 1:
                aqi_before = _safe_float(aqi_raw[0])
        else:
            aqi_before = _safe_float(aqi_raw)
    except Exception as e:
        logger.debug("Error parsing AQI list: %s", e)
        aqi_before = _safe_float(aqi_raw)

    return aqi_before, aqi_after


# ---------------- classification ----------------
def classify_air_node(mq135_ppm=None, mq7_ppm=None, mq2_ppm=None, mq4_ppm=None, mq6_ppm=None, temp_c=None, hum_pct=None):
    """Classify AIR node risk"""
    level = RISK_OK
    reasons = []

    def _eval_gas(sensor_key, value, display_name):
        nonlocal level, reasons
        if value is None:
            return
        thr = AIR_THRESHOLDS.get(sensor_key)
        if not thr:
            return
        l, m, h = thr
        if h is not None and value >= h:
            level = _max_risk(level, RISK_HIGH)
            reasons.append(f"Very high {display_name} level ({sensor_key.upper()} ≈ {value:.0f} ppm)")
        elif m is not None and value >= m:
            level = _max_risk(level, RISK_MEDIUM)
            reasons.append(f"Elevated {display_name} level ({sensor_key.upper()} ≈ {value:.0f} ppm)")
        elif l is not None and value >= l:
            level = _max_risk(level, RISK_LOW)
            reasons.append(f"{display_name} starting to rise ({sensor_key.upper()} ≈ {value:.0f} ppm)")

    _eval_gas("mq135", mq135_ppm, "air quality")
    _eval_gas("mq7", mq7_ppm, "CO")
    _eval_gas("mq2", mq2_ppm, "gas (MQ2)")
    _eval_gas("mq4", mq4_ppm, "gas (MQ4)")
    _eval_gas("mq6", mq6_ppm, "gas (MQ6)")

    thr_temp = AIR_THRESHOLDS.get("temp")
    if thr_temp and thr_temp[2] is not None and temp_c is not None:
        _, _, high_t = thr_temp
        if temp_c >= high_t:
            level = _max_risk(level, RISK_HIGH)
            reasons.append(f"Very high temperature ({temp_c:.1f} °C)")

    if not reasons:
        reasons.append("All sensors within normal range.")
    return level, reasons


def classify_water_node(tds_ppm, temp_c=None):
    level = RISK_OK
    reasons = []

    if tds_ppm is not None:
        l, m, h = WATER_THRESHOLDS["tds"]
        if h is not None and tds_ppm >= h:
            level = _max_risk(level, RISK_HIGH)
            reasons.append(f"Highly contaminated water (TDS ≈ {tds_ppm:.0f} ppm)")
        elif m is not None and tds_ppm >= m:
            level = _max_risk(level, RISK_MEDIUM)
            reasons.append(f"Poor water quality (TDS ≈ {tds_ppm:.0f} ppm)")
        elif l is not None and tds_ppm >= l:
            level = _max_risk(level, RISK_LOW)
            reasons.append(f"Increasing dissolved solids (TDS ≈ {tds_ppm:.0f} ppm)")

    thr_temp = WATER_THRESHOLDS.get("temp")
    if thr_temp and thr_temp[2] is not None and temp_c is not None:
        _, _, high_t = thr_temp
        if temp_c >= high_t:
            level = _max_risk(level, RISK_HIGH)
            reasons.append(f"Abnormally warm water ({temp_c:.1f} °C)")

    if not reasons:
        reasons.append("All sensors within normal range.")
    return level, reasons


def classify_hepa_node(aqi_before=None, aqi_after=None):
    """Classify HEPA node risk with before/after AQI values"""
    level = RISK_OK
    reasons = []

    # Check AQI before filtration (input air)
    if aqi_before is not None:
        l, m, h = HEPA_THRESHOLDS["aqi_before"]
        if aqi_before >= h:
            level = _max_risk(level, RISK_HIGH)
            reasons.append(f"Very unhealthy input air (AQI Before ≈ {aqi_before:.0f})")
        elif aqi_before >= m:
            level = _max_risk(level, RISK_MEDIUM)
            reasons.append(f"Poor input air quality (AQI Before ≈ {aqi_before:.0f})")
        elif aqi_before >= l:
            level = _max_risk(level, RISK_LOW)
            reasons.append(f"Moderate input air quality (AQI Before ≈ {aqi_before:.0f})")

    # Check AQI after filtration (output air)
    if aqi_after is not None:
        l, m, h = HEPA_THRESHOLDS["aqi_after"]
        if aqi_after >= h:
            level = _max_risk(level, RISK_HIGH)
            reasons.append(f"HEPA filtration insufficient (AQI After ≈ {aqi_after:.0f})")
        elif aqi_after >= m:
            level = _max_risk(level, RISK_MEDIUM)
            reasons.append(f"Output air quality degraded (AQI After ≈ {aqi_after:.0f})")
        elif aqi_after >= l:
            level = _max_risk(level, RISK_LOW)
            reasons.append(f"Output air quality needs attention (AQI After ≈ {aqi_after:.0f})")

    # Check filtration efficiency
    if aqi_before is not None and aqi_after is not None:
        if aqi_after >= aqi_before * 0.8:  # Less than 20% reduction
            level = _max_risk(level, RISK_HIGH)
            reasons.append(f"Poor filtration efficiency (Before: {aqi_before:.0f} → After: {aqi_after:.0f})")

    if not reasons:
        reasons.append("Air quality within safe range.")
    return level, reasons


def classify_genesis_node(aqi_input=None, aqi_output=None, lux=None):
    """Classify GENESIS node risk"""
    level = RISK_OK
    reasons = []

    # Check AQI input
    if aqi_input is not None:
        l, m, h = GENESIS_THRESHOLDS["aqi_input"]
        if aqi_input >= h:
            level = _max_risk(level, RISK_HIGH)
            reasons.append(f"Very unhealthy input air (AQI Input ≈ {aqi_input:.0f})")
        elif aqi_input >= m:
            level = _max_risk(level, RISK_MEDIUM)
            reasons.append(f"Poor input air quality (AQI Input ≈ {aqi_input:.0f})")
        elif aqi_input >= l:
            level = _max_risk(level, RISK_LOW)
            reasons.append(f"Moderate input air quality (AQI Input ≈ {aqi_input:.0f})")

    # Check AQI output
    if aqi_output is not None:
        l, m, h = GENESIS_THRESHOLDS["aqi_output"]
        if aqi_output >= h:
            level = _max_risk(level, RISK_HIGH)
            reasons.append(f"Filtration insufficient (AQI Output ≈ {aqi_output:.0f})")
        elif aqi_output >= m:
            level = _max_risk(level, RISK_MEDIUM)
            reasons.append(f"Output air quality degraded (AQI Output ≈ {aqi_output:.0f})")

    # Check light intensity
    if lux is not None:
        _, _, high_lux = GENESIS_THRESHOLDS["lux"]
        if high_lux is not None and lux >= high_lux:
            level = _max_risk(level, RISK_LOW)
            reasons.append(f"Very high light exposure (Lux ≈ {lux:.0f})")

    if not reasons:
        reasons.append("All sensors within normal range.")
    return level, reasons


# ---------------- alert logic ----------------
def maybe_send_node_alert(user_email, node_id, node_type, risk_level, reasons):
    """Send alert email and log to database"""
    if risk_level == RISK_OK or not user_email:
        return

    now = time.time()
    key = (node_id, node_type)
    last_level, last_time = _last_alert_state.get(key, (None, 0))

    should_send = False
    if last_level is None or last_level != risk_level or (now - last_time) > ALERT_COOLDOWN_SECONDS:
        should_send = True

    if not should_send:
        logger.debug("Skipping alert for %s %s (recently sent)", node_id, node_type)
        return

    _last_alert_state[key] = (risk_level, now)

    # Send email
    try:
        ALERT_EXECUTOR.submit(
            iPT_UA_database.send_mail_for_alert,
            user_email,
            node_id,
            node_type,
            risk_level,
            reasons,
        )
        logger.info("Queued alert email for %s (%s) risk=%s", node_id, node_type, risk_level)
    except Exception as e:
        logger.exception("Failed to queue alert task: %s", e)

    # Log alert to database
    try:
        alert_message = f"{node_type} Node '{node_id}' - {risk_level} Risk: {'; '.join(reasons)}"
        ALERT_EXECUTOR.submit(
            iPT_UA_database.log_alert_to_database,
            user_email,
            node_type,
            alert_message
        )
        logger.info("Logged alert to database for %s (%s)", node_id, node_type)
    except Exception as e:
        logger.exception("Failed to log alert to database: %s", e)


# ---------------- processors ----------------
def process_air_alert(client_id, mq135, mq7, mq2, mq4, mq6, temp, hum):
    mq135_f = _safe_float(mq135)
    mq7_f = _safe_float(mq7)
    mq2_f = _safe_float(mq2)
    mq4_f = _safe_float(mq4)
    mq6_f = _safe_float(mq6)
    temp_f = _safe_float(temp)
    hum_f = _safe_float(hum)

    try:
        user_email = iPT_UA_database.get_email_for_air_node(client_id)
    except Exception as e:
        logger.exception("DB lookup error for air node email: %s", e)
        user_email = None

    risk_level, reasons = classify_air_node(
        mq135_ppm=mq135_f, mq7_ppm=mq7_f, mq2_ppm=mq2_f,
        mq4_ppm=mq4_f, mq6_ppm=mq6_f, temp_c=temp_f, hum_pct=hum_f
    )
    maybe_send_node_alert(user_email, client_id, "AIR", risk_level, reasons)


def process_water_alert(client_id, tds_value, water_temp):
    tds_f = _safe_float(tds_value)
    temp_f = _safe_float(water_temp)

    try:
        user_email = iPT_UA_database.get_email_for_water_node(client_id)
    except Exception as e:
        logger.exception("DB lookup error for water node email: %s", e)
        user_email = None

    risk_level, reasons = classify_water_node(tds_f, temp_f)
    maybe_send_node_alert(user_email, client_id, "WATER", risk_level, reasons)


def process_hepa_alert(client_id, aqi_raw):
    """Process HEPA node alert with before/after AQI parsing"""
    # Parse AQI values (might be list [before, after])
    aqi_before, aqi_after = _parse_aqi_list(aqi_raw)

    try:
        user_email = iPT_UA_database.get_email_for_hepa_node(client_id)
    except Exception as e:
        logger.exception("DB lookup error for HEPA node email: %s", e)
        user_email = None

    risk_level, reasons = classify_hepa_node(aqi_before, aqi_after)
    maybe_send_node_alert(user_email, client_id, "HEPA", risk_level, reasons)


def process_genesis_alert(client_id, aqi_input, aqi_output, lux):
    """Process Genesis node alert"""
    aqi_in_f = _safe_float(aqi_input)
    aqi_out_f = _safe_float(aqi_output)
    lux_f = _safe_float(lux)

    try:
        user_email = iPT_UA_database.get_email_for_genesis_node(client_id)
    except Exception as e:
        logger.exception("DB lookup error for genesis node email: %s", e)
        user_email = None

    risk_level, reasons = classify_genesis_node(aqi_in_f, aqi_out_f, lux_f)
    maybe_send_node_alert(user_email, client_id, "GENESIS", risk_level, reasons)


# ---------------- Handler ----------------
class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        addr = self.client_address
        now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        logger.info("[%s] Connection from %s", now, addr)

        try:
            raw_line = self.rfile.readline(READLINE_MAX_BYTES)
            if not raw_line:
                return
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                return

            parts = line.split()
            if len(parts) < 2:
                logger.debug("Malformed line: %s", line)
                return

            msg_type = parts[0].upper()
            client_id = parts[1]

            # Update last seen
            now_dt = datetime.datetime.now()
            if "-AIR-" in client_id:
                with LAST_SEEN_LOCK:
                    LAST_SEEN[client_id] = now_dt
            elif "-WATER-" in client_id:
                with LAST_SEEN_WATER_LOCK:
                    LAST_SEEN_WATER[client_id] = now_dt
            elif "-HEPA-" in client_id:
                with LAST_SEEN_HEPA_LOCK:
                    LAST_SEEN_HEPA[client_id] = now_dt
            elif "-GENESIS-" in client_id:
                with LAST_SEEN_GENESIS_LOCK:
                    LAST_SEEN_GENESIS[client_id] = now_dt

            kv = _parse_kv_tokens(parts[2:])

            # ------------ AIR NODE ------------
            if "-AIR-" in client_id:
                mq135 = kv.get("mq135")
                mq7 = kv.get("mq7")
                mq2 = kv.get("mq2")
                mq4 = kv.get("mq4")
                mq6 = kv.get("mq6")
                temp = kv.get("temp")
                hum = kv.get("hum") or kv.get("humidity")

                logger.info("AIR %s -> MQ135=%s MQ7=%s MQ2=%s MQ4=%s MQ6=%s TEMP=%s HUM=%s",
                            client_id, mq135, mq7, mq2, mq4, mq6, temp, hum)

                try:
                    AIR_EXECUTOR.submit(_update_air_node_db_safe, client_id, mq135, mq7, mq2, mq4, mq6, hum, temp)
                    AIR_EXECUTOR.submit(_logs_air, client_id, mq135, mq7, mq2, mq4, mq6, hum, temp)
                except Exception:
                    logger.exception("Failed to schedule DB task for AIR node")

                try:
                    ALERT_EXECUTOR.submit(process_air_alert, client_id, mq135, mq7, mq2, mq4, mq6, temp, hum)
                except Exception:
                    logger.exception("Failed to schedule alert task for AIR node")

            # ------------ WATER NODE ------------
            elif "-WATER-" in client_id:
                tds_value = kv.get("tds") or kv.get("tds_ppm")
                water_temp = kv.get("temp") or kv.get("water_temp")

                logger.info("WATER %s -> TDS=%s TEMP=%s", client_id, tds_value, water_temp)

                try:
                    WATER_EXECUTOR.submit(_update_water_node_db_safe, client_id, tds_value, water_temp)
                    WATER_EXECUTOR.submit(_logs_water, client_id, tds_value, water_temp)
                except Exception:
                    logger.exception("Failed to schedule DB task for WATER node")

                try:
                    ALERT_EXECUTOR.submit(process_water_alert, client_id, tds_value, water_temp)
                except Exception:
                    logger.exception("Failed to schedule alert task for WATER node")

            # ------------ HEPA NODE ------------
            elif "-HEPA-" in client_id:
                aqi = kv.get("aqi")
                ps = kv.get("ps") or kv.get("puri") or "OFF"
                bat = kv.get("bat") or "0"

                logger.info("HEPA %s -> AQI=%s PS=%s BAT=%s", client_id, aqi, ps, bat)

                try:
                    HEPA_EXECUTOR.submit(_update_hepa_node_db_safe, client_id, aqi, ps, bat)
                    HEPA_EXECUTOR.submit(_logs_hepa, client_id, aqi, ps)
                except Exception:
                    logger.exception("Failed to schedule DB task for HEPA node")

                try:
                    # Pass raw AQI (might be list) to alert processor
                    ALERT_EXECUTOR.submit(process_hepa_alert, client_id, aqi)
                except Exception:
                    logger.exception("Failed to schedule alert task for HEPA node")

            # ------------ GENESIS NODE ------------
            elif "-GENESIS-" in client_id:
                aqi_input = kv.get("aqi") or kv.get("aqi_input")
                aqi_output = kv.get("aqi_output") or kv.get("aqi_out")
                lux = kv.get("lux") or kv.get("light")
                ps = kv.get("ps") or kv.get("puri") or "OFF"
                bat = kv.get("bat") or "0"

                logger.info("GENESIS %s -> AQI_IN=%s AQI_OUT=%s LUX=%s PS=%s BAT=%s",
                            client_id, aqi_input, aqi_output, lux, ps, bat)

                try:
                    GENESIS_EXECUTOR.submit(_update_genesis_node_db_safe, client_id, aqi_input, aqi_output, lux, ps,
                                            bat)
                    GENESIS_EXECUTOR.submit(_logs_genesis, client_id, aqi_input, aqi_output, lux, ps)
                except Exception:
                    logger.exception("Failed to schedule DB task for GENESIS node")

                try:
                    ALERT_EXECUTOR.submit(process_genesis_alert, client_id, aqi_input, aqi_output, lux)
                except Exception:
                    logger.exception("Failed to schedule alert task for GENESIS node")

            else:
                logger.debug("Unknown client id format: %s", client_id)

            # ACK
            ack = "•Server received: Data\n"
            try:
                self.wfile.write(ack.encode("utf-8"))
            except Exception:
                logger.debug("Failed to send ACK to %s", addr)

        except Exception as e:
            logger.exception("Handler error: %s", e)


# ---------------- Logs for analytics ----------------
def _logs_air(client_id, mq135, mq7, mq2, mq4, mq6, temp, hum):
    try:
        iPT_UA_database.log_air_data(client_id, mq135, mq7, mq2, mq4, mq6, temp, hum)
    except:
        pass


def _logs_water(client_id, tds, temp):
    try:
        iPT_UA_database.log_water_data(client_id, tds, temp)
    except:
        pass


def _logs_hepa(client_id, aqi, ps):
    try:
        iPT_UA_database.log_hepa_data(client_id, aqi, ps)
    except:
        pass


def _logs_genesis(client_id, aqi_input, aqi_output, lux, ps):
    try:
        iPT_UA_database.log_genesis_data(client_id, aqi_input, aqi_output, lux, ps)
    except:
        pass


# ---------------- DB-safe wrappers ----------------
def _update_air_node_db_safe(client_id, mq135, mq7, mq2, mq4, mq6, hum, temp):
    try:
        iPT_UA_database.update_air_node_online(client_id, mq135, mq7, mq2, mq4, mq6, hum, temp, "True", "100")
        logger.debug("DB updated AIR node %s", client_id)
    except Exception as e:
        logger.exception("DB update error for AIR node %s: %s", client_id, e)


def _update_water_node_db_safe(client_id, tds_value, water_temp):
    try:
        iPT_UA_database.update_water_node_online(client_id, tds_value, water_temp, "True", '100')
        logger.debug("DB updated WATER node %s", client_id)
    except Exception as e:
        logger.exception("DB update error for WATER node %s: %s", client_id, e)


def _update_hepa_node_db_safe(client_id, aqi, ps, bat):
    try:
        iPT_UA_database.update_hepa_node_online(client_id, aqi, ps, "True", bat)
        logger.debug("DB updated HEPA node %s", client_id)
    except Exception as e:
        logger.exception("DB update error for HEPA node %s: %s", client_id, e)


def _update_genesis_node_db_safe(client_id, aqi_input, aqi_output, lux, ps, bat):
    """Update Genesis node in database"""
    try:
        iPT_UA_database.update_genesis_node_online(client_id, aqi_input, aqi_output, lux, ps, "True", bat)
        logger.debug("DB updated GENESIS node %s", client_id)
    except Exception as e:
        logger.exception("DB update error for GENESIS node %s: %s", client_id, e)


# ---------------- Activity monitors ----------------
def activity_monitor_air(poll_interval=5):
    logger.info("Activity monitor (AIR) started, poll_interval=%s", poll_interval)
    while True:
        try:
            all_nodes = iPT_UA_database.get_all_names_air_nodes_online()
            now = datetime.datetime.now()

            with LAST_SEEN_LOCK:
                seen_copy = dict(LAST_SEEN)

            for node_row in all_nodes:
                node_key = _normalize_node_key(node_row)
                last = seen_copy.get(node_key)

                if last is None:
                    is_online = False
                else:
                    if isinstance(last, str):
                        try:
                            last_dt = datetime.datetime.fromisoformat(last)
                        except Exception:
                            last_dt = None
                    else:
                        last_dt = last

                    if last_dt is None:
                        is_online = False
                    else:
                        diff = (now - last_dt).total_seconds()
                        is_online = diff <= OFFLINE_TIMEOUT

                with LAST_KNOWN_STATUS_LOCK:
                    prev = LAST_KNOWN_STATUS_AIR.get(node_key)
                    if prev == is_online:
                        continue
                    LAST_KNOWN_STATUS_AIR[node_key] = is_online

                AIR_EXECUTOR.submit(_update_air_activity_safe, node_key, is_online)

            time.sleep(poll_interval)
        except Exception as e:
            logger.exception("Activity monitor (AIR) error: %s", e)
            time.sleep(5)


def _update_air_activity_safe(node_k, online_flag):
    try:
        iPT_UA_database.update_air_node_activity_online(node_k, "True" if online_flag else "False")
        logger.info("[ACTIVITY-AIR] DB updated node=%s online=%s", node_k, online_flag)
    except Exception as e:
        with LAST_KNOWN_STATUS_LOCK:
            LAST_KNOWN_STATUS_AIR.pop(node_k, None)
        logger.exception("ACTIVITY DB update error for AIR %s: %s", node_k, e)


def activity_monitor_water(poll_interval=5):
    logger.info("Activity monitor (WATER) started, poll_interval=%s", poll_interval)
    while True:
        try:
            all_nodes = iPT_UA_database.get_all_names_water_nodes_online()
            now = datetime.datetime.now()

            with LAST_SEEN_WATER_LOCK:
                seen_copy = dict(LAST_SEEN_WATER)

            for node_row in all_nodes:
                node_key = _normalize_node_key(node_row)
                last = seen_copy.get(node_key)

                if last is None:
                    is_online = False
                else:
                    if isinstance(last, str):
                        try:
                            last_dt = datetime.datetime.fromisoformat(last)
                        except Exception:
                            last_dt = None
                    else:
                        last_dt = last

                    if last_dt is None:
                        is_online = False
                    else:
                        diff = (now - last_dt).total_seconds()
                        is_online = diff <= OFFLINE_TIMEOUT

                with LAST_KNOWN_STATUS_LOCK:
                    prev = LAST_KNOWN_STATUS_WATER.get(node_key)
                    if prev == is_online:
                        continue
                    LAST_KNOWN_STATUS_WATER[node_key] = is_online

                WATER_EXECUTOR.submit(_update_water_activity_safe, node_key, is_online)

            time.sleep(poll_interval)
        except Exception as e:
            logger.exception("Activity monitor (WATER) error: %s", e)
            time.sleep(5)


def _update_water_activity_safe(node_k, online_flag):
    try:
        iPT_UA_database.update_water_node_activity_online(node_k, "True" if online_flag else "False")
        logger.info("[ACTIVITY-WATER] DB updated node=%s online=%s", node_k, online_flag)
    except Exception as e:
        with LAST_KNOWN_STATUS_LOCK:
            LAST_KNOWN_STATUS_WATER.pop(node_k, None)
        logger.exception("ACTIVITY-WATER DB update error for %s: %s", node_k, e)


def activity_monitor_hepa(poll_interval=5):
    logger.info("Activity monitor (HEPA) started, poll_interval=%s", poll_interval)
    while True:
        try:
            all_nodes = iPT_UA_database.get_all_names_hepa_nodes_online()
            now = datetime.datetime.now()

            with LAST_SEEN_HEPA_LOCK:
                seen_copy = dict(LAST_SEEN_HEPA)

            for node_row in all_nodes:
                node_key = _normalize_node_key(node_row)
                last = seen_copy.get(node_key)

                if last is None:
                    is_online = False
                else:
                    diff = (now - last).total_seconds()
                    is_online = diff <= OFFLINE_TIMEOUT

                with LAST_KNOWN_STATUS_LOCK:
                    prev = LAST_KNOWN_STATUS_HEPA.get(node_key)
                    if prev == is_online:
                        continue
                    LAST_KNOWN_STATUS_HEPA[node_key] = is_online

                HEPA_EXECUTOR.submit(_update_hepa_activity_safe, node_key, is_online)

            time.sleep(poll_interval)
        except Exception as e:
            logger.exception("Activity monitor (HEPA) error: %s", e)
            time.sleep(5)


def _update_hepa_activity_safe(node_k, online_flag):
    try:
        iPT_UA_database.update_hepa_node_activity_online(node_k, "True" if online_flag else "False")
        logger.info("[ACTIVITY-HEPA] DB updated node=%s online=%s", node_k, online_flag)
    except Exception as e:
        with LAST_KNOWN_STATUS_LOCK:
            LAST_KNOWN_STATUS_HEPA.pop(node_k, None)
        logger.exception("ACTIVITY-HEPA DB update error for %s: %s", node_k, e)


def activity_monitor_genesis(poll_interval=5):
    """Activity monitor for Genesis nodes"""
    logger.info("Activity monitor (GENESIS) started, poll_interval=%s", poll_interval)
    while True:
        try:
            all_nodes = iPT_UA_database.get_all_names_genesis_nodes_online()
            now = datetime.datetime.now()

            with LAST_SEEN_GENESIS_LOCK:
                seen_copy = dict(LAST_SEEN_GENESIS)

            for node_row in all_nodes:
                node_key = _normalize_node_key(node_row)
                last = seen_copy.get(node_key)

                if last is None:
                    is_online = False
                else:
                    diff = (now - last).total_seconds()
                    is_online = diff <= OFFLINE_TIMEOUT

                with LAST_KNOWN_STATUS_LOCK:
                    prev = LAST_KNOWN_STATUS_GENESIS.get(node_key)
                    if prev == is_online:
                        continue
                    LAST_KNOWN_STATUS_GENESIS[node_key] = is_online

                GENESIS_EXECUTOR.submit(_update_genesis_activity_safe, node_key, is_online)

            time.sleep(poll_interval)
        except Exception as e:
            logger.exception("Activity monitor (GENESIS) error: %s", e)
            time.sleep(5)


def _update_genesis_activity_safe(node_k, online_flag):
    try:
        iPT_UA_database.update_genesis_node_activity_online(node_k, "True" if online_flag else "False")
        logger.info("[ACTIVITY-GENESIS] DB updated node=%s online=%s", node_k, online_flag)
    except Exception as e:
        with LAST_KNOWN_STATUS_LOCK:
            LAST_KNOWN_STATUS_GENESIS.pop(node_k, None)
        logger.exception("ACTIVITY-GENESIS DB update error for %s: %s", node_k, e)


# ---------------- Hourly History Recorder ----------------
def hourly_history_recorder():
    """Record node history every hour"""
    logger.info("Hourly history recorder started")

    while True:
        try:
            # Wait for 1 hour
            time.sleep(3600)  # 3600 seconds = 1 hour

            logger.info("Recording hourly history snapshot...")

            # Record AIR nodes
            try:
                HISTORY_EXECUTOR.submit(iPT_UA_database.record_air_nodes_history)
            except Exception as e:
                logger.exception("Failed to record AIR history: %s", e)

            # Record WATER nodes
            try:
                HISTORY_EXECUTOR.submit(iPT_UA_database.record_water_nodes_history)
            except Exception as e:
                logger.exception("Failed to record WATER history: %s", e)

            # Record HEPA nodes
            try:
                HISTORY_EXECUTOR.submit(iPT_UA_database.record_hepa_nodes_history)
            except Exception as e:
                logger.exception("Failed to record HEPA history: %s", e)

            # Record GENESIS nodes
            try:
                HISTORY_EXECUTOR.submit(iPT_UA_database.record_genesis_nodes_history)
            except Exception as e:
                logger.exception("Failed to record GENESIS history: %s", e)

            logger.info("Hourly history recording completed")

        except Exception as e:
            logger.exception("Hourly history recorder error: %s", e)
            time.sleep(60)  # Wait 1 minute before retry


# ---------------- main and graceful shutdown ----------------
def serve_forever():
    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True

    # Start activity monitors
    t_air = threading.Thread(target=activity_monitor_air, name="Activity-AIR", daemon=True)
    t_air.start()

    t_water = threading.Thread(target=activity_monitor_water, name="Activity-WATER", daemon=True)
    t_water.start()

    t_hepa = threading.Thread(target=activity_monitor_hepa, name="Activity-HEPA", daemon=True)
    t_hepa.start()

    t_genesis = threading.Thread(target=activity_monitor_genesis, name="Activity-GENESIS", daemon=True)
    t_genesis.start()

    # Start hourly history recorder
    t_history = threading.Thread(target=hourly_history_recorder, name="History-Recorder", daemon=True)
    t_history.start()

    server = ThreadedTCPServer((HOST, PORT), Handler)
    sa = server.socket.getsockname()
    logger.info("Server listening on %s:%s", sa[0], sa[1])

    shutdown_event = threading.Event()

    def _signal_handler(signum, frame):
        logger.info("Signal %s received, shutting down...", signum)
        shutdown_event.set()
        try:
            server.shutdown()
        except Exception:
            pass

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        server.serve_forever()
    except Exception as e:
        logger.exception("Server exception: %s", e)
    finally:
        logger.info("Server stopping: shutting down executors and server socket")
        try:
            server.server_close()
        except Exception:
            pass

        for ex in (AIR_EXECUTOR, WATER_EXECUTOR, HEPA_EXECUTOR, GENESIS_EXECUTOR,
                   ALERT_EXECUTOR, ACTIVITY_EXECUTOR, HISTORY_EXECUTOR):
            try:
                ex.shutdown(wait=True, timeout=5)
            except TypeError:
                ex.shutdown(wait=True)
            except Exception:
                logger.exception("Error shutting down executor %s", ex)


if __name__ == "__main__":
    serve_forever()
