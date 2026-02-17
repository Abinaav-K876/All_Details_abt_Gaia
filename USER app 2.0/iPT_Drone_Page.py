from __future__ import annotations
from customtkinter import (CTkFrame, CTkLabel, CTkButton, CTkScrollableFrame, CTkTextbox, CTkSwitch)
from PIL import Image, ImageTk
from ultralytics import YOLO
import cv2
import threading
import time
import smtplib
from email.message import EmailMessage
import datetime
from typing import Optional, Dict, Any, List
import random
import numpy as np
from tkinter import filedialog, messagebox
import json, os
from add_drone_attachment import AddDroneAttachmentNodeTopLevel
from themes import pink, lavender_og, blue, green, orange

AVAILABLE_THEMES = {"Pink": pink, "Lavender": lavender_og, "Blue": blue, "Green": green, "Orange": orange}
CURRENT_THEME = None

def load_selected_theme():
    global CURRENT_THEME
    if os.path.exists("gaia_settings.json"):
        with open("gaia_settings.json", "r") as f:
            name = json.load(f).get("theme", 'Lavender')
            CURRENT_THEME = name
            return AVAILABLE_THEMES.get(name, 'Lavender')
    else:
        return lavender_og

THEME = load_selected_theme()

COLORS = {
    # Core backgrounds & accents
    "bg": THEME["LAVENDER_MIST"],
    "card_bg": THEME["PANEL"],
    "accent": THEME["VELVET_ORCHID"],
    "accent_hover": THEME["DARK_AMETHYST"],
    "accent_light": THEME["PANEL_ALT"],

    # Text
    "text_primary": THEME["PANEL_TEXT"],
    "text_secondary": THEME["PANEL_SUBTEXT"],
    "text_muted": THEME["MUTED"],
    "text_dark": THEME["TEXT_DARK"],

    # Borders / frames
    "border": THEME["PANEL_EDGE"],
    "frame": THEME["FRAME_BG"],

    # Status colors
    "success": THEME["SUCCESS"],
    "danger": THEME["DANGER"],
    "danger_hover": THEME["DANGER_HOVER"],
    "warning": THEME["WARN"],
    "warn_hover": THEME["WARN_HOVER"],

    # Status reminders
    "status_online": THEME["STATUS_ONLINE"],
    "status_idle": THEME["WARN"],
    "status_offline": THEME["STATUS_OFFLINE"],

    # Panels / layout
    "panel": THEME["PANEL"],
    "panel_edge": THEME["PANEL_EDGE"],
    "panel_alt": THEME["PANEL_ALT"],
    "hover": THEME["CLEAR_HOVER"],

    # Sidebar / root
    "sidebar": THEME["SIDEBAR_BG"],
    "sidebar_active": THEME["SIDEBAR_ACTIVE"],
    "root_bg_dark": THEME["ROOT_BG_DARK"],
    "divider": THEME["DIVIDER"],

    # UI utilities
    "info": THEME["VELVET_ORCHID"],
    "select": THEME["SELECT"],
    "progress_bg": THEME["PROGRESS_BG"],
    "placeholder": THEME["PLACEHOLDER"],
    "login_btn_bg": THEME["LOGIN_BTN_BG"],
    "login_btn_hover": THEME["LOGIN_BTN_HOVER"],

    # Profile
    "profile_bg": THEME["PROFILE_BG"],

    # Network / system
    "no_internet_bg": THEME["NO_INTERNET_BG"],
}

# ===================== CONFIG =====================
MODEL_PATH = "best.pt"
CLASS_MAP = {
    0: ("Dustbin overflow", "DUSTBIN_OVERFLOW"),
    1: ("Water log", "WATER_LOG"),
    2: ("Traffic jam", "TRAFFIC_JAM"),
}
CONF_THRESHOLD = 0.30
ALERT_CONF_THRESHOLD = 0.70
STABILITY_FRAMES = 3
CLASS_MIN_CONF = {0: 0.30, 1: 0.30, 2: 0.30}
CLASS_MIN_AREA_FRAC = {0: 0.015, 1: 0.020, 2: 0.010}

FRAME_SKIP = 1
DISPLAY_SIZE = (900, 600)

EMAIL_SENDER = "gaiasentinel@gmail.com"
EMAIL_PASSWORD = "gkaebatusfvipaec"
EMAIL_FROM_NAME = "Gaia Sentinel Alerts"
ALERT_RECIPIENT = "vain.blackmail@gmail.com"
ALERT_COOLDOWN = 60

DRONES: List[Dict[str, Any]] = [
    {"id": "GS-DS-ALPHA",
    "role": "Air Quality",
    "status": "ONLINE",
    "battery": 92,
    "link": 100,
    "altitude": 0,
    "speed": 0,
    "last_mission": "Campus Sweep A1",
    "last_seen": "Just now",
    "location": "Main Campus Roof",} ]

class GaiaSentinelDroneCenter(CTkFrame):
    """Drone Operation Center with selectable log file and action/error message boxes."""

    def __init__(self, master):
        super().__init__(master, fg_color=COLORS["bg"])
        self.master = master
        self.pack(fill="both", expand=True)

        self._init_variables()
        self._build_ui()
        self._init_camera_and_model()

    # ===================== INIT =====================

    def _init_variables(self):
        self.selected_drone_id: Optional[str] = None
        self._drone_cards: Dict[str, CTkFrame] = {}
        self._detail_widgets: Dict[str, Any] = {}
        self.cap = None
        self.yolo: Optional[YOLO] = None
        self.running = True
        self._ai_enabled = False
        self._frame_count = 0
        self._process_count = 0
        self._last_time = time.time()
        self._stability: Dict[tuple, int] = {}
        self._last_alert_times: Dict[str, float] = {}
        self._camera_image = None
        self._is_closing = False
        self._last_processed_frame = None
        self._ai_switch: Optional[CTkSwitch] = None
        self._stream_status_label: Optional[CTkLabel] = None
        self._detection_status_label: Optional[CTkLabel] = None
        self._active_detections_label: Optional[CTkLabel] = None
        self._pause_btn: Optional[CTkButton] = None
        self.status_log: Optional[CTkTextbox] = None
        self._log_file_path: Optional[str] = None  # user‑chosen log file

    def _build_ui(self):
        main = CTkFrame(self, fg_color=COLORS["bg"])
        main.pack(fill="both", expand=True, padx=0, pady=0)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(1, weight=1)

        self._build_top_bar(main)
        self._build_left_sidebar(main)
        self._build_center_feed(main)
        self._build_right_panel(main)

    # ===================== TOP BAR =====================

    def _build_top_bar(self, parent: CTkFrame):
        top = CTkFrame(parent, fg_color=COLORS["card_bg"], height=60, corner_radius=12)
        top.grid(row=0, column=0, columnspan=3, sticky="ew", padx=0, pady=(0, 12))
        top.grid_propagate(False)
        top.grid_columnconfigure(1, weight=1)

        title_frame = CTkFrame(top, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=15)

        CTkLabel(title_frame, text="🛸 Drone Attachment Operation Center", font=("Segoe UI", 24, "bold"), text_color=COLORS["accent"]).pack(anchor="center")

        stats_frame = CTkFrame(top, fg_color="transparent")
        stats_frame.grid(row=0, column=2, sticky="e", padx=20)

        stats = [
            ("FLEET", len(DRONES), COLORS["text_primary"]),
            ("ONLINE", f"{sum(1 for d in DRONES if d['status'] == 'ONLINE')}", COLORS["success"]),
            ("WARNING", sum(1 for d in DRONES if d["status"] == "WARNING"), COLORS["warning"]),
            ("OFFLINE", sum(1 for d in DRONES if d["status"] == "OFFLINE"), COLORS["danger"])
        ]

        for label, value, color in stats:
            frame = CTkFrame(stats_frame, fg_color="transparent")
            frame.pack(side="left", padx=8)
            CTkLabel(frame, text=label, font=("Segoe UI", 9), text_color=COLORS["text_muted"]).pack()
            CTkLabel(frame, text=str(value), font=("Segoe UI", 16, "bold"), text_color=color).pack()

    # ===================== LEFT SIDEBAR =====================

    def _build_left_sidebar(self, parent: CTkFrame):
        left = CTkFrame(parent, fg_color=COLORS["sidebar"], width=320, corner_radius=12)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        left.grid_propagate(False)
        left.grid_rowconfigure(2, weight=1)

        header = CTkFrame(left, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=(10, 0))
        header.grid_propagate(False)

        CTkLabel(header, text="Fleet Management", font=("Segoe UI", 18, "bold"), text_color=COLORS["text_primary"], anchor="w").pack(fill="x", padx=(10, 0))

        btn_frame = CTkFrame(left, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=11, pady=12)
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        CTkButton(btn_frame, text="➕ Add Drone Attachment", fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color="white", height=36,
            corner_radius=8, font=("Segoe UI", 10, "bold"), command=lambda: self._add_drone(parent)).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        CTkButton(btn_frame, text="🗑 Remove", fg_color=COLORS["danger"], hover_color="#DC2626", text_color="white",
            height=36, corner_radius=8, font=("Segoe UI", 10, "bold"), command=self._remove_selected_drone).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.fleet_list = CTkScrollableFrame(left, fg_color="transparent", corner_radius=0)
        self.fleet_list.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        self._refresh_fleet_list()

    # ===================== CENTER FEED =====================

    def _build_center_feed(self, parent: CTkFrame):
        center = CTkFrame(parent, fg_color="transparent")
        center.grid(row=1, column=1, sticky="nsew", padx=0)
        center.grid_rowconfigure(1, weight=1)
        center.grid_columnconfigure(0, weight=1)

        feed_header = CTkFrame(center, fg_color=COLORS["card_bg"], height=60, corner_radius=12)
        feed_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        feed_header.grid_propagate(False)
        feed_header.grid_columnconfigure(1, weight=1)

        header_left = CTkFrame(feed_header, fg_color="transparent")
        header_left.grid(row=0, column=0, sticky="w", padx=20)

        CTkLabel(header_left, text="Camera Feed", font=("Segoe UI", 16, "bold"), text_color=COLORS["text_primary"]).pack(anchor="w")

        status_row = CTkFrame(header_left, fg_color="transparent")
        status_row.pack(anchor="w", pady=(2, 0))

        self._stream_status_label = CTkLabel(status_row, text="● LIVE", font=("Segoe UI", 10, "bold"), text_color=COLORS["success"])
        self._stream_status_label.pack(side="left", padx=(0, 12))

        self._detection_status_label = CTkLabel(status_row, text="🔍 Detection: OFF", font=("Segoe UI", 10, "bold"), text_color=COLORS["text_muted"])
        self._detection_status_label.pack(side="left", padx=(0, 12))

        self._active_detections_label = CTkLabel(status_row, text="⚠️ Alerts: 0", font=("Segoe UI", 10, "bold"), text_color=COLORS["text_muted"])
        self._active_detections_label.pack(side="left")

        self._ai_switch = CTkSwitch(feed_header, text="AI Detection",  font=("Segoe UI", 12, "bold"), command=self._toggle_ai_detection,
            fg_color=COLORS["border"], progress_color=COLORS["success"], button_color=COLORS["card_bg"], button_hover_color=COLORS["hover"])
        self._ai_switch.grid(row=0, column=2, sticky="e", padx=20)
        self._ai_switch.configure(state="disabled", text_color=COLORS["text_muted"])

        feed_container = CTkFrame(center, fg_color=COLORS["text_primary"], corner_radius=12)
        feed_container.grid(row=1, column=0, sticky="nsew")
        feed_container.grid_rowconfigure(0, weight=1)
        feed_container.grid_columnconfigure(0, weight=1)

        self.camera_label = CTkLabel(feed_container, text="📹\n\nCamera Initializing...\n\nSelect a drone Attachment from fleet to begin monitoring",
            font=("Segoe UI", 14), text_color=COLORS["text_muted"], justify="center", fg_color=COLORS["card_bg"])
        self.camera_label.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        control_panel = CTkFrame(center, fg_color=COLORS["card_bg"], height=90, corner_radius=12)
        control_panel.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        control_panel.grid_propagate(False)
        control_panel.grid_columnconfigure((0, 1, 2, 3), weight=1)

        CTkButton(control_panel, text="📊 View Telemetry", fg_color=COLORS["info"],
            hover_color=COLORS["accent_hover"], text_color="white", height=45, corner_radius=8,
            font=("Segoe UI", 12, "bold"), command=self._view_telemetry).grid(row=0, column=0, padx=8, pady=20, sticky="ew")

        CTkButton(control_panel, text="📸 Capture Frame", fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"], text_color="white", height=45,
            corner_radius=8, font=("Segoe UI", 12, "bold"), command=self._capture_frame).grid(row=0, column=1, padx=8, pady=20, sticky="ew")

        CTkButton(control_panel, text="📁 Export Log", fg_color=COLORS["warning"],
            hover_color="#D97706", text_color="white", height=45, corner_radius=8,
            font=("Segoe UI", 12, "bold"), command=self._export_log).grid(row=0, column=2, padx=8, pady=20, sticky="ew")

        self._pause_btn = CTkButton(control_panel, text="⏸ Pause Stream", fg_color=COLORS["border"],
            hover_color=COLORS["text_muted"], text_color=COLORS["text_primary"],
            height=45, corner_radius=8, font=("Segoe UI", 12, "bold"),
            command=self._toggle_stream)
        self._pause_btn.grid(row=0, column=3, padx=8, pady=20, sticky="ew")

    # ===================== RIGHT PANEL =====================

    def _build_right_panel(self, parent: CTkFrame):
        right = CTkFrame(parent, fg_color="transparent", width=350, corner_radius=12)
        right.grid(row=1, column=2, sticky="nsew", padx=(12, 0))
        right.grid_propagate(False)
        right.grid_rowconfigure(2, weight=1)

        self._build_drone_info_card(right)
        self._build_status_log(right)

    def _build_drone_info_card(self, parent: CTkFrame):
        parent.grid_columnconfigure(0, weight=1)
        info_card = CTkFrame(parent, fg_color=COLORS["card_bg"], corner_radius=12)
        info_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        CTkLabel(info_card, text="Drone Attachment Details", font=("Segoe UI", 14, "bold"), text_color=COLORS["text_primary"]).pack(anchor="center", padx=12, pady=(2, 0))

        header = CTkFrame(info_card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=5)
        header.grid_columnconfigure(0, weight=1)

        self._detail_widgets["drone_name"] = CTkLabel(header, text="No Drone Attachment Selected", font=("Segoe UI", 16, "bold"), text_color=COLORS["text_primary"], anchor="w")
        self._detail_widgets["drone_name"].grid(row=0, column=0, sticky="w")

        self._detail_widgets["status_badge"] = CTkLabel(header, text="IDLE", font=("Segoe UI", 10, "bold"), text_color="white", fg_color=COLORS["status_idle"], corner_radius=12, padx=12, pady=4)
        self._detail_widgets["status_badge"].grid(row=0, column=1, padx=(10, 0), sticky="e")

        tele_grid = CTkFrame(info_card, fg_color="transparent")
        tele_grid.pack(fill="x", padx=12, pady=(2, 8))
        for i in range(2):
            tele_grid.grid_columnconfigure(i, weight=1, uniform="tele")

        metrics = [
            ("Altitude", "altitude", "0 m"),
            ("Speed", "speed", "0 m/s"),
            ("Battery", "battery", "0%"),
            ("Link", "link", "0%"),
        ]

        for idx, (label, key, default) in enumerate(metrics):
            row, col = divmod(idx, 2)
            box = CTkFrame(tele_grid, fg_color=COLORS["accent_light"], corner_radius=10)
            box.grid(row=row, column=col, padx=3, pady=3, sticky="ew")

            CTkLabel(box, text=label, font=("Segoe UI", 12), text_color=COLORS["text_secondary"]).pack(anchor="w", padx=12, pady=(5, 0))

            self._detail_widgets[key] = CTkLabel(box, text=default, font=("Segoe UI", 13, "bold"), text_color=COLORS["accent"])
            self._detail_widgets[key].pack(anchor="w", padx=12, pady=(0, 5))

        location_frame = CTkFrame(info_card, fg_color=COLORS["hover"], corner_radius=8)
        location_frame.pack(fill="x", padx=20, pady=(0, 10))

        CTkLabel(location_frame, text="📍 Location", font=("Segoe UI", 10), text_color=COLORS["text_secondary"]).pack(anchor="w", padx=12, pady=(6, 0))

        self._detail_widgets["location"] = CTkLabel(location_frame, text="Not assigned", font=("Segoe UI", 12, "bold"), text_color=COLORS["text_primary"])
        self._detail_widgets["location"].pack(anchor="w", padx=12, pady=(0, 8))

    def _build_status_log(self, parent: CTkFrame):
        parent.grid_columnconfigure(0, weight=1)
        log_card = CTkFrame(parent, fg_color=COLORS["card_bg"], corner_radius=12)
        log_card.grid(row=2, column=0, sticky="nsew")
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        log_header = CTkFrame(log_card, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        log_header.grid_columnconfigure(0, weight=1)

        CTkLabel(
            log_header, text="System Log", font=("Segoe UI", 14, "bold"),
            text_color=COLORS["text_primary"]
        ).grid(row=0, column=0, sticky="w")

        CTkButton(
            log_header, text="Clear", fg_color=COLORS["border"],
            hover_color=COLORS["hover"], text_color=COLORS["text_primary"],
            width=60, height=28, corner_radius=6, font=("Segoe UI", 10, "bold"),
            command=self._clear_log
        ).grid(row=0, column=1, sticky="e")

        self.status_log = CTkTextbox(
            log_card, fg_color=COLORS["hover"], text_color=COLORS["text_primary"],
            border_width=0, corner_radius=8, font=("Consolas", 10)
        )
        self.status_log.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self.status_log.insert("end", "[INFO] System initialized successfully\n")
        self.status_log.configure(state="disabled")

    # ===================== LOGGING =====================

    def _append_to_log_file(self, line: str):
        """Write log line to user‑chosen file if set."""
        if not self._log_file_path:
            return
        try:
            with open(self._log_file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            # Show error once but avoid infinite recursion
            messagebox.showerror("Log file error", f"Could not write to log file:\n{e}")  # [web:52]

    def _log_status(self, text: str):
        """Log to UI + optional file with safety check."""
        if not self.winfo_exists() or not self.status_log.winfo_exists():
            return

        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {text}"

        try:
            self.status_log.configure(state="normal")
            self.status_log.insert("end", line + "\n")
            self.status_log.see("end")
            self.status_log.configure(state="disabled")
        except Exception:
            pass

        self._append_to_log_file(line)

    # ===================== FLEET =====================

    def _refresh_fleet_list(self):
        for widget in self.fleet_list.winfo_children():
            widget.destroy()
        self._drone_cards.clear()
        for drone in DRONES:
            self._create_fleet_card(drone)

    def _create_fleet_card(self, drone: Dict[str, Any]):
        card = CTkFrame(
            self.fleet_list, fg_color=COLORS["card_bg"], corner_radius=10,
            border_width=2, border_color=COLORS["border"]
        )
        card.pack(fill="x", pady=6, padx=4)
        self._drone_cards[drone["id"]] = card
        card.bind("<Button-1>", lambda _: self._select_drone(drone["id"]))

        header = CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 6))
        header.grid_columnconfigure(0, weight=1)

        name_label = CTkLabel(
            header, text=drone["id"], font=("Segoe UI", 13, "bold"),
            text_color=COLORS["text_primary"], anchor="w"
        )
        name_label.grid(row=0, column=0, sticky="w")
        name_label.bind("<Button-1>", lambda _: self._select_drone(drone["id"]))

        status_color = self._get_status_color(drone["status"])
        status_badge = CTkLabel(
            header, text=f"● {drone['status']}", font=("Segoe UI", 10, "bold"),
            text_color=status_color
        )
        status_badge.grid(row=0, column=1, sticky="e")
        status_badge.bind("<Button-1>", lambda _: self._select_drone(drone["id"]))

        role_label = CTkLabel(
            card, text=drone["role"], font=("Segoe UI", 10),
            text_color=COLORS["text_secondary"], anchor="w"
        )
        role_label.pack(anchor="w", padx=14, pady=(0, 8))
        role_label.bind("<Button-1>", lambda _: self._select_drone(drone["id"]))

        stats = CTkFrame(card, fg_color="transparent")
        stats.pack(fill="x", padx=14, pady=(0, 10))

        stat_text = f"🔋 {drone['battery']}%  •  📡 {drone['link']}%  •  📍 {drone['location']}"
        stat_label = CTkLabel(stats, text=stat_text, font=("Segoe UI", 9), text_color=COLORS["text_muted"])
        stat_label.pack(anchor="w")
        stat_label.bind("<Button-1>", lambda _: self._select_drone(drone["id"]))

    def _get_status_color(self, status: str) -> str:
        if status == "ONLINE":
            return COLORS["status_online"]
        elif status == "WARNING":
            return COLORS["status_idle"]
        return COLORS["status_offline"]

    def _add_drone(self, parent):
        try:
            def do_after_success(new_id):
                DRONES.append({
                    "id": new_id,
                    "role": "New Drone",
                    "status": "Idle",
                    "battery": random.randint(50, 100),
                    "link": random.randint(60, 100),
                    "altitude": 0,
                    "speed": 0,
                    "last_mission": "Not assigned",
                    "last_seen": "Just now",
                    "location": "Base Station",
                })

                self._refresh_fleet_list()
                self._log_status(f"✅ Added new drone Attachment: {new_id}")

            AddDroneAttachmentNodeTopLevel(parent, do_after_success)

        except Exception as e:
            self._log_status(f"❌ Add drone Attachment error: {e}")
            messagebox.showerror("Error", f"Could not add drone Attachment:\n{e}")

    def _remove_selected_drone(self):
        if not self.selected_drone_id:
            self._log_status("⚠️ No drone Attachment selected for removal")
            messagebox.showwarning("No selection", "Select a drone Attachment to remove.")
            return

        try:
            removed_id = self.selected_drone_id
            DRONES[:] = [d for d in DRONES if d["id"] != self.selected_drone_id]
            self.selected_drone_id = None
            self._refresh_fleet_list()
            self._reset_details()
            if self._ai_switch is not None:
                self._ai_switch.deselect()
                self._ai_switch.configure(state="disabled", text_color=COLORS["text_muted"])
            self._ai_enabled = False
            self._log_status(f"🗑 Removed drone Attachment: {removed_id}")
            messagebox.showinfo("Drone Attachment removed", f"Drone Attachment {removed_id} removed.")
        except Exception as e:
            self._log_status(f"❌ Remove drone Attachment error: {e}")
            messagebox.showerror("Error", f"Could not remove drone Attachment:\n{e}")

    def _select_drone(self, drone_id: str):
        for did, card in self._drone_cards.items():
            card.configure(border_color=COLORS["border"], border_width=2)

        self.selected_drone_id = drone_id
        if drone_id in self._drone_cards:
            self._drone_cards[drone_id].configure(border_color=COLORS["accent"], border_width=3)

        drone = next((d for d in DRONES if d["id"] == drone_id), None)
        if drone:
            self._update_details(drone)
            self._log_status(f"📡 Selected drone Attachment: {drone_id}")
            if self._ai_switch is not None:
                self._ai_switch.configure(state="normal", text_color=COLORS["text_primary"])

    # ===================== DETAIL =====================

    def _reset_details(self):
        self._detail_widgets["drone_name"].configure(text="No Drone Attachment Selected")
        self._detail_widgets["status_badge"].configure(text="IDLE", fg_color=COLORS["status_idle"])
        self._detail_widgets["altitude"].configure(text="0 m")
        self._detail_widgets["speed"].configure(text="0 m/s")
        self._detail_widgets["battery"].configure(text="0%")
        self._detail_widgets["link"].configure(text="0%")
        self._detail_widgets["location"].configure(text="Not assigned")
        self._detection_status_label.configure(text="🔍 Detection: OFF", text_color=COLORS["text_muted"])
        self._active_detections_label.configure(text="⚠️ Alerts: 0", text_color=COLORS["text_muted"])

    def _update_details(self, drone: Dict[str, Any]):
        self._detail_widgets["drone_name"].configure(text=drone["id"])
        status_color = self._get_status_color(drone["status"])
        self._detail_widgets["status_badge"].configure(text=drone["status"].upper(), fg_color=status_color)
        self._detail_widgets["altitude"].configure(text=f"{drone['altitude']} m")
        self._detail_widgets["speed"].configure(text=f"{drone['speed']} m/s")
        self._detail_widgets["battery"].configure(text=f"{drone['battery']}%")
        self._detail_widgets["link"].configure(text=f"{drone['link']}%")
        self._detail_widgets["location"].configure(text=drone["location"])

    # ===================== CONTROL ACTIONS =====================

    def _view_telemetry(self):
        try:
            if not self.selected_drone_id:
                self._log_status("⚠️ Select a  Attachment to view telemetry")
                messagebox.showwarning("No selection", "Select a drone Attachment to view telemetry.")
                return
            drone = next((d for d in DRONES if d["id"] == self.selected_drone_id), None)
            if drone:
                self._log_status(f"📊 Telemetry for {drone['id']}:")
                self._log_status(f"   Altitude: {drone['altitude']}m | Speed: {drone['speed']}m/s")
                self._log_status(f"   Battery: {drone['battery']}% | Link: {drone['link']}%")
                self._log_status(f"   Location: {drone['location']} | Status: {drone['status']}")
                messagebox.showinfo("Telemetry", f"Telemetry displayed for {drone['id']}.")
        except Exception as e:
            self._log_status(f"❌ Telemetry error: {e}")
            messagebox.showerror("Error", f"Could not show telemetry:\n{e}")

    def _capture_frame(self):
        try:
            if not self.selected_drone_id:
                self._log_status("⚠️ Select a Drone Attachment to capture frame")
                messagebox.showwarning("No selection", "Select a Attachment to capture frame.")
                return
            if self.cap is None or not self.cap.isOpened():
                self._log_status("❌ Camera not available")
                messagebox.showerror("Camera error", "Camera not available.")
                return
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{self.selected_drone_id}_{timestamp}.jpg"
            ret, frame = self.cap.read()
            if ret:
                cv2.imwrite(filename, frame)
                self._log_status(f"📸 Frame captured: {filename}")
                messagebox.showinfo("Capture complete", f"Frame saved as:\n{filename}")
            else:
                raise RuntimeError("Failed to read frame from camera")
        except Exception as e:
            self._log_status(f"❌ Capture error: {e}")
            messagebox.showerror("Error", f"Could not capture frame:\n{e}")

    def _export_log(self):
        """Ask user where to store log and save current contents there."""
        try:
            file_path = filedialog.asksaveasfilename(
                parent=self,
                title="Save log as...",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )  # [web:36][web:40]
            if not file_path:
                self._log_status("ℹ️ Log export cancelled by user")
                return

            self._log_file_path = file_path  # remember for future appends
            content = self.status_log.get("1.0", "end-1c")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._log_status(f"📁 Log exported: {file_path}")
            messagebox.showinfo("Log saved", f"Log saved to:\n{file_path}")
        except Exception as e:
            self._log_status(f"❌ Export error: {e}")
            messagebox.showerror("Error", f"Could not export log:\n{e}")

    def _clear_log(self):
        try:
            self.status_log.configure(state="normal")
            self.status_log.delete("1.0", "end")
            self.status_log.insert("end", "[INFO] Log cleared\n")
            self.status_log.configure(state="disabled")
            self._append_to_log_file("----- LOG CLEARED -----")
            messagebox.showinfo("Log cleared", "Log has been cleared.")
        except Exception as e:
            self._log_status(f"❌ Clear log error: {e}")
            messagebox.showerror("Error", f"Could not clear log:\n{e}")

    def _toggle_stream(self):
        try:
            self.running = not self.running
            if self.running:
                self._pause_btn.configure(text="⏸ Pause Stream")
                self._stream_status_label.configure(text="● LIVE", text_color=COLORS["success"])
                self._log_status("▶️ Stream resumed")
                messagebox.showinfo("Stream", "Camera stream resumed.")
            else:
                self._pause_btn.configure(text="▶️ Resume Stream")
                self._stream_status_label.configure(text="⏸ PAUSED", text_color=COLORS["warning"])
                self._log_status("⏸ Stream paused")
                messagebox.showinfo("Stream", "Camera stream paused.")
        except Exception as e:
            self._log_status(f"❌ Stream toggle error: {e}")
            messagebox.showerror("Error", f"Could not toggle stream:\n{e}")

    def _require_selection(self) -> Optional[Dict[str, Any]]:
        if not self.selected_drone_id:
            self._log_status("⚠️ No drone Attachment selected")
            messagebox.showwarning("No selection", "Select a drone Attachment first.")
            return None
        return next((d for d in DRONES if d["id"] == self.selected_drone_id), None)

    def _toggle_ai_detection(self):
        if not self.selected_drone_id:
            self._log_status("⚠️ Select a drone Attachment to enable AI detection")
            if self._ai_switch is not None:
                self._ai_switch.deselect()
            messagebox.showwarning("No selection", "Select a drone Attachment to use AI detection.")
            return

        self._ai_enabled = bool(self._ai_switch.get())
        if self._ai_enabled:
            self._detection_status_label.configure(
                text="🔍 Detection: ON", text_color=COLORS["success"]
            )
            self._log_status(f"🎯 AI detection enabled for {self.selected_drone_id}")
            messagebox.showinfo("AI Detection", "AI detection enabled.")
        else:
            self._detection_status_label.configure(
                text="🔍 Detection: OFF", text_color=COLORS["text_muted"]
            )
            self._active_detections_label.configure(text="⚠️ Alerts: 0", text_color=COLORS["text_muted"])
            self._log_status("🔍 AI detection disabled")
            messagebox.showinfo("AI Detection", "AI detection disabled.")

    # ===================== CAMERA & AI =====================

    def _init_camera_and_model(self):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.cap = None
                self._log_status("❌ Camera not available")
                messagebox.showerror("Camera error", "Camera not available.")
            else:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self._log_status("✅ Camera initialized (1280x720)")
        except Exception as e:
            self.cap = None
            self._log_status(f"❌ Camera error: {e}")
            messagebox.showerror("Camera error", f"Error initializing camera:\n{e}")

        threading.Thread(target=self._load_yolo_model, daemon=True).start()
        self.after(40, self._update_frame)

    def _load_yolo_model(self):
        try:
            self.yolo = YOLO(MODEL_PATH)
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self.yolo.predict(dummy, verbose=False, conf=CONF_THRESHOLD)
            self._log_status(f"✅ AI model loaded: {MODEL_PATH}")
        except Exception as e:
            self.yolo = None
            self._log_status(f"❌ Failed to load AI model: {e}")
            messagebox.showerror("AI Model error", f"Could not load AI model:\n{e}")

    def _update_frame(self):
        if self._is_closing:
            return
        if not self.running or self.cap is None:
            self.after(60, self._update_frame)
            return

        try:
            ok, frame = self.cap.read()
            if not ok:
                self.after(200, self._update_frame)
                return

            self._update_fps()

            if self._ai_enabled and self.selected_drone_id and self.yolo is not None:
                self._process_count += 1
                if self._process_count % FRAME_SKIP == 0:
                    display_image = self._process_frame_with_ai(frame)
                else:
                    display_image = self._last_processed_frame if self._last_processed_frame else self._resize_frame(frame)
            else:
                display_image = self._resize_frame(frame)

            self._camera_image = ImageTk.PhotoImage(display_image)
            self.camera_label.configure(image=self._camera_image, text="", fg_color=COLORS["text_primary"])
        except Exception as e:
            self._log_status(f"⚠️ Frame error: {e}")

        self.after(40, self._update_frame)

    def _resize_frame(self, frame) -> Image.Image:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame_rgb.shape
        target_w, target_h = DISPLAY_SIZE

        aspect = w / h
        target_aspect = target_w / target_h
        if aspect > target_aspect:
            new_w = target_w
            new_h = int(target_w / aspect)
        else:
            new_h = target_h
            new_w = int(target_h * aspect)

        pil_image = Image.fromarray(frame_rgb)
        resized = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        canvas = Image.new('RGB', DISPLAY_SIZE, (20, 20, 30))
        offset = ((target_w - new_w) // 2, (target_h - new_h) // 2)
        canvas.paste(resized, offset)
        return canvas

    def _process_frame_with_ai(self, frame) -> Image.Image:
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = frame_rgb.shape
            target_w, target_h = DISPLAY_SIZE

            aspect = w / h
            target_aspect = target_w / target_h
            if aspect > target_aspect:
                new_w = target_w
                new_h = int(target_w / aspect)
            else:
                new_h = target_h
                new_w = int(target_h * aspect)

            inference_frame = cv2.resize(frame_rgb, (new_w, new_h))

            results = self.yolo.predict(
                source=inference_frame,
                conf=CONF_THRESHOLD,
                verbose=False,
                device='gpu',
                half=False
            )

            if not results:
                canvas = Image.new('RGB', DISPLAY_SIZE, (20, 20, 30))
                canvas.paste(Image.fromarray(inference_frame), ((target_w - new_w) // 2, (target_h - new_h) // 2))
                self._last_processed_frame = canvas
                return canvas

            result = results[0]
            detections = self._extract_detections(result, (new_w, new_h))
            detections = self._apply_temporal_stability(detections, (new_h, new_w, 3))

            if detections:
                self._handle_detections(detections)
                annotated_bgr = result.plot()
                annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
                canvas = Image.new('RGB', DISPLAY_SIZE, (20, 20, 30))
                canvas.paste(Image.fromarray(annotated_rgb), ((target_w - new_w) // 2, (target_h - new_h) // 2))
                self._last_processed_frame = canvas
                return canvas
            else:
                self._active_detections_label.configure(text="⚠️ Alerts: 0", text_color=COLORS["text_muted"])

            canvas = Image.new('RGB', DISPLAY_SIZE, (20, 20, 30))
            canvas.paste(Image.fromarray(inference_frame), ((target_w - new_w) // 2, (target_h - new_h) // 2))
            self._last_processed_frame = canvas
            return canvas

        except Exception as e:
            self._log_status(f"⚠️ AI error: {e}")
            return self._resize_frame(frame)

    def _update_fps(self):
        self._frame_count += 1
        now = time.time()
        if now - self._last_time >= 1.0:
            fps = self._frame_count / (now - self._last_time)
            if hasattr(self.master, "title"):
                self.master.title(f"Gaia Sentinel — Drone Attachment Center ({fps:.1f} FPS)")
            self._frame_count = 0
            self._last_time = now

    def _extract_detections(self, result, size: tuple) -> List[tuple]:
        detections = []
        h, w = size[1], size[0]
        frame_area = float(h * w)
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            if conf < CLASS_MIN_CONF.get(cls_id, CONF_THRESHOLD):
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            box_area = float((x2 - x1) * (y2 - y1))
            if box_area / frame_area >= CLASS_MIN_AREA_FRAC.get(cls_id, 0.0):
                detections.append((cls_id, conf, x1, y1, x2, y2))
        return detections

    def _apply_temporal_stability(self, detections: List[tuple], shape: tuple) -> List[tuple]:
        h, w, _ = shape
        stable = []
        for key in list(self._stability.keys()):
            self._stability[key] = max(0, self._stability[key] - 1)
            if self._stability[key] == 0:
                self._stability.pop(key, None)
        for cls_id, conf, x1, y1, x2, y2 in detections:
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            gx, gy = int(cx / max(1, w / 10)), int(cy / max(1, h / 10))
            key = (cls_id, gx, gy)
            self._stability[key] = self._stability.get(key, 0) + 2
            if self._stability[key] >= STABILITY_FRAMES:
                stable.append((cls_id, conf, x1, y1, x2, y2))
        return stable

    def _handle_detections(self, detections: List[tuple]):
        best_cls_id, best_conf, *_ = max(detections, key=lambda d: d[1])
        best_label, best_code = CLASS_MAP.get(best_cls_id, (f"Class {best_cls_id}", f"CLASS_{best_cls_id}"))
        self._active_detections_label.configure(
            text=f"⚠️ Alerts: {len(detections)}", text_color=COLORS["danger"]
        )
        self._log_status(f"⚠️ {best_label} detected ({best_conf:.2f})")
        for cls_id, conf, *_ in detections:
            label, code = CLASS_MAP.get(cls_id, (f"Class {cls_id}", f"CLASS_{cls_id}"))
            if conf >= ALERT_CONF_THRESHOLD:
                self._maybe_send_alert(code, label, conf)

    def _maybe_send_alert(self, code: str, label: str, conf: float):
        now = time.time()
        last = self._last_alert_times.get(code, 0)
        if now - last < ALERT_COOLDOWN:
            return
        self._last_alert_times[code] = now
        self._log_status(f"📧 Sending alert: {label}")

        drone_id = self.selected_drone_id or "UNKNOWN"
        location = next((d.get("location", "Unknown") for d in DRONES if d["id"] == drone_id), "Unknown")

        threading.Thread(
            target=self._send_alert_email,
            args=(code, label, conf, drone_id, location),
            daemon=True
        ).start()

    def _send_alert_email(self, code: str, label: str, conf: float, drone_id: str, location: str):
        if not all([EMAIL_SENDER, EMAIL_PASSWORD, ALERT_RECIPIENT]):
            return
        subject = f"Gaia Sentinel Alert — {label} Detected"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body = (
            f"Gaia Sentinel AI Alert\n\n"
            f"Alert Type : {label}\n"
            f"Drone Attachment : {drone_id}\n"
            f"Location   : {location}\n"
            f"Confidence : {conf:.2f}\n"
            f"Time       : {timestamp}\n"
        )

        try:
            msg = EmailMessage()
            msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_SENDER}>"
            msg["To"] = ALERT_RECIPIENT
            msg["Subject"] = subject
            msg.set_content(body)

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)

            self._log_status(f"✅ Alert sent for {label}")
        except Exception as e:
            self._log_status(f"❌ Email error: {e}")
            messagebox.showerror("Email error", f"Could not send alert email:\n{e}")

    # ===================== CLEANUP =====================

    def _on_closing(self):
        self._is_closing = True
        self.running = False
        try:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
        except Exception:
            pass
        self.destroy()

    def destroy(self):
        self._is_closing = True
        try:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
        except Exception:
            pass
        super().destroy()
