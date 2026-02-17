import random
from iPT_UA_database import *
from tkinter import messagebox
from PIL import Image
from customtkinter import *
import socket
import urllib.request
import add_air_node
import add_water_node
import add_hepa_node
import add_genesis_node
import program_esp_gui
import threading
from themes import pink, lavender_og, blue, green, orange
import json, os
from iPT_Drone_Page import GaiaSentinelDroneCenter
from pages.home_core import Dashboard

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
    "bg_primary": THEME["LAVENDER_MIST"],
    "bg_secondary": THEME["WISTERIA"],
    "accent": THEME["VELVET_ORCHID"],
    "accent_hover": THEME["DARK_AMETHYST"],
    "text_main": THEME["COFFEE_BEAN"],
    "text_subtle": THEME["VELVET_ORCHID"],
    "border": THEME["DARK_AMETHYST"],
    "shadow": THEME["COFFEE_BEAN"],

    # Status / system
    "danger": THEME["DANGER"],
    "danger_hover": THEME["DANGER_HOVER"],
    "success": THEME["SUCCESS"],

    # Generic backgrounds
    "bg": THEME["LAVENDER_MIST"],
    "accent1": THEME["WISTERIA"],
    "accent2": THEME["VELVET_ORCHID"],
    "accent3": THEME["DARK_AMETHYST"],
    "accent4": THEME["COFFEE_BEAN"],

    # Panels / cards
    "panel": THEME["PANEL"],
    "panel_edge": THEME["PANEL_EDGE"],
    "panel_alt": THEME["PANEL_ALT"],
    "text": THEME["PANEL_TEXT"],
    "subtext": THEME["PANEL_SUBTEXT"],

    # Warnings / selection
    "warn": THEME["WARN"],
    "warn_hover": THEME["WARN_HOVER"],
    "select": THEME["SELECT"],

    # Text / muted
    "text_dark": THEME["TEXT_DARK"],
    "muted": THEME["MUTED"],

    # Frames
    "frame": THEME["FRAME_BG"],

    # Root / sidebar
    "root_bg_dark": THEME["ROOT_BG_DARK"],
    "SIDEBAR_BG": THEME["SIDEBAR_BG"],
    "SIDEBAR_ACTIVE": THEME["SIDEBAR_ACTIVE"],
    "DIVIDER": THEME["DIVIDER"],
    "DANGER_HOVER": THEME["DANGER_HOVER"],
    "NO_INTERNET_BG": THEME["NO_INTERNET_BG"],

    # Progress / login / inputs
    "progress_bg": THEME["PROGRESS_BG"],
    "login_btn_bg": THEME["LOGIN_BTN_BG"],
    "login_btn_hover": THEME["LOGIN_BTN_HOVER"],
    "placeholder": THEME["PLACEHOLDER"],

    # Profile / clear hover
    "PROFILE_BG": THEME["PROFILE_BG"],
    "clear_hover": THEME["CLEAR_HOVER"],

    # Status pills
    "STATUS_ONLINE": THEME["STATUS_ONLINE"],
    "STATUS_OFFLINE": THEME["STATUS_OFFLINE"],
    "PROFILE_BG": THEME["PROFILE_BG"],
    'FRAME_BG': THEME["FRAME_BG"],
    "ROOT_BG_DARK": THEME["ROOT_BG_DARK"],
    "STATUS_OFFLINE": THEME["STATUS_OFFLINE"],
    'PANEL': THEME["PANEL"],
    "PANEL_TEXT": THEME["PANEL_TEXT"],
    'PROGRESS_BG': THEME["PROGRESS_BG"], 
    "VELVET_ORCHID": THEME["VELVET_ORCHID"],
    "DARK_AMETHYST": THEME["DARK_AMETHYST"],
    'SUCCESS': THEME["SUCCESS"], 
    'CLEAR_HOVER': THEME["CLEAR_HOVER"],
    'WARN': THEME["WARN"],
    'WARN_HOVER': THEME["WARN_HOVER"],
    "STATUS_ONLINE": THEME["STATUS_ONLINE"],
    'PANEL_SUBTEXT': THEME["PANEL_SUBTEXT"],
    'PLACEHOLDER': THEME["PLACEHOLDER"],
}

def is_online(timeout=3):
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=timeout).close()
        return True
    except Exception as e:
        print(e)
    try:
        with urllib.request.urlopen("http://clients3.google.com/generate_204", timeout=timeout) as r:
            if r.status == 204:
                return True
            else:
                return True
    except Exception as e:
        print(e)
    return False


class IPropellerUserApp:
    def __init__(self):
        self.all_nodes_id_in = None
        self.all_nodes_data_change_ids = None
        self.selected_node_id = None
        self.air_nodes = None
        self.water_nodes = None
        self.root = CTk()
        set_appearance_mode("dark")
        self.root.title("Gaia Sentinel")
        self.root.iconbitmap('icon2.ico')
        windowWidth = 450
        windowHeight = 600
        positionRight = int(self.root.winfo_screenwidth() / 2 - windowWidth / 2)
        positionDown = int(self.root.winfo_screenheight() / 2 - windowHeight / 2)
        self.root.geometry("+{}+{}".format(positionRight, positionDown))
        self.root.minsize(600, 450)
        self.root.resizable(True, True)

        self._last_status = None
        self.root.after(1000, self._start_connectivity_loop)

        self.main_frame = None
        self.home_back_img_id = None
        self.user = 'Abinaav K'
        self.user_email = 'vain.blackmail@gmail.com'

        self._handle_connectivity(True)

        self.root.mainloop()

    def _start_connectivity_loop(self):
        def worker():
            ok = is_online(timeout=3)
            self.root.after(0, self._handle_connectivity, ok)

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(4000, self._start_connectivity_loop)

    def _handle_connectivity(self, ok):
        if self._last_status == ok:
            return
        self._last_status = ok
        if ok:
            self.home_page()
        else:
            self.no_internet_page()

    def home_page(self):
        for childing in self.root.winfo_children():
            childing.destroy()

        self.root.title("Gaia Sentinel - Home")
        self.root.configure(fg_color=THEME["ROOT_BG_DARK"])
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight() - 73}+0+0")
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.main_frame = CTkFrame(self.root, fg_color=COLORS["bg_primary"], corner_radius=15, border_width=1, border_color=COLORS["panel_edge"])
        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=15, pady=10)

        topbar = CTkFrame(self.root, fg_color=COLORS["bg_secondary"], corner_radius=15)
        topbar.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=13, pady=(10, 0))
        topbar.grid_columnconfigure(1, weight=1)

        image = CTkImage(light_image=Image.open("in_app_logo.png"), size=(50, 50))
        logo = CTkLabel(topbar, image=image, text='')
        logo.grid(row=0, column=0, padx=(10, 0), pady=5)

        title = CTkLabel(topbar, text="Gaia Sentinel", text_color=COLORS["text_main"], font=("Segoe UI Semibold", 28, 'bold'))
        title.grid(row=0, column=1, sticky="w", padx=10)

        image1 = CTkImage(light_image=Image.open("no_user_icon.png"), size=(40, 40))
        person_ico = CTkLabel(topbar, image=image1, text='')
        person_ico.grid(row=0, column=2, padx=(25, 0), pady=5)

        user_btn = CTkLabel(topbar, text=self.user, fg_color=COLORS["bg_secondary"], text_color=COLORS["text_main"],
                            corner_radius=12, height=35, font=('tahoma', 17))
        user_btn.grid(row=0, column=3, padx=(5, 25), pady=5)

        self.current_nav_button = ''
        self.nav_buttons = {}

        sidebar = CTkFrame(self.root, fg_color=COLORS['SIDEBAR_BG'], width=230, corner_radius=15)
        sidebar.grid(row=1, column=0, sticky="nsew", padx=(13, 0), pady=10)
        # Row 6 will be the expanding spacer
        sidebar.grid_rowconfigure(6, weight=1)

        # Split items into top and bottom
        top_items = [
            ("🏡  Home", self.home_home_page),
            ("🚁  Drone", self.home_drone_page),
            ("🌀  Air Node", self.home_air_node_page),
            ("💧  Water Node", self.home_water_node_page),
            ("💨  Hepa Node", self.home_hepa_node_page),
            ("🍃  Genesis Node", self.home_genesis_node_page),
            ("💬  Support", self.home_support_page)]
        
        bottom_items = [("⚙️  Settings", self.home_settings_page)]

        for i, (name, command) in enumerate(top_items):
            btn = CTkButton(sidebar, command=lambda b=name, cmd=command: self.navigate(b, cmd),
                            text=name, fg_color="transparent", hover_color=COLORS['SIDEBAR_ACTIVE'],
                            text_color=COLORS["text_main"], anchor="w", font=("tahoma", 17), 
                            height=45, corner_radius=10)
            btn.grid(row=i, column=0, sticky="ew", padx=16, pady=4)
            self.nav_buttons[name] = btn

            if name == '🏡  Home':
                self.navigate(name, command)

        # Add Settings at row 7 (after the spacer row 6)
        for i, (name, command) in enumerate(bottom_items):
            btn = CTkButton(sidebar, command=lambda b=name, cmd=command: self.navigate(b, cmd),
                            text=name, fg_color="transparent", hover_color=COLORS['SIDEBAR_ACTIVE'],
                            text_color=COLORS["text_main"], anchor="w", font=("tahoma", 17), 
                            height=45, corner_radius=10)
            btn.grid(row=7+i, column=0, sticky="ew", padx=16, pady=4)
            self.nav_buttons[name] = btn

        divider = CTkFrame(sidebar, fg_color=COLORS['DIVIDER'], height=2)
        divider.grid(row=8, column=0, sticky="ew")

        logout_btn = CTkButton(sidebar, text="\u23F3 Logout", fg_color=COLORS["danger"], hover_color=COLORS['DANGER_HOVER'],
                               text_color="white", command=self.welcome_page, corner_radius=10, font=("Segoe UI", 14, "bold"))
        logout_btn.grid(row=9, column=0, sticky="ew", padx=15, pady=(15, 10))

    def navigate(self, button_name, cmd):
        if self.current_nav_button == button_name:
            return

        if self.current_nav_button:
            self.nav_buttons[self.current_nav_button].configure(fg_color='transparent', text_color="black")

        if CURRENT_THEME in ('Orange', 'Lavender'):
            self.nav_buttons[button_name].configure(fg_color=COLORS['SIDEBAR_ACTIVE'])
        else:
            self.nav_buttons[button_name].configure(fg_color=COLORS['SIDEBAR_ACTIVE'], text_color="white")
        
        self.current_nav_button = button_name
        cmd()

    def home_home_page(self):
        for child in self.main_frame.winfo_children():
            if id(child) != self.home_back_img_id:
                child.destroy()

        self.main_frame.configure(fg_color=COLORS["bg_secondary"])
        self.dashboard = Dashboard(self.main_frame, self, COLORS)

    def _old_home_home_page(self):
        for child in self.main_frame.winfo_children():
            if id(child) != self.home_back_img_id:
                child.destroy()

        self.main_frame.configure(fg_color=COLORS["bg_secondary"])

        # ----------------- LOAD USER INFO (for header card) -----------------
        current_user = {
            "username": self.user_email,
            "state": "Unknown",
            "city": "Unknown",
            "email": self.user_email,
        }

        # ----------------- LOAD LIVE SENSOR DATA FROM DB -----------------
        sensors = []
        alerts = []

        # If DB failed or is empty, fall back to your original demo sensors/alerts
        if not sensors:
            sensors = [
                {"id": "AQ-01", "type": "Air", "status": "online", "region": "Forest North", "details": {}},
                {"id": "AQ-02", "type": "Air", "status": "offline", "region": "Wetland East", "details": {}},
                {"id": "WQ-01", "type": "Water", "status": "online", "region": "River Delta", "details": {}},
                {"id": "WQ-02", "type": "Water", "status": "online", "region": "Reservoir West", "details": {}},
                {"id": "DN-01", "type": "Drone", "status": "online", "region": "Coastal Watch", "details": {}},
                {"id": "DN-02", "type": "Drone", "status": "offline", "region": "Highland Ridge", "details": {}},
            ]

        if not alerts:
            import datetime
            now = datetime.datetime.now()
            alerts = [
                {
                    "level": "warning",
                    "source": "AQ-02",
                    "msg": "Wetland East air node offline.",
                    "time": (now - datetime.timedelta(minutes=18)).strftime("%H:%M"),
                },
                {
                    "level": "info",
                    "source": "DN-01",
                    "msg": "Drone mission completed, imagery uploaded.",
                    "time": (now - datetime.timedelta(minutes=43)).strftime("%H:%M"),
                },
                {
                    "level": "info",
                    "source": "System",
                    "msg": "Daily data backup completed.",
                    "time": (now - datetime.timedelta(hours=3)).strftime("%H:%M"),
                },
            ]

        # ----------------- BASIC STATS -----------------
        total_sensors = len(sensors)
        online = sum(1 for s in sensors if s["status"] == "online")
        offline = sum(1 for s in sensors if s["status"] == "offline")
        uptime_ratio = (online / total_sensors) if total_sensors else 0
        warning_count = sum(1 for a in alerts if a.get("level") == "warning")

        type_counts = {"Air": 0, "Water": 0, "Drone": 0}
        for s in sensors:
            t = s.get("type")
            if t in type_counts:
                type_counts[t] += 1

        # ----------------- POPUP: SENSOR DETAIL (TOPMOST) -----------------
        def open_sensor_detail(sensor: dict):
            # Avoid master=tk error: only use self if it is a tk widget
            try:
                master = self if hasattr(self, "tk") else None
            except Exception:
                master = None

            win = CTkToplevel(master)
            win.title(f"Sensor details — {sensor.get('id', '')}")
            win.geometry("420x320")
            win.grab_set()
            win.configure(fg_color=COLORS["panel"])
            try:
                pass
            except Exception:
                pass
            win.lift()
            win.focus_force()

            CTkLabel(
                win,
                text=f"{sensor.get('id', '')} • {sensor.get('type', '')}",
                font=("Segoe UI Semibold", 17, "bold"),
                text_color=COLORS["text_dark"],
            ).pack(anchor="w", padx=16, pady=(14, 4))

            region = sensor.get("region", "-")
            status = sensor.get("status", "-")
            st_color = THEME['STATUS_ONLINE'] if status == "online" else THEME['STATUS_OFFLINE']

            CTkLabel(
                win,
                text=status.upper(),
                font=("Segoe UI", 11, "bold"),
                text_color="black",
                fg_color=st_color,
                corner_radius=8,
                padx=8,
                pady=4,
            ).pack(anchor="w", padx=16, pady=(0, 6))

            CTkLabel(
                win,
                text=f"Region: {region}",
                font=("Segoe UI", 11),
                text_color=COLORS["text"],
            ).pack(anchor="w", padx=16, pady=(0, 4))

            # Show details if present (from DB)
            details = sensor.get("details", {}) or {}
            if details:
                detail_frame = CTkFrame(win, fg_color=COLORS["panel_alt"], corner_radius=12)
                detail_frame.pack(fill="x", padx=16, pady=(8, 8))
                for k, v in details.items():
                    CTkLabel(
                        detail_frame,
                        text=f"{k}: {v}",
                        font=("Segoe UI", 10),
                        text_color=COLORS["subtext"],
                    ).pack(anchor="w", padx=10, pady=1)
            else:
                CTkLabel(
                    win,
                    text="No live telemetry available for this node.",
                    font=("Segoe UI", 10),
                    text_color=COLORS["subtext"],
                ).pack(anchor="w", padx=16, pady=(6, 8))

            # Quick actions based on type
            btn_row = CTkFrame(win, fg_color="transparent")
            btn_row.pack(fill="x", padx=16, pady=(6, 10))
            btn_row.grid_columnconfigure((0, 1), weight=1)

            def go_to_manager():
                if hasattr(self, "home_settings_page"):
                    self.home_settings_page()
                win.destroy()

            CTkButton(
                btn_row,
                text="Open in manager",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color="white",
                corner_radius=10,
                height=30,
                command=go_to_manager,
            ).grid(row=0, column=0, padx=4, pady=4, sticky="ew")

            CTkButton(
                btn_row,
                text="Close",
                fg_color=COLORS["panel_alt"],
                hover_color=COLORS["frame"],
                text_color=COLORS["text_dark"],
                corner_radius=10,
                height=30,
                command=win.destroy,
            ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        # ----------------- MAIN WRAPPER -----------------
        wrapper = CTkFrame(self.main_frame, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)
        wrapper.grid_rowconfigure(0, weight=0)
        wrapper.grid_rowconfigure(1, weight=1)
        wrapper.grid_columnconfigure(0, weight=3)
        wrapper.grid_columnconfigure(1, weight=2)

        # ----------------- HEADER -----------------
        header = CTkFrame(
            wrapper,
            fg_color=COLORS["panel"],
            corner_radius=24,
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        header.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        CTkLabel(
            header,
            text="Gaia Sentinel • Home",
            font=("Segoe UI Semibold", 20, "bold"),
            text_color=COLORS["text_main"],
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(10, 0))

        CTkLabel(
            header,
            text="Live overview of your environmental network.",
            font=("Segoe UI", 11),
            text_color=COLORS["subtext"],
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 12))

        CTkLabel(
            header,
            text=datetime.datetime.now().strftime("%d %b %Y  •  %I:%M %p"),
            font=("Segoe UI", 11),
            text_color=COLORS["muted"],
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=22)

        # Small user profile chip in header
        user_chip = CTkFrame(header, fg_color=COLORS["panel_alt"], corner_radius=999)
        user_chip.grid(row=0, column=2, rowspan=2, sticky="e", padx=(0, 18), pady=8)
        CTkLabel(
            user_chip,
            text=f"{current_user['username']}  •  {current_user['city']}, {current_user['state']}",
            font=("Segoe UI", 9),
            text_color=COLORS["subtext"],
        ).pack(padx=10, pady=4)

        # ----------------- LEFT SIDE -----------------
        left = CTkFrame(wrapper, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        left.grid_rowconfigure(0, weight=0)  # hero
        left.grid_rowconfigure(1, weight=0)  # kpi row
        left.grid_rowconfigure(2, weight=1)  # regions + timeline
        left.grid_columnconfigure(0, weight=3)
        left.grid_columnconfigure(1, weight=2)

        # HERO PANEL
        hero = CTkFrame(
            left,
            fg_color=COLORS["panel_alt"],
            corner_radius=24,
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        hero.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=0)

        CTkLabel(
            hero,
            text="Defend the planet.\nShape the future.",
            font=("Segoe UI Semibold", 24, "bold"),
            text_color=COLORS["text"],
            justify="left",
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(16, 4))

        CTkLabel(
            hero,
            text="Today’s snapshot for all Gaia nodes — air, water and drone missions.",
            font=("Segoe UI", 11),
            text_color=COLORS["subtext"],
            wraplength=450,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 16))

        # Simple health bar
        health_box = CTkFrame(hero, fg_color="transparent")
        health_box.grid(row=0, column=1, rowspan=2, sticky="e", padx=22, pady=12)

        CTkLabel(
            health_box,
            text="Network health",
            font=("Segoe UI", 11, "bold"),
            text_color=COLORS["text_subtle"],
        ).pack(anchor="w", pady=(0, 2))

        health_bar = CTkProgressBar(
            health_box,
            width=160,
            height=10,
            corner_radius=999,
            fg_color=COLORS["frame"],
            progress_color=COLORS["accent"],
        )
        health_bar.set(uptime_ratio)
        health_bar.pack(pady=(2, 4))

        CTkLabel(
            health_box,
            text=f"{online}/{total_sensors} sensors online",
            font=("Segoe UI", 10),
            text_color=COLORS["muted"],
        ).pack(anchor="w")

        # ----------------- KPI CARDS ROW -----------------
        kpi_row = CTkFrame(left, fg_color="transparent")
        kpi_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def kpi(parent, col, title, value, sub):
            card = CTkFrame(
                parent,
                fg_color=COLORS["panel"],
                corner_radius=18,
                border_width=1,
                border_color=COLORS["panel_edge"],
            )
            card.grid(row=0, column=col, sticky="nsew", padx=4)
            CTkLabel(
                card,
                text=title,
                font=("Segoe UI", 10, "bold"),
                text_color=COLORS["text_subtle"],
            ).pack(anchor="w", padx=12, pady=(8, 0))
            CTkLabel(
                card,
                text=value,
                font=("Segoe UI Semibold", 18, "bold"),
                text_color=COLORS["text"],
            ).pack(anchor="w", padx=12, pady=(2, 0))
            CTkLabel(
                card,
                text=sub,
                font=("Segoe UI", 9),
                text_color=COLORS["muted"],
            ).pack(anchor="w", padx=12, pady=(0, 8))

        kpi(kpi_row, 0, "Total sensors", str(total_sensors), "All registered nodes")
        kpi(kpi_row, 1, "Online", str(online), "Responding normally")
        kpi(kpi_row, 2, "Offline", str(offline), "Needs attention")
        kpi(
            kpi_row,
            3,
            "Alerts today",
            str(warning_count),
            "Warnings in the last 24h",
        )

        # ----------------- REGIONS GRID (bottom-left) -----------------
        regions_panel = CTkFrame(
            left,
            fg_color=COLORS["panel"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        regions_panel.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        regions_panel.grid_rowconfigure(1, weight=1)
        regions_panel.grid_columnconfigure((0, 1), weight=1)

        CTkLabel(
            regions_panel,
            text="Regions overview",
            font=("Segoe UI Semibold", 14, "bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(10, 2))

        regions = {}
        for s in sensors:
            r = s.get("region", "Unknown")
            info = regions.setdefault(r, {"online": 0, "offline": 0})
            if s["status"] == "online":
                info["online"] += 1
            else:
                info["offline"] += 1

        regions_frame = CTkScrollableFrame(
            regions_panel,
            fg_color="transparent",
            corner_radius=0,
        )
        regions_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(0, 8))

        if not regions:
            CTkLabel(
                regions_frame,
                text="No regions configured.",
                font=("Segoe UI", 11),
                text_color=COLORS["muted"],
            ).pack(pady=10)
        else:
            for name, info in regions.items():
                box = CTkFrame(
                    regions_frame,
                    fg_color=COLORS["panel_alt"],
                    corner_radius=16,
                    border_width=1,
                    border_color=COLORS["panel_edge"],
                )
                box.pack(fill="x", padx=4, pady=4)

                CTkLabel(
                    box,
                    text=name,
                    font=("Segoe UI Semibold", 11, "bold"),
                    text_color=COLORS["text"],
                ).grid(row=0, column=0, sticky="w", padx=12, pady=(6, 0))

                CTkLabel(
                    box,
                    text=f"{info['online']} online • {info['offline']} offline",
                    font=("Segoe UI", 10),
                    text_color=COLORS["subtext"],
                ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 6))

                p = info["online"] / (info["online"] + info["offline"]) if (info["online"] + info["offline"]) else 0
                bar = CTkProgressBar(
                    box,
                    width=160,
                    height=8,
                    corner_radius=999,
                    fg_color=COLORS["frame"],
                    progress_color=COLORS["accent"],
                )
                bar.set(p)
                bar.grid(row=0, column=1, rowspan=2, sticky="e", padx=12)

                box.grid_columnconfigure(0, weight=1)

        # ----------------- ACTIVITY TIMELINE (bottom-right of left area) -----------------
        timeline_panel = CTkFrame(
            left,
            fg_color=COLORS["panel"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        timeline_panel.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        timeline_panel.grid_rowconfigure(1, weight=1)
        timeline_panel.grid_columnconfigure(0, weight=1)

        CTkLabel(
            timeline_panel,
            text="Activity timeline",
            font=("Segoe UI Semibold", 14, "bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(10, 2))

        timeline_frame = CTkScrollableFrame(
            timeline_panel,
            fg_color="transparent",
            corner_radius=0,
        )
        timeline_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

        for ev in sorted(alerts, key=lambda a: a.get("time", ""), reverse=True):
            row = CTkFrame(
                timeline_frame,
                fg_color=COLORS["frame"],
                corner_radius=14,
            )
            row.pack(fill="x", padx=4, pady=4)

            CTkLabel(
                row,
                text=ev.get("time", ""),
                font=("Segoe UI", 9, "bold"),
                text_color=COLORS["muted"],
            ).grid(row=0, column=0, sticky="nw", padx=10, pady=(6, 0))

            CTkLabel(
                row,
                text=ev.get("msg", ""),
                font=("Segoe UI", 10),
                text_color=COLORS["text"],
                wraplength=260,
                justify="left",
            ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 2))

            CTkLabel(
                row,
                text=f"Source: {ev.get('source', '')}",
                font=("Segoe UI", 9),
                text_color=COLORS["subtext"],
            ).grid(row=2, column=0, sticky="w", padx=10, pady=(0, 6))

        # ----------------- RIGHT SIDE: QUICK ACTIONS + SENSOR LIST + STATUS -----------------
        right = CTkFrame(wrapper, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(14, 0))
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=0)
        right.grid_columnconfigure(0, weight=1)

        # QUICK ACTIONS + SENSOR LIST PANEL
        quick = CTkFrame(
            right,
            fg_color=COLORS["panel_alt"],
            corner_radius=24,
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        quick.grid(row=0, column=0, sticky="nsew")
        quick.grid_rowconfigure(5, weight=1)
        quick.grid_columnconfigure(0, weight=1)

        CTkLabel(
            quick,
            text="Quick actions",
            font=("Segoe UI Semibold", 14, "bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(10, 2))

        CTkLabel(
            quick,
            text="Jump straight into common Gaia Sentinel workflows.",
            font=("Segoe UI", 11),
            text_color=COLORS["subtext"],
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 8))

        btn_box = CTkFrame(quick, fg_color="transparent")
        btn_box.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 10))

        CTkButton(
            btn_box,
            text="Open live dashboard",
            height=34,
            corner_radius=18,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=("Segoe UI", 12, "bold"),
        ).pack(fill="x", pady=3)

        CTkButton(
            btn_box,
            text="View alerts center",
            height=34,
            corner_radius=18,
            fg_color="transparent",
            border_width=2,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            hover_color=COLORS["panel"],
            font=("Segoe UI", 12, "bold"),
        ).pack(fill="x", pady=3)

        CTkButton(
            btn_box,
            text="Manage sensors",
            height=34,
            corner_radius=18,
            fg_color="transparent",
            border_width=2,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            hover_color=COLORS["panel"],
            font=("Segoe UI", 12, "bold"),
        ).pack(fill="x", pady=3)

        CTkButton(
            btn_box,
            text="Support & diagnostics",
            height=34,
            corner_radius=18,
            fg_color="transparent",
            border_width=2,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            hover_color=COLORS["panel"],
            font=("Segoe UI", 12, "bold"),
        ).pack(fill="x", pady=3)

        # ------------ SENSOR LIST + FILTERS ------------
        sensors_header = CTkFrame(quick, fg_color="transparent")
        sensors_header.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 2))
        sensors_header.grid_columnconfigure(0, weight=1)
        sensors_header.grid_columnconfigure(1, weight=0)

        CTkLabel(
            sensors_header,
            text="Sensors",
            font=("Segoe UI Semibold", 13, "bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w")

        from tkinter import StringVar
        filter_var = StringVar(value="All")

        sensors_frame = CTkScrollableFrame(
            quick,
            fg_color="transparent",
            corner_radius=0,
        )
        sensors_frame.grid(row=5, column=0, sticky="nsew", padx=14, pady=(2, 10))

        def rebuild_sensor_list(*_args):
            for w in sensors_frame.winfo_children():
                w.destroy()

            active_filter = filter_var.get()

            for s in sensors:
                if active_filter == "Air" and s["type"] != "Air":
                    continue
                if active_filter == "Water" and s["type"] != "Water":
                    continue
                if active_filter == "Drone" and s["type"] != "Drone":
                    continue
                if active_filter == "Online" and s["status"] != "online":
                    continue
                if active_filter == "Offline" and s["status"] != "offline":
                    continue

                row = CTkFrame(
                    sensors_frame,
                    fg_color=COLORS["panel"],
                    corner_radius=14,
                    border_width=1,
                    border_color=COLORS["panel_edge"],
                )
                row.pack(fill="x", padx=2, pady=3)

                row.grid_columnconfigure(0, weight=1)
                row.grid_columnconfigure(1, weight=0)

                CTkLabel(
                    row,
                    text=f"{s['id']} • {s['type']}",
                    font=("Segoe UI", 11, "bold"),
                    text_color=COLORS["text_dark"],
                ).grid(row=0, column=0, sticky="w", padx=10, pady=(6, 0))

                CTkLabel(
                    row,
                    text=s.get("region", "-"),
                    font=("Segoe UI", 10),
                    text_color=COLORS["subtext"],
                ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 6))

                st = s["status"]
                st_color = THEME['STATUS_ONLINE'] if st == "online" else THEME['STATUS_OFFLINE']
                CTkLabel(
                    row,
                    text=st.upper(),
                    font=("Segoe UI", 10, "bold"),
                    text_color="black",
                    fg_color=st_color,
                    corner_radius=8,
                    padx=8,
                    pady=4,
                ).grid(row=0, column=1, rowspan=2, sticky="e", padx=10)

                def on_click(_evt, sensor=s):
                    open_sensor_detail(sensor)

                row.bind("<Button-1>", on_click)
                for child in row.winfo_children():
                    child.bind("<Button-1>", on_click)

        filter_menu = CTkOptionMenu(
            sensors_header,
            values=["All", "Air", "Water", "Drone", "Online", "Offline"],
            variable=filter_var,
            command=lambda choice: rebuild_sensor_list(),
            fg_color=COLORS["accent"],
            button_color=COLORS["accent_hover"],
            text_color="white",
            corner_radius=10,
            width=120,
        )
        filter_menu.grid(row=0, column=1, sticky="e")

        # Summary chips row
        chip_row = CTkFrame(quick, fg_color="transparent")
        chip_row.grid(row=4, column=0, sticky="ew", padx=16, pady=(2, 4))

        def chip(text):
            c = CTkFrame(
                chip_row,
                fg_color=COLORS["panel"],
                corner_radius=999,
                border_width=0,
            )
            CTkLabel(
                c,
                text=text,
                font=("Segoe UI", 9),
                text_color=COLORS["subtext"],
            ).pack(padx=8, pady=3)
            return c

        chip(f"Air: {type_counts['Air']}").pack(side="left", padx=2)
        chip(f"Water: {type_counts['Water']}").pack(side="left", padx=2)
        chip(f"Drones: {type_counts['Drone']}").pack(side="left", padx=2)

        rebuild_sensor_list()

    def home_drone_page(self):
        for child in self.main_frame.winfo_children():
            if not id(child) == self.home_back_img_id:
                child.destroy()

        self.main_frame.configure(fg_color=COLORS["bg_secondary"])

        drone_center = GaiaSentinelDroneCenter(self.main_frame)
        drone_center.pack(fill="both", expand=True)

    def home_air_node_page(self):
        for child in self.main_frame.winfo_children():
            if not id(child) == self.home_back_img_id:
                child.destroy()

        self.all_nodes_id_in = {}
        self.all_nodes_data_change_ids = {}

        def re_enter_nodes_list():
            abc = get_all_names_air_nodes_offline()
            self.air_nodes = []
            for row in abc:
                self.air_nodes.append(row)

        if not hasattr(self, "air_nodes"):
            self.air_nodes = []
            re_enter_nodes_list()

        if not hasattr(self, "selected_node_id"):
            self.selected_node_id = None

        def add_node_initial():
            render_nodes()

        def remove_node():
            if not self.selected_node_id:
                messagebox.showinfo("Select a node", "Click a node card to select it, then press Remove.")
                return

            remove_air_node_offline(self.selected_node_id)
            self.all_nodes_id_in.pop(f'Node: {self.selected_node_id}', None)
            self.all_nodes_data_change_ids.pop(f'Node: {self.selected_node_id}', None)
            self.selected_node_id = None
            render_nodes()
            messagebox.showinfo('INFO', 'AIR NODE Removed Successful!')

        def render_nodes():
            re_enter_nodes_list()
            for w in grid_area.winfo_children():
                w.destroy()

            a = 0
            for node in self.air_nodes:
                r, c = divmod(a, 3)  # 3 per row
                card = _node_card(grid_area, node)
                card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
                a += 1

            # re-apply selection highlight if needed
            try:
                if self.selected_node_id:
                    key = f"Node: {self.selected_node_id}"
                    if key in self.all_nodes_id_in:
                        self.all_nodes_id_in[key].configure(
                            border_color=COLORS["select"],
                            border_width=3
                        )
            except Exception:
                pass

        def _toggle_select(node_id: str):
            # clear all borders
            for frame_key in self.all_nodes_id_in:
                try:
                    self.all_nodes_id_in[frame_key].configure(border_width=0)
                except Exception:
                    pass

            self.selected_node_id = node_id[0]
            key = f"Node: {node_id[0]}"
            if key in self.all_nodes_id_in:
                self.all_nodes_id_in[key].configure(border_color=COLORS["select"], border_width=3)

        def _node_card(parent, node):
            # Default values
            mq135 = "-"
            mq7 = "-"
            mq2 = "-"
            mq4 = "-"
            mq6 = "-"
            hum = "-"
            temp = "-"
            activity_stat = "False"
            battery = "0"
            online = True

            list_to_upload = []

            card = CTkFrame(
                parent,
                fg_color=COLORS["panel"],
                corner_radius=16,
                border_color=COLORS["select"],
                border_width=0,
            )
            card.grid_rowconfigure(3, weight=1)
            card.grid_columnconfigure(0, weight=1)

            self.all_nodes_id_in[f"Node: {node[0]}"] = card
            card.bind("<Button-1>", lambda e, nid=node: _toggle_select(nid))

            # ---------- Header ----------
            head = CTkFrame(card, fg_color="transparent")
            head.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
            head.grid_columnconfigure(0, weight=1)

            CTkLabel(
                head,
                text=node,
                anchor="w",
                font=("Segoe UI Semibold", 16, "bold"),
                text_color=COLORS["text"],
            ).grid(row=0, padx=(10, 0), column=0, sticky="w")

            status_color = THEME["STATUS_ONLINE"] if activity_stat == "True" else THEME["STATUS_OFFLINE"]
            of_for_id = CTkLabel(
                head,
                text=("ONLINE" if activity_stat == "True" else "OFFLINE"),
                font=("Segoe UI", 12, "bold"),
                text_color="black",
                fg_color=status_color,
                corner_radius=8,
                padx=8,
                pady=4,
            )
            of_for_id.grid(row=0, column=1, sticky="e", padx=(0, 10))
            list_to_upload.append(of_for_id)  # index 0

            # ---------- Metrics ----------
            metrics = CTkFrame(card, fg_color="transparent")
            metrics.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 2))

            # 3 columns, up to 3 rows
            for col in (0, 1, 2):
                metrics.grid_columnconfigure(col, weight=1, uniform="m")

            def metric(row, col, title, value, unit):
                box = CTkFrame(metrics, fg_color=COLORS["panel_edge"], corner_radius=12)
                box.bind("<Button-1>", lambda e, nid=node: _toggle_select(nid))
                box.grid(row=row, column=col, sticky="nsew", padx=6, pady=4)

                CTkLabel(
                    box,
                    text=title,
                    text_color=COLORS["subtext"],
                    font=("Segoe UI", 13, "bold"),
                ).pack(anchor="w", padx=10, pady=(8, 0))

                lbl = CTkLabel(
                    box,
                    text=f"{value} {unit}" if online and value != "-" else "-",
                    text_color=COLORS["text"],
                    font=("Segoe UI Semibold", 18, "bold"),
                )
                lbl.pack(anchor="w", padx=10, pady=(0, 8))
                list_to_upload.append(lbl)
                return lbl

            # Order here defines indices in list_to_upload
            # index 1
            metric(0, 0, "Air Quality (MQ135)", mq135, "ppm")
            # index 2
            metric(0, 1, "CO (MQ7)", mq7, "ppm")
            # index 3
            metric(0, 2, "Smoke (MQ2)", mq2, "ppm")
            # index 4
            metric(1, 0, "Gas (MQ4)", mq4, "ppm")
            # index 5
            metric(1, 1, "Gas (MQ6)", mq6, "ppm")
            # index 6
            metric(1, 2, "Temperature", temp, "°C")
            # index 7
            metric(2, 0, "Humidity", hum, "%")

            # ---------- Battery bar ----------
            bar = CTkProgressBar(
                card,
                height=12,
                corner_radius=6,
                fg_color=THEME["PROGRESS_BG"],
                progress_color=COLORS["accent"],
            )
            bar.grid(row=2, column=0, sticky="ew", padx=14, pady=(8, 0))
            try:
                batt_val = float(battery)
            except Exception:
                batt_val = 0
            bar.set(max(0, min(1, batt_val / 100)) if online else 0)
            list_to_upload.append(bar)  # index 8

            bat_for_id = CTkLabel(
                card,
                text=f"Battery: {batt_val:.0f}%" if online else "Battery: -%",
                font=("Segoe UI", 12),
                text_color=COLORS["subtext"],
            )
            bat_for_id.grid(row=3, column=0, sticky="w", padx=14, pady=(6, 12))
            list_to_upload.append(bat_for_id)  # index 9

            self.all_nodes_data_change_ids[f"Node: {node[0]}"] = list_to_upload
            return card

        # ------------ outer layout ------------
        self.main_frame.configure(fg_color=COLORS["bg_secondary"])
        container = CTkFrame(self.main_frame, fg_color=COLORS["bg_secondary"], corner_radius=14)
        container.pack(fill="both", expand=True, padx=9, pady=14)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        grid_area = CTkScrollableFrame(container, fg_color="transparent")
        grid_area.grid(row=0, column=0, sticky="nsew", padx=5, pady=(12, 6))
        for c in (0, 1, 2):
            grid_area.grid_columnconfigure(c, weight=1, uniform="cols")

        actions = CTkFrame(container, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=5, pady=(6, 12))
        actions.grid_columnconfigure((0, 1), weight=1, uniform="btns")

        CTkButton(
            actions,
            text="Add AirNode",
            height=44,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=("Segoe UI Semibold", 16),
            command=lambda: add_air_node.AddAirNodeTopLevel(self.root, add_node_initial),
        ).grid(row=0, column=0, padx=6, pady=4, sticky="ew")

        CTkButton(
            actions,
            text="Remove AirNode",
            height=44,
            fg_color=COLORS["warn"],
            hover_color=COLORS["warn_hover"],
            text_color="white",
            font=("Segoe UI Semibold", 16),
            command=remove_node,
        ).grid(row=0, column=1, padx=6, pady=4, sticky="ew")

        # ------------ periodic refresh (now includes MQ2, MQ4, MQ6) ------------
        def periodic_super_ref():
            try:
                for abc in self.all_nodes_data_change_ids:
                    node_id = abc.split(": ")[1]
                    addy = get_data_air_node_online(node_id)
                    # Expected: [mq135, mq7, mq2, mq4, mq6, dht22_hum, dht22_temp, activity_status, bat_status]
                    mq135 = addy[0]
                    mq7 = addy[1]
                    mq2 = addy[2]
                    mq4 = addy[3]
                    mq6 = addy[4]
                    hum = addy[5]
                    temp = addy[6]
                    activity_stat = addy[7]
                    battery = addy[8]
                    online = True

                    widgets = self.all_nodes_data_change_ids[abc]

                    status_color = THEME["STATUS_ONLINE"] if activity_stat == "True" else THEME["STATUS_OFFLINE"]
                    widgets[0].configure(text=("ONLINE" if activity_stat == "True" else "OFFLINE"),
                                         fg_color=status_color)

                    widgets[1].configure(text=f"{mq135} ppm" if online and mq135 != "-" else "-")
                    widgets[2].configure(text=f"{mq7} ppm" if online and mq7 != "-" else "-")
                    widgets[3].configure(text=f"{mq2} ppm" if online and mq2 != "-" else "-")
                    widgets[4].configure(text=f"{mq4} ppm" if online and mq4 != "-" else "-")
                    widgets[5].configure(text=f"{mq6} ppm" if online and mq6 != "-" else "-")
                    widgets[6].configure(text=f"{temp} °C" if online and temp != "-" else "-")
                    widgets[7].configure(text=f"{hum} %" if online and hum != "-" else "-")

                    try:
                        batt_val = float(battery)
                    except Exception:
                        batt_val = 0

                    widgets[8].set(max(0, min(1, batt_val / 100)) if online else 0)
                    widgets[9].configure(
                        text=f"Battery: {batt_val:.0f}%" if online else "Battery: -%"
                    )
            except Exception:
                pass

        def periodic_refresh():
            th = threading.Thread(target=periodic_super_ref, daemon=True)
            th.start()
            self.root.after(2000, periodic_refresh)

        render_nodes()
        self.root.after(2000, periodic_refresh)

    def home_water_node_page(self):
        for child in self.main_frame.winfo_children():
            if not id(child) == self.home_back_img_id:
                child.destroy()

        self.all_nodes_id_in = {}
        self.all_nodes_data_change_ids = {}

        def re_enter_nodes_list():
            abc = get_all_names_water_nodes_offline()
            self.water_nodes = []
            for row in abc:
                self.water_nodes.append(row)

        if not hasattr(self, "water_nodes"):
            self.water_nodes = []
            re_enter_nodes_list()

        if not hasattr(self, "selected_node_id"):
            self.selected_node_id = None

        def add_node_initial():
            render_nodes()

        def remove_node():
            if not self.selected_node_id:
                messagebox.showinfo("Select a node", "Click a node card to select it, then press Remove.")
                return

            remove_water_node_offline(self.selected_node_id)
            self.all_nodes_id_in.pop(f'Node: {self.selected_node_id}')
            self.all_nodes_data_change_ids.pop(f'Node: {self.selected_node_id}')
            self.selected_node_id = None
            render_nodes()
            messagebox.showinfo('INFO', 'WATER NODE Removed Successful!')

        def render_nodes():
            re_enter_nodes_list()
            for w in grid_area.winfo_children():
                w.destroy()

            a = 0
            for node in self.water_nodes:
                r, c = divmod(a, 3)  # 3 per row
                card = _node_card(grid_area, node)
                card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
                a += 1

            try:
                if self.selected_node_id:
                    if f"Node: {self.selected_node_id}" in self.all_nodes_id_in:
                        self.all_nodes_id_in[f"Node: {self.selected_node_id}"].configure(border_color=COLORS["select"],
                                                                                         border_width=3)
            except:
                pass

        def _toggle_select(node_id: str):
            for frame in self.all_nodes_id_in:
                try:
                    self.all_nodes_id_in[frame].configure(border_width=0)
                except Exception:
                    pass

            self.selected_node_id = node_id[0]
            if f"Node: {node_id[0]}" in self.all_nodes_id_in:
                self.all_nodes_id_in[f"Node: {node_id[0]}"].configure(border_color=COLORS["select"], border_width=3)

        def _node_card(parent, node):
            tds = "-"
            temp = "-"
            activity_stat = "False"
            battery = "0"
            online = True

            list_to_upload = []

            card = CTkFrame(parent, fg_color=COLORS["panel"], corner_radius=16, border_color=COLORS["select"],
                            border_width=0)
            card.grid_rowconfigure(2, weight=1)
            card.grid_columnconfigure(0, weight=1)

            self.all_nodes_id_in[f"Node: {node[0]}"] = card
            card.bind("<Button-1>", lambda e, nid=node: _toggle_select(nid))

            head = CTkFrame(card, fg_color="transparent")
            head.grid(row=0, column=0, sticky="ew", padx=8, pady=(12, 4))
            head.grid_columnconfigure(0, weight=1)

            CTkLabel(head, text=node, anchor="w", font=("Segoe UI Semibold", 16, "bold"),
                     text_color=COLORS["text"]).grid(row=0, padx=(10, 0), column=0, sticky="w")

            status_color = THEME["STATUS_ONLINE"] if activity_stat == "True" else THEME["STATUS_OFFLINE"]
            status_lbl = CTkLabel(head, text=("ONLINE" if activity_stat == "True" else "OFFLINE"),
                                  font=("Segoe UI", 12, "bold"), text_color="black", fg_color=status_color,
                                  corner_radius=8, padx=8, pady=4)
            status_lbl.grid(row=0, column=1, sticky="e", padx=(0, 10))
            list_to_upload.append(status_lbl)

            metrics = CTkFrame(card, fg_color="transparent")
            metrics.grid(row=1, column=0, sticky="ew", padx=8, pady=(6, 2))
            for col in (0, 1):
                metrics.grid_columnconfigure(col, weight=1, uniform="m")

            def metric(col, title, value, unit):
                box = CTkFrame(metrics, fg_color=COLORS["panel_edge"], corner_radius=12)
                box.bind("<Button-1>", lambda e, nid=node: _toggle_select(nid))
                box.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)

                CTkLabel(box, text=title, text_color=COLORS["subtext"], font=("Segoe UI", 13, "bold")).pack(anchor="w",
                                                                                                            padx=10,
                                                                                                            pady=(8, 0))

                value_lbl = CTkLabel(box, text=f"{value} {unit}" if online and value != "-" else "-",
                                     text_color=COLORS["text"], font=("Segoe UI Semibold", 18, "bold"))
                value_lbl.pack(anchor="w", padx=10, pady=(0, 8))
                return value_lbl

            tds_lbl = metric(0, "Water Quality (TDS)", tds, "ppm")
            temp_lbl = metric(1, "Temperature", temp, "°C")
            list_to_upload.append(tds_lbl)
            list_to_upload.append(temp_lbl)

            bar = CTkProgressBar(card, height=12, corner_radius=6, fg_color=THEME["PROGRESS_BG"],
                                 progress_color=COLORS["accent"])
            bar.grid(row=2, column=0, sticky="ew", padx=8, pady=(8, 0))
            try:
                batt_val = float(battery)
            except Exception:
                batt_val = 0
            bar.set(max(0, min(1, batt_val / 100)) if online else 0)
            list_to_upload.append(bar)

            bat_lbl = CTkLabel(card, text=f"Battery: {batt_val:.0f}%" if online else "Battery: -%",
                               font=("Segoe UI", 12), text_color=COLORS["subtext"])
            bat_lbl.grid(row=3, column=0, sticky="w", padx=8, pady=(6, 12))
            list_to_upload.append(bat_lbl)

            self.all_nodes_data_change_ids[f"Node: {node[0]}"] = list_to_upload
            return card

        self.main_frame.configure(fg_color=COLORS["bg_secondary"])
        container = CTkFrame(self.main_frame, fg_color=COLORS["bg_secondary"], corner_radius=14)
        container.pack(fill="both", expand=True, padx=9, pady=14)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        grid_area = CTkScrollableFrame(container, fg_color="transparent")
        grid_area.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
        for c in (0, 1, 2):
            grid_area.grid_columnconfigure(c, weight=1, uniform="cols")

        # bottom actions
        actions = CTkFrame(container, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=12, pady=(6, 12))
        actions.grid_columnconfigure((0, 1), weight=1, uniform="btns")

        CTkButton(actions, text="Add WaterNode", height=44, fg_color=COLORS["accent"],
                  hover_color=COLORS["accent_hover"], text_color="white", font=("Segoe UI Semibold", 16),
                  command=lambda: add_water_node.AddWaterNodeTopLevel(self.root, add_node_initial)).grid(row=0,
                                                                                                         column=0,
                                                                                                         padx=6, pady=4,
                                                                                                         sticky="ew")

        CTkButton(actions, text="Remove WaterNode", height=44, fg_color=COLORS["warn"],
                  hover_color=COLORS["warn_hover"], text_color="white", font=("Segoe UI Semibold", 16),
                  command=remove_node).grid(row=0, column=1, padx=6, pady=4, sticky="ew")

        def periodic_super_ref():
            try:
                for abc in self.all_nodes_data_change_ids:
                    node_name = abc.split(": ")[1]
                    addy = get_data_water_node_online(node_name)
                    tds = addy[0]
                    temp = addy[1]
                    activity_stat = addy[2]
                    battery = addy[3]
                    online = True

                    widgets = self.all_nodes_data_change_ids[abc]

                    status_color = THEME["STATUS_ONLINE"] if activity_stat == "True" else THEME["STATUS_OFFLINE"]
                    widgets[0].configure(text=("ONLINE" if activity_stat == "True" else "OFFLINE"),
                                         fg_color=status_color)
                    widgets[1].configure(text=f"{tds} ppm" if online and tds != "-" else "-")
                    widgets[2].configure(text=f"{temp} °C" if online and temp != "-" else "-")

                    try:
                        batt_val = float(battery)
                    except Exception:
                        batt_val = 0
                    widgets[3].set(max(0, min(1, batt_val / 100)) if online else 0)

                    widgets[4].configure(text=f"Battery: {batt_val:.0f}%" if online else "Battery: -%")
            except Exception:
                pass

        def periodic_refresh():
            th = threading.Thread(target=periodic_super_ref, daemon=True)
            th.start()
            self.root.after(2000, periodic_refresh)

        render_nodes()
        self.root.after(2000, periodic_refresh)

    def home_hepa_node_page(self):
        for child in self.main_frame.winfo_children():
            if not id(child) == self.home_back_img_id:
                child.destroy()

        self.all_nodes_id_in = {}
        self.all_nodes_data_change_ids = {}

        def re_enter_nodes_list():
            abc = get_all_names_hepa_nodes_offline()
            self.hepa_nodes = []
            for row in abc:
                self.hepa_nodes.append(row)

        if not hasattr(self, "hepa_nodes"):
            self.hepa_nodes = []
            re_enter_nodes_list()

        if not hasattr(self, "selected_node_id"):
            self.selected_node_id = None

        def add_node_initial():
            render_nodes()

        def remove_node():
            if not self.selected_node_id:
                messagebox.showinfo("Select a node", "Click a node card to select it, then press Remove.")
                return

            remove_hepa_node_offline(self.selected_node_id)
            self.all_nodes_id_in.pop(f'Node: {self.selected_node_id}', None)
            self.all_nodes_data_change_ids.pop(f'Node: {self.selected_node_id}', None)
            self.selected_node_id = None
            render_nodes()
            messagebox.showinfo('INFO', 'HEPA NODE Removed Successful!')

        def render_nodes():
            re_enter_nodes_list()
            for w in grid_area.winfo_children():
                w.destroy()

            a = 0
            for node in self.hepa_nodes:
                r, c = divmod(a, 3)  # 3 per row
                card = _node_card(grid_area, node)
                card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
                a += 1

            try:
                if self.selected_node_id:
                    key = f"Node: {self.selected_node_id}"
                    if key in self.all_nodes_id_in:
                        self.all_nodes_id_in[key].configure(
                            border_color=COLORS["select"],
                            border_width=3
                        )
            except Exception:
                pass

        def _toggle_select(node_id: str):
            for frame_key in self.all_nodes_id_in:
                try:
                    self.all_nodes_id_in[frame_key].configure(border_width=0)
                except Exception:
                    pass

            self.selected_node_id = node_id[0]
            key = f"Node: {node_id[0]}"
            if key in self.all_nodes_id_in:
                self.all_nodes_id_in[key].configure(border_color=COLORS["select"], border_width=3)

        def _node_card(parent, node):
            aqi_before = "-"
            aqi_after = "-"
            purification_state = "-"
            activity_stat = "False"
            battery = "0"
            online = True

            list_to_upload = []

            card = CTkFrame(
                parent,
                fg_color=COLORS["panel"],
                corner_radius=16,
                border_color=COLORS["select"],
                border_width=0,
            )
            card.grid_rowconfigure(2, weight=1)
            card.grid_columnconfigure(0, weight=1)

            self.all_nodes_id_in[f"Node: {node[0]}"] = card
            card.bind("<Button-1>", lambda e, nid=node: _toggle_select(nid))

            # ---------- Header ----------
            head = CTkFrame(card, fg_color="transparent")
            head.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
            head.grid_columnconfigure(0, weight=1)

            CTkLabel(
                head,
                text=node,
                anchor="w",
                font=("Segoe UI Semibold", 16, "bold"),
                text_color=COLORS["text"],
            ).grid(row=0, padx=(10, 0), column=0, sticky="w")

            status_color = THEME["STATUS_ONLINE"] if activity_stat == "True" else THEME["STATUS_OFFLINE"]
            status_lbl = CTkLabel(
                head,
                text=("ONLINE" if activity_stat == "True" else "OFFLINE"),
                font=("Segoe UI", 12, "bold"),
                text_color="black",
                fg_color=status_color,
                corner_radius=8,
                padx=8,
                pady=4,
            )
            status_lbl.grid(row=0, column=1, sticky="e", padx=(0, 10))
            list_to_upload.append(status_lbl)  # index 0

            # ---------- Metrics ----------
            metrics = CTkFrame(card, fg_color="transparent")
            metrics.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 2))

            for col in (0, 1, 2):
                metrics.grid_columnconfigure(col, weight=1, uniform="m")

            def metric(col, title, value):
                box = CTkFrame(metrics, fg_color=COLORS["panel_edge"], corner_radius=12)
                box.bind("<Button-1>", lambda e, nid=node: _toggle_select(nid))
                box.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)

                CTkLabel(
                    box,
                    text=title,
                    text_color=COLORS["subtext"],
                    font=("Segoe UI", 13, "bold"),
                ).pack(anchor="w", padx=10, pady=(8, 0))

                lbl = CTkLabel(
                    box,
                    text=value if online and value != "-" else "-",
                    text_color=COLORS["text"],
                    font=("Segoe UI Semibold", 18, "bold"),
                )
                lbl.pack(anchor="w", padx=10, pady=(0, 8))
                return lbl

            # index 1
            aqi_before_lbl = metric(0, "AQI Before", aqi_before)
            list_to_upload.append(aqi_before_lbl)

            # index 2
            aqi_after_lbl = metric(1, "AQI After", aqi_after)
            list_to_upload.append(aqi_after_lbl)

            # index 3
            purification_lbl = metric(2, "Purification State", purification_state)
            list_to_upload.append(purification_lbl)

            # ---------- Battery bar ----------
            bar = CTkProgressBar(
                card,
                height=12,
                corner_radius=6,
                fg_color=THEME["PROGRESS_BG"],
                progress_color=COLORS["accent"],
            )
            bar.grid(row=2, column=0, sticky="ew", padx=14, pady=(8, 0))
            try:
                batt_val = float(battery)
            except Exception:
                batt_val = 0
            bar.set(max(0, min(1, batt_val / 100)) if online else 0)
            list_to_upload.append(bar)  # index 4

            bat_lbl = CTkLabel(
                card,
                text=f"Battery: {batt_val:.0f}%" if online else "Battery: -%",
                font=("Segoe UI", 12),
                text_color=COLORS["subtext"],
            )
            bat_lbl.grid(row=3, column=0, sticky="w", padx=14, pady=(6, 12))
            list_to_upload.append(bat_lbl)  # index 5

            self.all_nodes_data_change_ids[f"Node: {node[0]}"] = list_to_upload
            return card

        # ------------ outer layout ------------
        self.main_frame.configure(fg_color=COLORS["bg_secondary"])
        container = CTkFrame(self.main_frame, fg_color=COLORS["bg_secondary"], corner_radius=14)
        container.pack(fill="both", expand=True, padx=9, pady=14)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        grid_area = CTkScrollableFrame(container, fg_color="transparent")
        grid_area.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
        for c in (0, 1, 2):
            grid_area.grid_columnconfigure(c, weight=1, uniform="cols")

        actions = CTkFrame(container, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=12, pady=(6, 12))
        actions.grid_columnconfigure((0, 1), weight=1, uniform="btns")

        CTkButton(
            actions,
            text="Add HepaNode",
            height=44,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=("Segoe UI Semibold", 16),
            command=lambda: add_hepa_node.AddHepaNodeTopLevel(self.root, add_node_initial),
        ).grid(row=0, column=0, padx=6, pady=4, sticky="ew")

        CTkButton(
            actions,
            text="Remove HepaNode",
            height=44,
            fg_color=COLORS["warn"],
            hover_color=COLORS["warn_hover"],
            text_color="white",
            font=("Segoe UI Semibold", 16),
            command=remove_node,
        ).grid(row=0, column=1, padx=6, pady=4, sticky="ew")

        # ------------ periodic refresh ------------
        def periodic_super_ref():
            try:
                for abc in self.all_nodes_data_change_ids:
                    node_name = abc.split(": ")[1]
                    addy = get_data_hepa_node_online(node_name)
                    # Expected: [aqi_data, purification_state, activity_status, battery]
                    aqi_raw = addy[0]
                    purification_state = addy[1]
                    activity_stat = addy[2]
                    battery = addy[3]
                    online = True

                    aqi_before = "-"
                    aqi_after = "-"

                    try:
                        if isinstance(aqi_raw, str) and aqi_raw.startswith('[') and aqi_raw.endswith(']'):
                            import ast
                            aqi_list = ast.literal_eval(aqi_raw)
                            if isinstance(aqi_list, list) and len(aqi_list) >= 2:
                                aqi_before = str(aqi_list[0])
                                aqi_after = str(aqi_list[1])
                        elif isinstance(aqi_raw, list) and len(aqi_raw) >= 2:
                            aqi_before = str(aqi_raw[0])
                            aqi_after = str(aqi_raw[1])
                        else:
                            aqi_before = str(aqi_raw)
                    except Exception:
                        aqi_before = str(aqi_raw)

                    widgets = self.all_nodes_data_change_ids[abc]

                    status_color = THEME["STATUS_ONLINE"] if activity_stat == "True" else THEME["STATUS_OFFLINE"]
                    widgets[0].configure(
                        text=("ONLINE" if activity_stat == "True" else "OFFLINE"),
                        fg_color=status_color
                    )

                    widgets[1].configure(text=aqi_before if online and aqi_before != "-" else "-")
                    widgets[2].configure(text=aqi_after if online and aqi_after != "-" else "-")
                    widgets[3].configure(text=str(purification_state) if online and purification_state != "-" else "-")

                    try:
                        batt_val = float(battery)
                    except Exception:
                        batt_val = 0

                    widgets[4].set(max(0, min(1, batt_val / 100)) if online else 0)
                    widgets[5].configure(
                        text=f"Battery: {batt_val:.0f}%" if online else "Battery: -%"
                    )
            except Exception:
                pass

        def periodic_refresh():
            th = threading.Thread(target=periodic_super_ref, daemon=True)
            th.start()
            self.root.after(2000, periodic_refresh)

        render_nodes()
        self.root.after(2000, periodic_refresh)

    def home_genesis_node_page(self):
        for child in self.main_frame.winfo_children():
            if not id(child) == self.home_back_img_id:
                child.destroy()

        self.all_nodes_id_in = {}
        self.all_nodes_data_change_ids = {}

        def re_enter_nodes_list():
            abc = get_all_names_genesis_nodes_offline()
            self.genesis_nodes = []
            for row in abc:
                self.genesis_nodes.append(row)

        if not hasattr(self, "genesis_nodes"):
            self.genesis_nodes = []
            re_enter_nodes_list()

        if not hasattr(self, "selected_node_id"):
            self.selected_node_id = None

        def add_node_initial():
            render_nodes()

        def remove_node():
            if not self.selected_node_id:
                messagebox.showinfo("Select a node", "Click a node card to select it, then press Remove.")
                return

            remove_genesis_node_offline(self.selected_node_id)
            self.all_nodes_id_in.pop(f'Node: {self.selected_node_id}', None)
            self.all_nodes_data_change_ids.pop(f'Node: {self.selected_node_id}', None)
            self.selected_node_id = None
            render_nodes()
            messagebox.showinfo('INFO', 'GENESIS NODE Removed Successful!')

        def render_nodes():
            re_enter_nodes_list()
            for w in grid_area.winfo_children():
                w.destroy()

            a = 0
            for node in self.genesis_nodes:
                r, c = divmod(a, 3)  # 3 per row
                card = _node_card(grid_area, node)
                card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
                a += 1

            try:
                if self.selected_node_id:
                    key = f"Node: {self.selected_node_id}"
                    if key in self.all_nodes_id_in:
                        self.all_nodes_id_in[key].configure(
                            border_color=COLORS["select"],
                            border_width=3
                        )
            except Exception:
                pass

        def _toggle_select(node_id: str):
            for frame_key in self.all_nodes_id_in:
                try:
                    self.all_nodes_id_in[frame_key].configure(border_width=0)
                except Exception:
                    pass

            self.selected_node_id = node_id[0]
            key = f"Node: {node_id[0]}"
            if key in self.all_nodes_id_in:
                self.all_nodes_id_in[key].configure(border_color=COLORS["select"], border_width=3)

        def _node_card(parent, node):
            # Default values for Genesis Bio-Node
            aqi_input = "-"
            aqi_output = "-"
            light_intensity = "-"
            purification = "OFF"
            activity_stat = "False"
            battery = "0"
            online = True

            list_to_upload = []

            card = CTkFrame(
                parent,
                fg_color=COLORS["panel"],
                corner_radius=16,
                border_color=COLORS["select"],
                border_width=0,
            )
            card.grid_rowconfigure(2, weight=1)
            card.grid_columnconfigure(0, weight=1)

            self.all_nodes_id_in[f"Node: {node[0]}"] = card
            card.bind("<Button-1>", lambda e, nid=node: _toggle_select(nid))

            # ---------- Header ----------
            head = CTkFrame(card, fg_color="transparent")
            head.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
            head.grid_columnconfigure(0, weight=1)

            CTkLabel(
                head,
                text=node,
                anchor="w",
                font=("Segoe UI Semibold", 16, "bold"),
                text_color=COLORS["text"],
            ).grid(row=0, padx=(10, 0), column=0, sticky="w")

            status_color = THEME["STATUS_ONLINE"] if activity_stat == "True" else THEME["STATUS_OFFLINE"]
            status_lbl = CTkLabel(
                head,
                text=("ONLINE" if activity_stat == "True" else "OFFLINE"),
                font=("Segoe UI", 12, "bold"),
                text_color="white",
                fg_color=status_color,
                corner_radius=8,
                padx=8,
                pady=4,
            )
            status_lbl.grid(row=0, column=1, sticky="e", padx=(0, 10))
            list_to_upload.append(status_lbl)  # index 0

            # ---------- Metrics ----------
            metrics = CTkFrame(card, fg_color="transparent")
            metrics.grid(row=1, column=0, sticky="ew", padx=14, pady=(6, 2))

            # 2 rows, 2 columns for the 4 metrics
            for col in (0, 1):
                metrics.grid_columnconfigure(col, weight=1, uniform="m")

            def metric(row, col, title, value, unit=""):
                box = CTkFrame(metrics, fg_color=COLORS["panel_edge"], corner_radius=12)
                box.bind("<Button-1>", lambda e, nid=node: _toggle_select(nid))
                box.grid(row=row, column=col, sticky="nsew", padx=6, pady=4)

                CTkLabel(
                    box,
                    text=title,
                    text_color=COLORS["subtext"],
                    font=("Segoe UI", 11, "bold"),
                ).pack(anchor="w", padx=10, pady=(8, 0))

                display_text = f"{value} {unit}".strip() if online and value != "-" else "-"
                lbl = CTkLabel(
                    box,
                    text=display_text,
                    text_color=COLORS["text"],
                    font=("Segoe UI Semibold", 18, "bold"),
                )
                lbl.pack(anchor="w", padx=10, pady=(0, 8))
                return lbl

            # index 1
            aqi_input_lbl = metric(0, 0, "AQI INPUT", aqi_input, "AQI")
            list_to_upload.append(aqi_input_lbl)

            # index 2
            aqi_output_lbl = metric(0, 1, "AQI OUTPUT", aqi_output, "AQI")
            list_to_upload.append(aqi_output_lbl)

            # index 3
            light_lbl = metric(1, 0, "LIGHT INTENSITY", light_intensity, "Lux")
            list_to_upload.append(light_lbl)

            # index 4
            purification_lbl = metric(1, 1, "PURIFICATION", purification, "")
            list_to_upload.append(purification_lbl)

            # ---------- Battery bar ----------
            bar = CTkProgressBar(
                card,
                height=12,
                corner_radius=6,
                fg_color=THEME["PROGRESS_BG"],
                progress_color=COLORS["accent"],
            )
            bar.grid(row=2, column=0, sticky="ew", padx=14, pady=(8, 0))
            try:
                batt_val = float(battery)
            except Exception:
                batt_val = 0
            bar.set(max(0, min(1, batt_val / 100)) if online else 0)
            list_to_upload.append(bar)  # index 5

            bat_lbl = CTkLabel(
                card,
                text=f"Battery: {batt_val:.0f}%" if online else "Battery: -%",
                font=("Segoe UI", 12),
                text_color=COLORS["subtext"],
            )
            bat_lbl.grid(row=3, column=0, sticky="w", padx=14, pady=(6, 12))
            list_to_upload.append(bat_lbl)  # index 6

            self.all_nodes_data_change_ids[f"Node: {node[0]}"] = list_to_upload
            return card

        # ------------ outer layout ------------
        self.main_frame.configure(fg_color=COLORS["bg_secondary"])
        container = CTkFrame(self.main_frame, fg_color=COLORS["bg_secondary"], corner_radius=14)
        container.pack(fill="both", expand=True, padx=9, pady=14)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        grid_area = CTkScrollableFrame(container, fg_color="transparent")
        grid_area.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
        for c in (0, 1, 2):
            grid_area.grid_columnconfigure(c, weight=1, uniform="cols")

        actions = CTkFrame(container, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=12, pady=(6, 12))
        actions.grid_columnconfigure((0, 1), weight=1, uniform="btns")

        CTkButton(
            actions,
            text="Add New Genesis Node",
            height=44,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=("Segoe UI Semibold", 16),
            command=lambda: add_genesis_node.AddGenesisNodeTopLevel(self.root, add_node_initial),
        ).grid(row=0, column=0, padx=6, pady=4, sticky="ew")

        CTkButton(
            actions,
            text="Remove Genesis Node",
            height=44,
            fg_color=COLORS["warn"],
            hover_color=COLORS["warn_hover"],
            text_color="white",
            font=("Segoe UI Semibold", 16),
            command=remove_node,
        ).grid(row=0, column=1, padx=6, pady=4, sticky="ew")

        # ------------ periodic refresh ------------
        def periodic_super_ref():
            try:
                for abc in self.all_nodes_data_change_ids:
                    node_name = abc.split(": ")[1]
                    addy = get_data_genesis_node_online(node_name)
                    # Expected: [aqi_input, aqi_output, light_intensity, purification_state, activity_status, battery]
                    aqi_input = addy[0]
                    aqi_output = addy[1]
                    light_intensity = addy[2]
                    purification = addy[3]
                    activity_stat = addy[4]
                    battery = addy[5]
                    online = True

                    widgets = self.all_nodes_data_change_ids[abc]

                    status_color = THEME["STATUS_ONLINE"] if activity_stat == "True" else THEME["STATUS_OFFLINE"]
                    widgets[0].configure(
                        text=("ONLINE" if activity_stat == "True" else "OFFLINE"),
                        fg_color=status_color
                    )

                    widgets[1].configure(text=f"{aqi_input} AQI" if online and aqi_input != "-" else "-")
                    widgets[2].configure(text=f"{aqi_output} AQI" if online and aqi_output != "-" else "-")
                    widgets[3].configure(text=f"{light_intensity} Lux" if online and light_intensity != "-" else "-")
                    widgets[4].configure(text=str(purification) if online and purification != "-" else "OFF")

                    try:
                        batt_val = float(battery)
                    except Exception:
                        batt_val = 0

                    widgets[5].set(max(0, min(1, batt_val / 100)) if online else 0)
                    widgets[6].configure(
                        text=f"Battery: {batt_val:.0f}%" if online else "Battery: -%"
                    )
            except Exception:
                pass

        def periodic_refresh():
            th = threading.Thread(target=periodic_super_ref, daemon=True)
            th.start()
            self.root.after(2000, periodic_refresh)

        render_nodes()
        self.root.after(2000, periodic_refresh)

    def home_support_page(self):
        for child in self.main_frame.winfo_children():
            if not id(child) == self.home_back_img_id:
                child.destroy()

        self.main_frame.configure(fg_color=COLORS["bg_secondary"])

        # Main Container
        container = CTkFrame(self.main_frame, fg_color="transparent")
        container.pack(padx=20, pady=20, fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1, uniform="equal")
        container.grid_columnconfigure(1, weight=1, uniform="equal")
        container.grid_rowconfigure(0, weight=1)

        # --- LEFT: FAQ SECTION ---
        left_panel = CTkFrame(container, fg_color=COLORS["panel"], corner_radius=15, border_width=1,
                              border_color=COLORS["panel_edge"])
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        CTkLabel(left_panel, text="💬 Frequently Asked Questions", font=("Segoe UI Semibold", 24, "bold"),
                 text_color=COLORS["text_main"]).pack(anchor="w", padx=25, pady=(25, 15))

        faq_scroll = CTkScrollableFrame(left_panel, fg_color="transparent", corner_radius=0)
        faq_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        def add_faq(q, a):
            row = CTkFrame(faq_scroll, fg_color=COLORS['panel_alt'], corner_radius=12)
            row.pack(fill="x", padx=15, pady=6)
            CTkLabel(row, text=q, font=("Segoe UI Semibold", 16), text_color=COLORS['text_main'], wraplength=450,
                     justify="left").pack(anchor="w", padx=15, pady=(12, 5))
            CTkLabel(row, text=a, font=("Segoe UI", 14), text_color=COLORS['subtext'], wraplength=450,
                     justify="left").pack(anchor="w", padx=15, pady=(0, 12))

        add_faq("Why is my dashboard data not updating?",
                "Usually happens when sensors are momentarily offline. The app will automatically retry every few seconds.")
        add_faq("Can I use Gaia Sentinel offline?",
                "Yes, you can view cached data. However, real-time updates require an active internet connection.")
        add_faq("What is TDS and why does it matter?",
                "Total Dissolved Solids (TDS) measures dissolved substances in water. Levels below 300 are generally considered excellent for drinking.")
        add_faq("How often should I check the AQI?",
                "The app updates live. We recommend checking frequently if you live in high-traffic or industrial areas.")
        add_faq("What if a node stays offline for too long?",
                "If a node is offline for >24h, try power-cycling the device or verifying Wi-Fi settings in the Settings tab.")
        add_faq("Are drone missions automated?",
                "Drones follow pre-configured safety paths. You can monitor live telemetry and feeds in the Drone Fleet tab.")
        add_faq("How do I reset my password?",
                "Go to the Settings tab or use the 'Forgot Password' link on the login screen.")
        add_faq("Why is the app running slowly?",
                "Ensure your device has sufficient memory. We've optimized data fetching to be as lightweight as possible.")

        # --- RIGHT: TICKET SECTION ---
        right_panel = CTkFrame(container, fg_color=COLORS["panel"], corner_radius=15, border_width=1,
                               border_color=COLORS["panel_edge"])
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        CTkLabel(right_panel, text="🛠️ Create Support Ticket", font=("Segoe UI Semibold", 24, "bold"),
                 text_color=COLORS["text_main"]).pack(anchor="w", padx=25, pady=(25, 15))

        form = CTkFrame(right_panel, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=25)

        CTkLabel(form, text="Subject", font=("Segoe UI Semibold", 15), text_color=COLORS["subtext"]).pack(anchor="w",
                                                                                                          pady=(5, 2))
        subject = CTkEntry(form, placeholder_text="Brief summary of the issue", height=40, corner_radius=10,
                           border_width=1, border_color=COLORS["panel_edge"], font=("Segoe UI", 14),
                           fg_color=COLORS["panel_alt"], text_color=COLORS["text_main"])
        subject.pack(fill="x", pady=(0, 15))

        CTkLabel(form, text="Category", font=("Segoe UI Semibold", 15), text_color=COLORS["subtext"]).pack(anchor="w",
                                                                                                           pady=(0, 2))
        category = CTkOptionMenu(form, values=["Bug", "Feature Request", "UI Issue", "Hardware", "Other"], height=40,
                                 corner_radius=10, fg_color=COLORS["accent"], button_color=COLORS["accent_hover"],
                                 font=("Segoe UI", 14), dropdown_fg_color=COLORS["panel_alt"],
                                 dropdown_text_color=COLORS["text_main"])
        category.set("Bug")
        category.pack(fill="x", pady=(0, 15))

        CTkLabel(form, text="Description", font=("Segoe UI Semibold", 15), text_color=COLORS["subtext"]).pack(
            anchor="w", pady=(0, 2))
        body = CTkTextbox(form, height=180, corner_radius=12, border_width=1, border_color=COLORS["panel_edge"],
                          fg_color=COLORS["panel_alt"], font=("Segoe UI", 14), text_color=COLORS["text_main"])
        body.pack(fill="x", pady=(0, 15))

        # Attachment Area
        attach_frame = CTkFrame(form, fg_color="transparent")
        attach_frame.pack(fill="x", pady=5)
        attach_label = CTkLabel(attach_frame, text="No file attached", font=("Segoe UI", 13),
                                text_color=COLORS["muted"])

        def attach_file():
            p = filedialog.askopenfilename(title="Attach Screenshot", filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
            if p:
                attach_label.configure(text=os.path.basename(p), text_color=COLORS["text_main"])
                attach_label._path = p

        CTkButton(attach_frame, text="📎 Attach File", width=120, height=32, corner_radius=8,
                  fg_color=COLORS["panel_edge"], text_color=COLORS["text_main"], hover_color=COLORS["panel_alt"],
                  font=("Segoe UI", 13), command=attach_file).pack(side="left")
        attach_label.pack(side="left", padx=15)

        # Action Buttons
        btn_row = CTkFrame(right_panel, fg_color="transparent")
        btn_row.pack(fill="x", padx=25, pady=25)

        def save_ticket():
            subj = subject.get().strip()
            desc = body.get("1.0", "end").strip()

            if not subj or not desc:
                messagebox.showwarning("Missing Information", "Please fill in both subject and description.")
                return

            try:
                send_support_ticket(
                    self.user,
                    self.user_email,
                    subj,
                    category.get(),
                    desc,
                    getattr(attach_label, "_path", None)
                )
                subject.delete(0, "end")
                body.delete("1.0", "end")
                if hasattr(attach_label, "_path"):
                    delattr(attach_label, "_path")
                attach_label.configure(text="No file attached", text_color=COLORS["muted"])
                messagebox.showinfo("Success", "Your ticket has been submitted.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send ticket: {str(e)}")

        CTkButton(btn_row, text="Send Ticket", height=45, corner_radius=12, fg_color=COLORS["accent"],
                  hover_color=COLORS["accent_hover"], font=("Segoe UI Semibold", 16), command=save_ticket).pack(
            side="left", fill="x", expand=True, padx=(0, 5))
        CTkButton(btn_row, text="Clear", height=45, corner_radius=12, border_width=2, border_color=COLORS["danger"],
                  fg_color="transparent", text_color=COLORS["danger"], hover_color=THEME["CLEAR_HOVER"],
                  font=("Segoe UI Semibold", 16), command=lambda: [subject.delete(0, "end"), body.delete("1.0", "end"),
                                                                   attach_label.configure(text="No file attached",
                                                                                          text_color=COLORS["muted"]),
                                                                   delattr(attach_label, "_path") if hasattr(
                                                                       attach_label, "_path") else None]).pack(
            side="left", fill="x", expand=True, padx=(5, 0))

    def home_settings_page(self):
        import json, os

        # ---------- SIMPLE SETTINGS PERSISTENCE ----------
        SETTINGS_FILE = "gaia_settings.json"

        default_settings = {
            "username": self.user or "",
            "email": self.user_email or "",
            "twofa": False,
            "notif_enabled": True,
            "notif_node_offline": True,
            "notif_sensor_alert": True,
            "notif_channel": "App Only",
            "quiet_from": "22:00",
            "quiet_to": "07:00",
            "auto_discover": True,
            "auto_ota": False,
            "auto_remove": False,
            "inactive_days": "30",
            "naming_scheme": "Auto",
            "upload_freq": "2s",
            "theme": "Lavender",
            "font_size": "Normal",
            "ui_scale": 1.0,
            "dev_logs": False,
            "live_console": False,
            # new: thresholds
            "pm25_limit": "80",
            "co_limit": "50",
            "tds_limit": "500",
            "temp_limit": "35",
            # new: network/server
            "server_ip": getattr(self, "server_ip", "192.168.1.7"),
            "server_port": str(getattr(self, "server_port", 5050)),
        }

        # load once into self.gaia_settings
        if not hasattr(self, "gaia_settings"):
            if os.path.isfile(SETTINGS_FILE):
                try:
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # merge with defaults to avoid missing keys
                    cfg = default_settings.copy()
                    cfg.update(data)
                    self.gaia_settings = cfg
                except Exception:
                    self.gaia_settings = default_settings.copy()
            else:
                self.gaia_settings = default_settings.copy()
        else:
            # ensure new keys exist if we added defaults later
            for k, v in default_settings.items():
                self.gaia_settings.setdefault(k, v)

        s = self.gaia_settings  # shorthand

        # ---------- KEEP BACKGROUND ----------
        for child in self.main_frame.winfo_children():
            if not id(child) == self.home_back_img_id:
                child.destroy()

        self.main_frame.configure(fg_color=COLORS["bg_secondary"])

        # ---------- TOP WRAPPER ----------
        profile0_frame = CTkFrame(
            self.main_frame,
            width=500,
            fg_color=THEME["PROFILE_BG"],
            corner_radius=15
        )
        profile0_frame.pack(padx=25, pady=15, fill="y", expand=True)

        CTkLabel(
            profile0_frame,
            text="⚙️ SETTINGS",
            font=("tahoma", 32, "bold"),
            text_color=COLORS["text_dark"]
        ).pack(pady=(10, 10))

        # Scrollable content area
        profile1_frame = CTkScrollableFrame(
            profile0_frame,
            height=self.main_frame.winfo_height(),
            width=500,
            fg_color=THEME["PROFILE_BG"],
            corner_radius=15
        )
        profile1_frame.pack(fill="y", expand=True, padx=10, pady=(0, 10))

        # ------------------------------------------------------------------
        # 1️⃣ USER & SECURITY SETTINGS
        # ------------------------------------------------------------------
        user_frame = CTkFrame(profile1_frame, fg_color=COLORS["frame"], corner_radius=15)
        user_frame.pack(padx=20, pady=10, fill="x")
        user_frame.grid_columnconfigure(1, weight=1)

        CTkLabel(
            user_frame,
            text="👤 User & Security",
            font=("tahoma", 22, "bold"),
            text_color=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 5))

        # Username
        CTkLabel(
            user_frame,
            text="Username:",
            font=("tahoma", 15),
            text_color=COLORS["text_dark"]
        ).grid(row=1, column=0, sticky="w", padx=25, pady=4)
        name_entry = CTkEntry(
            user_frame,
            width=260,
            fg_color=THEME["FRAME_BG"],
            border_color=COLORS["border"],
            text_color=COLORS["text_dark"],
            placeholder_text_color=THEME["PLACEHOLDER"]
        )
        name_entry.insert(0, self.user)
        name_entry.grid(row=1, column=1, padx=20, pady=4, sticky="ew")

        # Email
        CTkLabel(
            user_frame,
            text="Email:",
            font=("tahoma", 15),
            text_color=COLORS["text_dark"]
        ).grid(row=2, column=0, sticky="w", padx=25, pady=4)
        email_entry = CTkEntry(
            user_frame,
            width=260,
            fg_color=THEME["FRAME_BG"],
            border_color=COLORS["border"],
            text_color=COLORS["text_dark"],
            placeholder_text_color=THEME["PLACEHOLDER"]
        )
        email_entry.insert(0, self.user_email)
        email_entry.grid(row=2, column=1, padx=20, pady=(4, 10), sticky="ew")

        # 2FA toggle
        twofa_var = BooleanVar(value=bool(s.get("twofa", False)))
        twofa_switch = CTkSwitch(
            user_frame,
            text="Enable Two-Factor Authentication",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"],
            fg_color=COLORS["panel_edge"],
            progress_color=THEME["VELVET_ORCHID"],
            button_color=THEME["VELVET_ORCHID"],
            button_hover_color=THEME["DARK_AMETHYST"],
            variable=twofa_var
        )
        twofa_switch.grid(row=3, column=0, columnspan=2, sticky="w", padx=25, pady=(4, 6))

        # Security buttons row
        sec_btn_row = CTkFrame(user_frame, fg_color="transparent")
        sec_btn_row.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=(8, 12))
        sec_btn_row.grid_columnconfigure((0, 1), weight=1)

        def change_password():
            from tkinter import messagebox, StringVar

            # --------- PICK PARENT (for centering) ----------
            parent = getattr(self, "root", None)
            if parent is None:
                parent = self.root  # fallback

            # ---------- TOPLEVEL WINDOW ----------
            win = CTkToplevel(parent)
            win.title("Change Password")
            win.resizable(False, False)
            win.configure(fg_color=COLORS["bg_primary"])
            win.grab_set()
            win.focus_force()

            # Base size (similar to Add Air Node)
            base_w, base_h = 500, 510
            try:
                win.update_idletasks()
                px = parent.winfo_rootx()
                py = parent.winfo_rooty()
                pw = parent.winfo_width()
                ph = parent.winfo_height()
                x = px + (pw - base_w) // 2
                y = py + (ph - base_h) // 2
                win.geometry(f"{base_w}x{base_h}+{x}+{y}")
            except Exception:
                win.geometry(f"{base_w}x{base_h}")

            # ---------- OUTER CONTAINER (soft bg) ----------
            outer = CTkFrame(
                win,
                fg_color=COLORS["bg_secondary"],
                corner_radius=26,
            )
            outer.pack(fill="both", expand=True, padx=18, pady=18)
            outer.grid_columnconfigure(0, weight=1)
            outer.grid_rowconfigure(2, weight=1)

            # ---------- HEADER: like "ADD AIR NODE" ----------
            header = CTkFrame(outer, corner_radius=999, fg_color="transparent")
            header.grid(row=0, column=0, sticky="ew", pady=(10, 8), padx=5)
            header.grid_columnconfigure(0, weight=1)

            CTkLabel(
                header,
                text="CHANGE PASSWORD", corner_radius=999,
                font=("Segoe UI Semibold", 24, "bold"),
                text_color=COLORS["text_dark"],
            ).grid(row=0, column=0, sticky="n", pady=(0, 4))

            # Small underline line
            CTkFrame(
                header,
                fg_color=COLORS["panel_edge"],
                height=2,
                corner_radius=999,
            ).grid(row=1, column=0, sticky="ew", padx=40, pady=(0, 2))

            # ---------- INNER CARD ----------
            card = CTkFrame(
                outer,
                fg_color=COLORS["panel"],
                corner_radius=24,
                border_width=0)
            card.grid(row=1, column=0, sticky="nsew", padx=28, pady=(10, 18))
            card.grid_columnconfigure(0, weight=1)

            # ---------- VARIABLES ----------
            current_var = StringVar()
            new_var = StringVar()
            confirm_var = StringVar()

            # ------- FIELD: Current password -------
            CTkLabel(
                card,
                text="Current password:",
                font=("Segoe UI Semibold", 12),
                text_color=COLORS["text_dark"],
            ).grid(row=0, column=0, sticky="w", padx=26, pady=(18, 2))

            current_entry = CTkEntry(
                card,
                textvariable=current_var,
                show="*",
                width=260,
                height=34,
                fg_color=COLORS["bg_primary"],
                border_color=COLORS["select"],
                border_width=2,
                corner_radius=14,
                text_color=COLORS["text_dark"],
            )
            current_entry.grid(row=1, column=0, sticky="ew", padx=26, pady=(0, 6))

            # ------- FIELD: New password -------
            CTkLabel(
                card,
                text="New password:",
                font=("Segoe UI Semibold", 12),
                text_color=COLORS["text_dark"],
            ).grid(row=2, column=0, sticky="w", padx=26, pady=(10, 2))

            new_entry = CTkEntry(
                card,
                textvariable=new_var,
                show="*",
                width=260,
                height=34,
                fg_color=COLORS["bg_primary"],
                border_color=COLORS["select"],
                border_width=2,
                corner_radius=14,
                text_color=COLORS["text_dark"],
            )
            new_entry.grid(row=3, column=0, sticky="ew", padx=26, pady=(0, 6))

            # ------- FIELD: Confirm password -------
            CTkLabel(
                card,
                text="Confirm new password:",
                font=("Segoe UI Semibold", 12),
                text_color=COLORS["text_dark"],
            ).grid(row=4, column=0, sticky="w", padx=26, pady=(10, 2))

            confirm_entry = CTkEntry(
                card,
                textvariable=confirm_var,
                show="*",
                width=260,
                height=34,
                fg_color=COLORS["bg_primary"],
                border_color=COLORS["select"],
                border_width=2,
                corner_radius=14,
                text_color=COLORS["text_dark"],
            )
            confirm_entry.grid(row=5, column=0, sticky="ew", padx=26, pady=(0, 8))

            # ---------- Tip (small text) ----------
            CTkLabel(
                card,
                text="Use at least 8 characters with letters, numbers and symbols.",
                font=("Segoe UI", 10),
                text_color=COLORS["muted"],
                wraplength=320,
                justify="center",
            ).grid(row=6, column=0, sticky="n", padx=26, pady=(0, 4))

            # ---------- BUTTON ROW ----------
            btn_row = CTkFrame(card, fg_color="transparent")
            btn_row.grid(row=7, column=0, sticky="n", pady=(12, 4))
            btn_row.grid_columnconfigure(0, weight=1)
            btn_row.grid_columnconfigure(1, weight=1)

            def do_cancel():
                win.grab_release()
                win.destroy()

            def do_save():
                cur = current_var.get().strip()
                new = new_var.get().strip()
                conf = confirm_var.get().strip()

                if not cur or not new or not conf:
                    messagebox.showwarning("Missing information", "Please fill in all fields.")
                    return

                if len(new) < 8:
                    messagebox.showwarning(
                        "Weak password",
                        "Password should be at least 8 characters long.",
                    )
                    return

                if new != conf:
                    messagebox.showerror("Mismatch", "New password and confirmation do not match.")
                    return

                # ---- DB update section (adapt to your setup) ----
                pass

            # Main purple button (like CONNECT)
            save_btn = CTkButton(
                btn_row,
                text="SAVE PASSWORD",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color="white",
                corner_radius=18,
                height=38,
                font=("Segoe UI Semibold", 13, "bold"),
                command=do_save,
            )
            save_btn.grid(row=0, column=0, columnspan=2, padx=60, sticky="ew")

            # Subtle cancel / info link (like "forgot password")
            def on_cancel_link(_evt=None):
                do_cancel()

            cancel_link = CTkLabel(
                card,
                text="cancel and go back",
                font=("Segoe UI", 12, "underline"),
                text_color=COLORS["muted"],
                cursor="hand2",
            )
            cancel_link.grid(row=8, column=0, pady=(2, 10))
            cancel_link.bind("<Button-1>", on_cancel_link)

            # Focus first field
            current_entry.focus_set()

        def logout_everywhere():
            # TODO: invalidate tokens/sessions globally
            messagebox.showinfo("Logged Out", "All active sessions have been logged out.")

        CTkButton(
            sec_btn_row,
            text="Change Password",
            fg_color=THEME["VELVET_ORCHID"],
            hover_color=THEME["DARK_AMETHYST"],
            text_color="white",
            height=32,
            corner_radius=10,
            font=('tahoma', 14),
            command=change_password
        ).grid(row=0, column=0, padx=5, pady=4, sticky="ew")

        CTkButton(
            sec_btn_row,
            text="Logout Everywhere",
            fg_color=THEME["DANGER"],
            hover_color=THEME["DANGER_HOVER"],
            text_color="white",
            height=32,
            corner_radius=10,
            font=('tahoma', 14),
            command=logout_everywhere
        ).grid(row=0, column=1, padx=5, pady=4, sticky="ew")

        # ------------------------------------------------------------------
        # 2️⃣ NOTIFICATION & ALERTS
        # ------------------------------------------------------------------
        notif_frame = CTkFrame(profile1_frame, fg_color=COLORS["frame"], corner_radius=15)
        notif_frame.pack(padx=20, pady=10, fill="x")
        notif_frame.grid_columnconfigure(1, weight=1)

        CTkLabel(
            notif_frame,
            text="🔔 Notifications & Alerts",
            font=("tahoma", 22, "bold"),
            text_color=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 6))

        # Master notifications
        notif_var = BooleanVar(value=bool(s.get("notif_enabled", True)))
        CTkSwitch(
            notif_frame,
            text="Enable notifications",
            font=("tahoma", 15),
            text_color=COLORS["text_dark"],
            fg_color=COLORS["panel_edge"],
            progress_color=THEME["VELVET_ORCHID"],
            button_color=THEME["VELVET_ORCHID"],
            button_hover_color=THEME["DARK_AMETHYST"],
            variable=notif_var
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=25, pady=(4, 2))

        node_offline_var = BooleanVar(value=bool(s.get("notif_node_offline", True)))
        CTkSwitch(
            notif_frame,
            text="Alert when a node goes offline",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"],
            fg_color=COLORS["panel_edge"],
            progress_color=THEME["VELVET_ORCHID"],
            button_color=THEME["VELVET_ORCHID"],
            button_hover_color=THEME["DARK_AMETHYST"],
            variable=node_offline_var
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=25, pady=2)

        sensor_alert_var = BooleanVar(value=bool(s.get("notif_sensor_alert", True)))
        CTkSwitch(
            notif_frame,
            text="Alert when sensor values exceed safe limits",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"],
            fg_color=COLORS["panel_edge"],
            progress_color=THEME["VELVET_ORCHID"],
            button_color=THEME["VELVET_ORCHID"],
            button_hover_color=THEME["DARK_AMETHYST"],
            variable=sensor_alert_var
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=25, pady=(2, 8))

        # Channel
        CTkLabel(
            notif_frame,
            text="Alert channel:",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"]
        ).grid(row=4, column=0, sticky="w", padx=25, pady=(4, 2))
        channel_var = StringVar(value=s.get("notif_channel", "App Only"))
        CTkOptionMenu(
            notif_frame,
            variable=channel_var,
            values=["App Only", "Email", "App + Email"],
            fg_color=THEME["VELVET_ORCHID"],
            button_color=THEME["DARK_AMETHYST"],
            dropdown_fg_color=COLORS["panel_alt"],
            dropdown_text_color=COLORS["text_dark"],
            dropdown_hover_color=COLORS["accent_hover"],
            text_color="white",
            corner_radius=10
        ).grid(row=4, column=1, padx=20, pady=(4, 2), sticky="ew")

        # Quiet hours
        CTkLabel(
            notif_frame,
            text="Quiet hours (no alerts):",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"]
        ).grid(row=5, column=0, sticky="w", padx=25, pady=(6, 2))

        quiet_from = CTkEntry(
            notif_frame,
            width=80,
            fg_color=THEME["FRAME_BG"],
            border_color=COLORS["border"],
            text_color=COLORS["text_dark"],
            placeholder_text="22:00",
            placeholder_text_color=THEME["PLACEHOLDER"]
        )
        quiet_from.insert(0, s.get("quiet_from", "22:00"))
        quiet_from.grid(row=5, column=1, sticky="w", padx=(20, 5), pady=(6, 2))

        quiet_to = CTkEntry(
            notif_frame,
            width=80,
            fg_color=THEME["FRAME_BG"],
            border_color=COLORS["border"],
            text_color=COLORS["text_dark"],
            placeholder_text="07:00",
            placeholder_text_color=THEME["PLACEHOLDER"]
        )
        quiet_to.insert(0, s.get("quiet_to", "07:00"))
        quiet_to.grid(row=5, column=1, sticky="w", padx=(120, 5), pady=(6, 2))

        # ------------------------------------------------------------------
        # 3️⃣ NODE MANAGEMENT PREFERENCES
        # ------------------------------------------------------------------
        node_frame = CTkFrame(profile1_frame, fg_color=COLORS["frame"], corner_radius=15)
        node_frame.pack(padx=20, pady=10, fill="x")
        node_frame.grid_columnconfigure(1, weight=1)

        CTkLabel(
            node_frame,
            text="🌐 Node Management",
            font=("tahoma", 22, "bold"),
            text_color=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 6))

        auto_discover_var = BooleanVar(value=bool(s.get("auto_discover", True)))
        CTkSwitch(
            node_frame,
            text="Auto-discover new nodes",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"],
            fg_color=COLORS["panel_edge"],
            progress_color=THEME["VELVET_ORCHID"],
            button_color=THEME["VELVET_ORCHID"],
            button_hover_color=THEME["DARK_AMETHYST"],
            variable=auto_discover_var
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=25, pady=2)

        auto_ota_var = BooleanVar(value=bool(s.get("auto_ota", False)))
        CTkSwitch(
            node_frame,
            text="Auto-update firmware (OTA)",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"],
            fg_color=COLORS["panel_edge"],
            progress_color=THEME["VELVET_ORCHID"],
            button_color=THEME["VELVET_ORCHID"],
            button_hover_color=THEME["DARK_AMETHYST"],
            variable=auto_ota_var
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=25, pady=2)

        auto_remove_var = BooleanVar(value=bool(s.get("auto_remove", False)))
        CTkSwitch(
            node_frame,
            text="Auto-remove inactive nodes",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"],
            fg_color=COLORS["panel_edge"],
            progress_color=THEME["VELVET_ORCHID"],
            button_color=THEME["VELVET_ORCHID"],
            button_hover_color=THEME["DARK_AMETHYST"],
            variable=auto_remove_var
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=25, pady=(2, 2))

        CTkLabel(
            node_frame,
            text="After days inactive:",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"]
        ).grid(row=4, column=0, sticky="w", padx=25, pady=(4, 2))
        inactive_days_var = StringVar(value=s.get("inactive_days", "30"))
        inactive_days_entry = CTkEntry(
            node_frame,
            width=80,
            textvariable=inactive_days_var,
            fg_color=THEME["FRAME_BG"],
            border_color=COLORS["border"],
            text_color=COLORS["text_dark"],
            placeholder_text_color=THEME["PLACEHOLDER"]
        )
        inactive_days_entry.grid(row=4, column=1, padx=20, pady=(4, 2), sticky="w")

        CTkLabel(
            node_frame,
            text="Default naming scheme:",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"]
        ).grid(row=5, column=0, sticky="w", padx=25, pady=(6, 2))
        naming_var = StringVar(value=s.get("naming_scheme", "Auto"))
        CTkOptionMenu(
            node_frame,
            variable=naming_var,
            values=["Auto", "Custom", "Location based"],
            fg_color=THEME["VELVET_ORCHID"],
            button_color=THEME["DARK_AMETHYST"],
            dropdown_fg_color=COLORS["panel_alt"],
            dropdown_text_color=COLORS["text_dark"],
            dropdown_hover_color=COLORS["accent_hover"],
            text_color="white",
            corner_radius=10
        ).grid(row=5, column=1, padx=20, pady=(6, 2), sticky="ew")

        CTkLabel(
            node_frame,
            text="Data upload frequency:",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"]
        ).grid(row=6, column=0, sticky="w", padx=25, pady=(6, 2))
        upload_var = StringVar(value=s.get("upload_freq", "2s"))
        CTkOptionMenu(
            node_frame,
            variable=upload_var,
            values=["1s", "2s", "5s", "10s"],
            fg_color=THEME["VELVET_ORCHID"],
            button_color=THEME["DARK_AMETHYST"],
            dropdown_fg_color=COLORS["panel_alt"],
            dropdown_text_color=COLORS["text_dark"],
            dropdown_hover_color=COLORS["accent_hover"],
            text_color="white",
            corner_radius=10
        ).grid(row=6, column=1, padx=20, pady=(6, 10), sticky="ew")

        # ------------------------------------------------------------------
        # 3.5️⃣ SENSOR ALERT THRESHOLDS (NEW)
        # ------------------------------------------------------------------
        thresh_frame = CTkFrame(profile1_frame, fg_color=COLORS["frame"], corner_radius=15)
        thresh_frame.pack(padx=20, pady=10, fill="x")
        thresh_frame.grid_columnconfigure(1, weight=1)

        CTkLabel(
            thresh_frame,
            text="📊 Sensor Alert Thresholds",
            font=("tahoma", 22, "bold"),
            text_color=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 6))

        def mk_threshold(row, label, key, unit, default_val):
            CTkLabel(
                thresh_frame,
                text=f"{label}:",
                font=("tahoma", 14),
                text_color=COLORS["text_dark"]
            ).grid(row=row, column=0, sticky="w", padx=25, pady=(4, 2))
            entry = CTkEntry(
                thresh_frame,
                width=100,
                fg_color=THEME["FRAME_BG"],
                border_color=COLORS["border"],
                text_color=COLORS["text_dark"],
                placeholder_text_color=THEME["PLACEHOLDER"]
            )
            entry.insert(0, s.get(key, default_val))
            entry.grid(row=row, column=1, sticky="w", padx=20, pady=(4, 2))
            CTkLabel(
                thresh_frame,
                text=unit,
                font=("tahoma", 13),
                text_color=COLORS["muted"]
            ).grid(row=row, column=1, sticky="w", padx=(140, 0), pady=(4, 2))
            return entry

        pm25_entry = mk_threshold(1, "PM2.5 limit", "pm25_limit", "µg/m³", "80")
        co_entry = mk_threshold(2, "CO (MQ7) limit", "co_limit", "ppm", "50")
        tds_entry = mk_threshold(3, "TDS limit", "tds_limit", "ppm", "500")
        ttemp_entry = mk_threshold(4, "Temperature limit", "temp_limit", "°C", "35")

        # ------------------------------------------------------------------
        # 4️⃣ APPEARANCE & THEME
        # ------------------------------------------------------------------
        appearance_frame = CTkFrame(profile1_frame, fg_color=COLORS["frame"], corner_radius=15)
        appearance_frame.pack(padx=20, pady=10, fill="x")
        appearance_frame.grid_columnconfigure(1, weight=1)

        CTkLabel(
            appearance_frame,
            text="🎨 Appearance & Theme",
            font=("tahoma", 22, "bold"),
            text_color=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 6))

        theme_var = StringVar(value=s.get("theme", "Lavender"))

        def apply_theme_changes(choice: str):
            if choice not in ("Lavender", "Pink", "Green", "Blue", "Orange"):
                return

            # ---------- 1) SAVE SETTINGS ----------
            def save_settings():
                s["theme"] = choice
                with open("gaia_settings.json", "w") as f:
                    import json
                    json.dump(s, f, indent=4)

            # ---------- 2) RESTART APP ----------
            def restart_app():
                import sys, os, subprocess

                # Close the current window
                popup.destroy()

                # Relaunch the same script again as a new process
                python = sys.executable
                script = sys.argv[0]

                try:
                    subprocess.Popen([python, script] + sys.argv[1:])
                    sys.exit(0)  # fully exit current instance
                except Exception as e:
                    print("Restart failed:", e)

            # ---------- 3) BUTTON ACTION HANDLERS ----------
            def do_save_and_restart():
                save_settings()
                popup.destroy()
                restart_app()

            def do_save_without_restart():
                save_settings()
                popup.destroy()

            def do_cancel():
                popup.destroy()

            # ---------- 4) POPUP UI ----------
            popup = CTkToplevel()
            popup.title("Gaia Sentinel - Apply Theme")
            popup.geometry("510x160")
            popup.resizable(False, False)
            popup.grab_set()

            popup.configure(fg_color=COLORS["panel"])

            CTkLabel(
                popup,
                text=f"Apply theme: {choice}?",
                font=("Segoe UI", 18, "bold"),
                text_color=COLORS["text_dark"]
            ).pack(pady=(18, 5))

            CTkLabel(
                popup,
                text="The interface must restart to fully apply the theme.\nWould you like to restart now?",
                font=("Segoe UI", 13),
                text_color=COLORS["muted"],
                justify="center"
            ).pack(pady=(0, 10))

            # BUTTON ROW
            btn_frame = CTkFrame(popup, fg_color="transparent")
            btn_frame.pack(pady=(5, 10))

            CTkButton(
                btn_frame,
                text="💾 Save & Restart",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color="white",
                command=do_save_and_restart,
                width=150,
                corner_radius=10
            ).grid(row=0, column=0, padx=5)

            CTkButton(
                btn_frame,
                text="✔ Save (Restart Later)",
                fg_color=COLORS["panel_alt"],
                hover_color=COLORS["warn_hover"],
                text_color=COLORS["text_dark"],
                command=do_save_without_restart,
                width=150,
                corner_radius=10
            ).grid(row=0, column=1, padx=5)

            CTkButton(
                btn_frame,
                text="✖ Cancel",
                fg_color=COLORS["danger"],
                hover_color=COLORS["danger_hover"],
                text_color="white",
                command=do_cancel,
                width=120,
                corner_radius=10
            ).grid(row=0, column=2, columnspan=1, pady=12, padx=5)

        CTkLabel(
            appearance_frame,
            text="Theme:",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"]
        ).grid(row=1, column=0, sticky="w", padx=25, pady=(4, 2))
        theme_menu = CTkOptionMenu(
            appearance_frame,
            variable=theme_var,
            values=['Lavender', 'Pink', "Green", 'Blue', "Orange"],
            command=apply_theme_changes,
            fg_color=THEME["VELVET_ORCHID"],
            button_color=THEME["DARK_AMETHYST"],
            dropdown_fg_color=COLORS["panel_alt"],
            dropdown_text_color=COLORS["text_dark"],
            dropdown_hover_color=COLORS["accent_hover"],
            text_color="white",
            corner_radius=10
        )
        theme_menu.grid(row=1, column=1, padx=20, pady=(4, 2), sticky="ew")

        CTkLabel(
            appearance_frame,
            text="Font size:",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"]
        ).grid(row=3, column=0, sticky="w", padx=25, pady=(6, 2))
        font_size_var = StringVar(value=s.get("font_size", "Normal"))
        CTkOptionMenu(
            appearance_frame,
            variable=font_size_var,
            values=["Small", "Normal", "Large"],
            fg_color=THEME["VELVET_ORCHID"],
            button_color=THEME["DARK_AMETHYST"],
            dropdown_fg_color=COLORS["panel_alt"],
            dropdown_text_color=COLORS["text_dark"],
            dropdown_hover_color=COLORS["accent_hover"],
            text_color="white",
            corner_radius=10
        ).grid(row=3, column=1, padx=20, pady=(6, 2), sticky="ew")

        CTkLabel(
            appearance_frame,
            text="UI scale:",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"]
        ).grid(row=4, column=0, sticky="w", padx=25, pady=(6, 2))
        scale_var = DoubleVar(value=float(s.get("ui_scale", 1.0)))

        def on_scale_change(v):
            try:
                val = float(v)
                set_widget_scaling(val)
            except Exception:
                pass

        CTkSlider(
            appearance_frame,
            from_=0.8,
            to=1.4,
            number_of_steps=6,
            variable=scale_var,
            fg_color=COLORS["panel_edge"],
            progress_color=THEME["VELVET_ORCHID"],
            button_color=THEME["DARK_AMETHYST"],
            command=on_scale_change,
            height=16
        ).grid(row=4, column=1, padx=20, pady=(6, 10), sticky="ew")

        # ------------------------------------------------------------------
        # 5️⃣ SYSTEM & DATA
        # ------------------------------------------------------------------
        system_frame = CTkFrame(profile1_frame, fg_color=COLORS["frame"], corner_radius=15)
        system_frame.pack(padx=20, pady=10, fill="x")
        system_frame.grid_columnconfigure((0, 1), weight=1)

        CTkLabel(
            system_frame,
            text="🖥️ System & Data",
            font=("tahoma", 22, "bold"),
            text_color=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 6))

        def backup_db():
            # TODO hook to actual backup function
            messagebox.showinfo("Backup", "Database backup started (stub).")

        def restore_db():
            messagebox.showinfo("Restore", "Restore process (stub).")

        def export_history():
            messagebox.showinfo("Export", "Sensor history export started (stub).")

        def clear_cache():
            messagebox.showinfo("Cache", "Cached data cleared (stub).")

        def factory_reset():
            if messagebox.askyesno("Factory Reset", "This will reset dashboard preferences. Continue?"):
                messagebox.showinfo("Factory Reset", "Dashboard reset (stub).")

        CTkButton(
            system_frame, text="Backup database",
            fg_color=THEME["VELVET_ORCHID"],
            hover_color=THEME["DARK_AMETHYST"],
            text_color="white",
            corner_radius=10,
            height=32,
            font=('tahoma', 14),
            command=backup_db
        ).grid(row=1, column=0, padx=15, pady=4, sticky="ew")

        CTkButton(
            system_frame, text="Restore backup",
            fg_color=THEME["VELVET_ORCHID"],
            hover_color=THEME["DARK_AMETHYST"],
            text_color="white",
            corner_radius=10,
            height=32,
            font=('tahoma', 14),
            command=restore_db
        ).grid(row=1, column=1, padx=15, pady=4, sticky="ew")

        CTkButton(
            system_frame, text="Export sensor history",
            fg_color=THEME["VELVET_ORCHID"],
            hover_color=THEME["DARK_AMETHYST"],
            text_color="white",
            corner_radius=10,
            height=32,
            font=('tahoma', 14),
            command=export_history
        ).grid(row=2, column=0, padx=15, pady=4, sticky="ew")

        CTkButton(
            system_frame, text="Clear cached data",
            fg_color=THEME["FRAME_BG"],
            hover_color=THEME["CLEAR_HOVER"],
            text_color=COLORS["text_dark"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
            height=32,
            font=('tahoma', 14),
            command=clear_cache
        ).grid(row=2, column=1, padx=15, pady=4, sticky="ew")

        CTkButton(
            system_frame, text="Factory reset dashboard",
            fg_color=THEME["DANGER"],
            hover_color=THEME["DANGER_HOVER"],
            text_color="white",
            corner_radius=10,
            height=32,
            font=('tahoma', 14, "bold"),
            command=factory_reset
        ).grid(row=3, column=0, columnspan=2, padx=15, pady=(8, 10), sticky="ew")

        # ------------------------------------------------------------------
        # 5.5️⃣ NETWORK / SERVER SETTINGS (NEW)
        # ------------------------------------------------------------------
        net_frame = CTkFrame(profile1_frame, fg_color=COLORS["frame"], corner_radius=15)
        net_frame.pack(padx=20, pady=10, fill="x")
        net_frame.grid_columnconfigure(1, weight=1)

        CTkLabel(
            net_frame,
            text="🌐 Network & Server",
            font=("tahoma", 22, "bold"),
            text_color=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 6))

        CTkLabel(
            net_frame,
            text="Server IP:",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"]
        ).grid(row=1, column=0, sticky="w", padx=25, pady=(4, 2))
        server_ip_entry = CTkEntry(
            net_frame,
            width=140,
            fg_color=THEME["FRAME_BG"],
            border_color=COLORS["border"],
            text_color=COLORS["text_dark"],
            placeholder_text_color=THEME["PLACEHOLDER"]
        )
        server_ip_entry.insert(0, s.get("server_ip", "192.168.1.7"))
        server_ip_entry.grid(row=1, column=1, sticky="w", padx=20, pady=(4, 2))

        CTkLabel(
            net_frame,
            text="Server port:",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"]
        ).grid(row=2, column=0, sticky="w", padx=25, pady=(4, 2))
        server_port_entry = CTkEntry(
            net_frame,
            width=80,
            fg_color=THEME["FRAME_BG"],
            border_color=COLORS["border"],
            text_color=COLORS["text_dark"],
            placeholder_text_color=THEME["PLACEHOLDER"]
        )
        server_port_entry.insert(0, s.get("server_port", "5050"))
        server_port_entry.grid(row=2, column=1, sticky="w", padx=20, pady=(4, 2))

        # ------------------------------------------------------------------
        # 6️⃣ DEVELOPER & DIAGNOSTICS
        # ------------------------------------------------------------------
        dev_frame = CTkFrame(profile1_frame, fg_color=COLORS["frame"], corner_radius=15)
        dev_frame.pack(padx=20, pady=10, fill="x")
        dev_frame.grid_columnconfigure(0, weight=1)
        dev_frame.grid_columnconfigure(1, weight=1)

        CTkLabel(
            dev_frame,
            text="🧪 Developer & Diagnostics",
            font=("tahoma", 22, "bold"),
            text_color=COLORS["text_dark"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 6))

        dev_logs_var = BooleanVar(value=bool(s.get("dev_logs", False)))
        CTkSwitch(
            dev_frame,
            text="Enable developer logs",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"],
            fg_color=COLORS["panel_edge"],
            progress_color=THEME["VELVET_ORCHID"],
            button_color=THEME["VELVET_ORCHID"],
            button_hover_color=THEME["DARK_AMETHYST"],
            variable=dev_logs_var
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=25, pady=2)

        live_console_var = BooleanVar(value=bool(s.get("live_console", False)))
        CTkSwitch(
            dev_frame,
            text="Show live server console",
            font=("tahoma", 14),
            text_color=COLORS["text_dark"],
            fg_color=COLORS["panel_edge"],
            progress_color=THEME["VELVET_ORCHID"],
            button_color=THEME["VELVET_ORCHID"],
            button_hover_color=THEME["DARK_AMETHYST"],
            variable=live_console_var
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=25, pady=2)

        def test_connection():
            # stub: here you could try a socket connection using server_ip_entry/port
            messagebox.showinfo("Connection Test", "Server connection looks good (stub).")

        def open_fw_tool():
            try:
                program_esp_gui.ProgramESP8266Window(self.root, "AIR")
            except Exception:
                messagebox.showinfo("Firmware Tool", "Firmware tool not hooked up yet.")

        CTkButton(
            dev_frame, text="Test server connection",
            fg_color=THEME["VELVET_ORCHID"],
            hover_color=THEME["DARK_AMETHYST"],
            text_color="white",
            corner_radius=10,
            height=32,
            font=('tahoma', 14),
            command=test_connection
        ).grid(row=3, column=0, padx=15, pady=(8, 10), sticky="ew")

        CTkButton(
            dev_frame, text="Open firmware update tool",
            fg_color=THEME["FRAME_BG"],
            hover_color=THEME["CLEAR_HOVER"],
            text_color=COLORS["text_dark"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=10,
            height=32,
            font=('tahoma', 14),
            command=open_fw_tool
        ).grid(row=3, column=1, padx=15, pady=(8, 10), sticky="ew")

        # ------------------------------------------------------------------
        # ACTION BUTTONS (BOTTOM)
        # ------------------------------------------------------------------
        button_frame = CTkFrame(profile1_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        def save_settings():
            # collect all values into self.gaia_settings
            self.gaia_settings["username"] = name_entry.get().strip()
            self.gaia_settings["email"] = email_entry.get().strip()
            self.gaia_settings["twofa"] = bool(twofa_var.get())
            self.gaia_settings["notif_enabled"] = bool(notif_var.get())
            self.gaia_settings["notif_node_offline"] = bool(node_offline_var.get())
            self.gaia_settings["notif_sensor_alert"] = bool(sensor_alert_var.get())
            self.gaia_settings["notif_channel"] = channel_var.get()
            self.gaia_settings["quiet_from"] = quiet_from.get().strip() or "22:00"
            self.gaia_settings["quiet_to"] = quiet_to.get().strip() or "07:00"
            self.gaia_settings["auto_discover"] = bool(auto_discover_var.get())
            self.gaia_settings["auto_ota"] = bool(auto_ota_var.get())
            self.gaia_settings["auto_remove"] = bool(auto_remove_var.get())
            self.gaia_settings["inactive_days"] = inactive_days_var.get().strip() or "30"
            self.gaia_settings["naming_scheme"] = naming_var.get()
            self.gaia_settings["upload_freq"] = upload_var.get()
            self.gaia_settings["theme"] = theme_var.get()
            self.gaia_settings["font_size"] = font_size_var.get()
            self.gaia_settings["ui_scale"] = float(scale_var.get())
            self.gaia_settings["dev_logs"] = bool(dev_logs_var.get())
            self.gaia_settings["live_console"] = bool(live_console_var.get())
            self.gaia_settings["pm25_limit"] = pm25_entry.get().strip() or "80"
            self.gaia_settings["co_limit"] = co_entry.get().strip() or "50"
            self.gaia_settings["tds_limit"] = tds_entry.get().strip() or "500"
            self.gaia_settings["temp_limit"] = ttemp_entry.get().strip() or "35"
            self.gaia_settings["server_ip"] = server_ip_entry.get().strip() or "192.168.1.7"
            self.gaia_settings["server_port"] = server_port_entry.get().strip() or "5050"

            # update easy-access attributes
            self.user = self.gaia_settings["username"]
            self.user_email = self.gaia_settings["email"]
            self.server_ip = self.gaia_settings["server_ip"]
            try:
                self.server_port = int(self.gaia_settings["server_port"])
            except ValueError:
                self.server_port = 5050

            # write JSON
            try:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.gaia_settings, f, indent=2)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}")
                return

            messagebox.showinfo("✅ Saved", "Settings saved for Gaia Sentinel!")

        def reset_defaults():
            # reset to defaults and re-open page
            self.gaia_settings = default_settings.copy()
            try:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.gaia_settings, f, indent=2)
            except Exception:
                pass
            messagebox.showinfo("Reset", "Settings have been reset to default values.")
            # re-render settings UI
            self.home_settings_page()

        CTkButton(
            button_frame,
            text="Save Changes",
            fg_color=THEME["VELVET_ORCHID"],
            hover_color=THEME["DARK_AMETHYST"],
            height=34,
            font=('tahoma', 16, "bold"),
            text_color='white',
            width=220,
            corner_radius=12,
            command=save_settings
        ).grid(row=0, column=0, padx=10)

        CTkButton(
            button_frame,
            text="Reset Defaults",
            text_color='white',
            fg_color=THEME["VELVET_ORCHID"],
            hover_color=THEME["DARK_AMETHYST"],
            height=34,
            font=('tahoma', 16),
            width=220,
            corner_radius=12,
            command=reset_defaults
        ).grid(row=0, column=1, padx=10)

    def no_internet_page(self):
        for child in self.root.winfo_children():
            child.destroy()

        self.root.title("Gaia Sentinel - Offline")

        main_frame = CTkFrame(self.root, fg_color=THEME["NO_INTERNET_BG"], corner_radius=20)
        main_frame.pack(expand=True, fill=None, anchor="center", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        try:
            img = CTkImage(light_image=Image.open("no_wifi.png"), size=(190, 190))
            icon_lbl = CTkLabel(main_frame, image=img, text="")
            icon_lbl.grid(row=0, column=0, pady=(50, 20))
        except:
            CTkLabel(main_frame, text="📡", font=("Segoe UI", 95)).grid(row=0, column=0, pady=(50, 20))

        CTkLabel(main_frame, text="No Internet Connection", font=("Segoe UI Semibold", 34, "bold"), text_color="black").grid(row=1, column=0, pady=(5, 10), padx=15)

        CTkLabel(main_frame, text='No internet connection detected.', font=("Segoe UI", 18), wraplength=550, justify="center", text_color='black').grid(row=2, column=0, pady=(0, 40), padx=15)

        def retry_now():
            try:
                ok = is_online()
                if ok:
                    self.home_page()
                else:
                    self.no_internet_page()
            except:
                self.no_internet_page()

        CTkButton(main_frame, text="Retry Connection", fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color="white", height=55, width=220, corner_radius=14, font=("Segoe UI", 18, "bold"), command=retry_now).grid(row=3, column=0, pady=(5, 35))

        CTkLabel(main_frame, text="© 2025 Gaia Sentinel. Built for those who protect nature.", font=("Segoe UI", 15), text_color='black').grid(row=4, column=0, padx=15, pady=(10, 20))

    def otp_page(self, username=None, email=None, back_page=None, password_sin=None):
        try:
            self.root.state("zoomed")
        except Exception:
            self.root.geometry(
                f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0"
            )

        self.root.title("Gaia Sentinel - OTP Verification")

        for child in self.root.winfo_children():
            child.destroy()

        # --------- HELPERS (SAME LOGIC) ---------
        def generate_otp(length=6):
            return ''.join(random.choice('1234567890') for _ in range(length))

        def generate_captcha(length=5):
            chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
            return ''.join(random.choice(chars) for _ in range(length))

        def refresh_captcha():
            nonlocal captcha_value
            captcha_value = generate_captcha()
            captcha_label.configure(text=captcha_value)

        def resend_otp():
            nonlocal otp
            otp = generate_otp()
            print(f"Resent OTP: {otp}")
            try:
                send_mail_for_otp(username, email, otp)
            except Exception:
                print("Failed to resend OTP via send_mail_for_otp")

        def back_to_previous_page():
            for c in self.root.winfo_children():
                c.destroy()
            if back_page == 'log':
                self.login_page()
            elif back_page == 'sin':
                self.signup_page()

        def check_otp():
            otp_v = otp_entry.get().strip()
            captcha = ent_captcha.get().strip()

            if not captcha or not otp_v:
                messagebox.showwarning("Error", "All fields are required.")
                return

            if otp_v != otp:
                messagebox.showerror("Error", "Invalid OTP")
                return

            if captcha != captcha_value:
                messagebox.showerror("Error", "Invalid Captcha")
                return

            # success path unchanged
            if back_page == 'sin':
                try:
                    ok = upload_user_details(username, email, password_sin)
                    if ok:
                        messagebox.showinfo("Success", "Successful!!!")
                        self.user = username
                        self.user_email = email
                        self.home_page()
                    else:
                        messagebox.showwarning("Warning", "Failed to save user to DB.")
                except Exception as e:
                    print("upload_user_details error:", e)
                    messagebox.showwarning("Warning", "Error while saving user to DB.")

            elif back_page == 'log':
                print(username, email)
                self.user = username
                self.user_email = email
                self.home_page()
                messagebox.showinfo("Success", "Successful!!!")

        # -------- GENERATE & SEND OTP (SAME BEHAVIOUR) --------
        otp = generate_otp()
        print(otp)
        try:
            send_mail_for_otp(username, email, otp)
        except Exception:
            print("Failed to send initial OTP via send_mail_for_otp")

        captcha_value = generate_captcha()

        # --------- LAYOUT (MATCHING LOGIN STYLE) ---------
        self.root.configure(fg_color=COLORS["bg_primary"])

        shell = CTkFrame(self.root, fg_color=COLORS["bg_primary"], corner_radius=0)
        shell.pack(fill="both", expand=True)

        # big rounded container
        main_shadow = CTkFrame(shell, fg_color=COLORS["shadow"], corner_radius=32)
        main_shadow.place(relx=0.5, rely=0.5, anchor="center",
                          relwidth=0.9, relheight=0.82)

        main_panel = CTkFrame(
            shell,
            fg_color=COLORS["panel"],
            corner_radius=28,
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        main_panel.place(relx=0.5, rely=0.5, anchor="center",
                         relwidth=0.9, relheight=0.82)

        main_panel.grid_rowconfigure(0, weight=1)
        main_panel.grid_columnconfigure(0, weight=3)  # left hero
        main_panel.grid_columnconfigure(1, weight=2)  # right card

        # ---------- LEFT HERO (TEXT) ----------
        hero = CTkFrame(main_panel, fg_color="transparent")
        hero.grid(row=0, column=0, sticky="nsew", padx=(26, 14), pady=24)
        hero.grid_rowconfigure(3, weight=1)

        # little banner like login
        banner = CTkFrame(hero, fg_color=COLORS["accent1"], corner_radius=24)
        banner.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        banner.grid_columnconfigure(0, weight=1)

        CTkLabel(
            banner,
            text="GAIA SENTINEL",
            font=("Segoe UI Semibold", 18, "bold"),
            text_color=COLORS["text_main"],
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(12, 0))

        CTkLabel(
            banner,
            text="Environmental Intelligence • Secured Access",
            font=("Segoe UI", 11),
            text_color=COLORS["text_subtle"],
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 12))

        # main hero headline
        CTkLabel(
            hero,
            text="Verify your access.\nStay in control.",
            font=("Segoe UI Semibold", 30, "bold"),
            text_color=COLORS["text"],
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 10))

        CTkLabel(
            hero,
            text="Enter the one‑time passcode we sent to your email to keep your "
                 "Gaia Sentinel workspace secure.",
            font=("Segoe UI", 12),
            text_color=COLORS["subtext"],
            wraplength=520,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(0, 12))

        bullets = CTkFrame(hero, fg_color="transparent")
        bullets.grid(row=3, column=0, sticky="nw")

        def bullet(text):
            r = bullets.grid_size()[1]
            CTkLabel(
                bullets,
                text="●",
                font=("Segoe UI", 11, "bold"),
                text_color=COLORS["accent3"],
            ).grid(row=r, column=0, sticky="ne", padx=(0, 6), pady=2)
            CTkLabel(
                bullets,
                text=text,
                font=("Segoe UI", 11),
                text_color=COLORS["text"],
                wraplength=420,
                justify="left",
            ).grid(row=r, column=1, sticky="w", pady=2)

        bullet("6‑digit OTP sent to your registered email address.")
        bullet("CAPTCHA check prevents automated login attempts.")
        bullet("Designed for guardians of forests, coasts and cities.")

        CTkLabel(
            hero,
            text=f"© {datetime.datetime.now().year} Gaia Sentinel • Built for those who protect nature",
            font=("Segoe UI", 10),
            text_color=COLORS["subtext"],
        ).grid(row=4, column=0, sticky="sw", pady=(18, 0))

        # ---------- RIGHT OTP CARD ----------
        form_wrap = CTkFrame(main_panel, fg_color="transparent")
        form_wrap.grid(row=0, column=1, sticky="nsew", padx=(10, 26), pady=24)
        form_wrap.grid_rowconfigure(0, weight=1)
        form_wrap.grid_columnconfigure(0, weight=1)

        card_shadow = CTkFrame(form_wrap, fg_color=COLORS["shadow"], corner_radius=26)
        card_shadow.place(relx=0.5, rely=0.5, anchor="center",
                          relwidth=0.96, relheight=0.96)

        card = CTkFrame(
            form_wrap,
            fg_color=COLORS["panel_alt"],
            corner_radius=24,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.place(relx=0.5, rely=0.5, anchor="center",
                   relwidth=0.96, relheight=0.96)

        inner = CTkFrame(card, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=26, pady=24)

        # Title / subtitle
        CTkLabel(
            inner,
            text="Enter OTP",
            font=("Tahoma", 26, "bold"),
            text_color=COLORS["text"],
        ).pack(pady=(4, 2), anchor="w")

        CTkLabel(
            inner,
            text=f"We’ve sent a 6‑digit code to {email or 'your email'}.",
            font=("Tahoma", 12),
            text_color=COLORS["subtext"],
            wraplength=360,
            justify="left",
        ).pack(pady=(0, 14), anchor="w")

        # OTP entry
        otp_entry = CTkEntry(
            inner,
            placeholder_text="6‑digit code",
            width=340,
            height=46,
            corner_radius=16,
            fg_color=COLORS["frame"],
            border_color=COLORS["border"],
            border_width=2,
            justify="center",
            font=("Segoe UI", 18),
            text_color=COLORS["text_dark"],
            placeholder_text_color=COLORS["muted"],
        )
        otp_entry.pack(pady=(4, 10))

        # Resend + small hint row
        row_resend = CTkFrame(inner, fg_color="transparent")
        row_resend.pack(pady=(0, 10), fill="x")

        resend_lbl = CTkLabel(
            row_resend,
            text="Resend OTP",
            text_color=COLORS["accent"],
            font=("Segoe UI", 12, "underline"),
            cursor="hand2",
        )
        resend_lbl.pack(side="left")
        resend_lbl.bind("<Button-1>", lambda e: resend_otp())
        resend_lbl.bind(
            "<Enter>",
            lambda e: resend_lbl.configure(
                text_color=COLORS["accent_hover"], font=("Segoe UI", 12, "underline")
            ),
        )
        resend_lbl.bind(
            "<Leave>",
            lambda e: resend_lbl.configure(
                text_color=COLORS["accent"], font=("Segoe UI", 12, "underline")
            ),
        )

        CTkLabel(
            row_resend,
            text="Code valid for a short time. Do not share it.",
            font=("Segoe UI", 10),
            text_color=COLORS["muted"],
        ).pack(side="right")

        # CAPTCHA panel (inside card)
        captcha_frame = CTkFrame(
            inner,
            fg_color=COLORS["frame"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        captcha_frame.pack(pady=(8, 12), fill="x")
        captcha_frame.grid_columnconfigure((0, 1, 2), weight=0)

        captcha_label = CTkLabel(
            captcha_frame,
            text=captcha_value,
            width=100,
            font=("Segoe UI Semibold", 20),
            text_color=COLORS["accent3"],
        )
        captcha_label.grid(row=0, column=0, padx=(16, 6), pady=10)

        refresh_btn = CTkButton(
            captcha_frame,
            text="\u27F3",
            width=40,
            height=32,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            command=refresh_captcha,
            corner_radius=12,
        )
        refresh_btn.grid(row=0, column=1, padx=6, pady=10)

        ent_captcha = CTkEntry(
            captcha_frame,
            placeholder_text="Enter CAPTCHA",
            width=180,
            height=34,
            fg_color=COLORS["panel_alt"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text_dark"],
            placeholder_text_color=COLORS["muted"],
        )
        ent_captcha.grid(row=0, column=2, padx=(6, 16), pady=10, sticky="e")

        # Buttons
        actions = CTkFrame(inner, fg_color="transparent")
        actions.pack(pady=(10, 8))

        verify_btn = CTkButton(
            actions,
            text="Verify and continue",
            command=check_otp,
            width=260,
            height=44,
            corner_radius=22,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=("Tahoma", 16, "bold"),
        )
        verify_btn.pack(pady=(4, 4))

        back_btn = CTkButton(
            actions,
            text="← Back",
            command=back_to_previous_page,
            width=260,
            height=40,
            corner_radius=20,
            fg_color="transparent",
            border_width=2,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            hover_color=COLORS["panel"],
            font=("Tahoma", 13, "bold"),
        )
        back_btn.pack(pady=(2, 0))

        # Optional footer inside card
        CTkLabel(
            inner,
            text=f"© {datetime.datetime.now().year} Gaia Sentinel — Protecting nature together",
            font=("Segoe UI", 10),
            text_color=COLORS["subtext"],
        ).pack(pady=(8, 0))

        # keep refs if needed
        self._otp_ui_refs = {
            "otp_entry": otp_entry,
            "captcha_label": captcha_label,
            "ent_captcha": ent_captcha,
            "verify_btn": verify_btn,
            "back_btn": back_btn,
        }

    def login_page(self):
        def change_password(s):
            from customtkinter import (
                CTkToplevel, CTkFrame, CTkLabel, CTkEntry,
                CTkButton, CTkCheckBox, CTkTabview
            )
            from tkinter import messagebox, StringVar
            from datetime import datetime, timedelta
            import random
            import iPT_UA_database as db

            # ------------ shared state ------------
            current_email: str | None = None
            current_username: str | None = None
            current_otp: str | None = None
            otp_expires_at: datetime | None = None

            # ------------ parent & toplevel ------------
            parent = getattr(self, "root", None) or self

            win = CTkToplevel(parent)
            win.title("Gaia Sentinel - Forgot Password")
            win.configure(fg_color=COLORS["bg_primary"])
            win.resizable(False, False)
            win.grab_set()

            BASE_W = 520
            STEP_H = {1: 420, 2: 430, 3: 630}

            def center(step: int):
                h = STEP_H[step]
                try:
                    win.update_idletasks()
                    px = parent.winfo_rootx()
                    py = parent.winfo_rooty()
                    pw = parent.winfo_width()
                    ph = parent.winfo_height()
                    x = px + (pw - BASE_W) // 2
                    y = py + (ph - h) // 2
                    win.geometry(f"{BASE_W}x{h}+{x}+{y}")
                except Exception:
                    win.geometry(f"{BASE_W}x{h}")

            # ------------ outer / card ------------
            center(1)
            outer = CTkFrame(
                win,
                fg_color=COLORS["bg_secondary"],
                corner_radius=26,
            )
            outer.pack(fill="both", expand=True, padx=18, pady=18)
            outer.grid_columnconfigure(0, weight=1)
            outer.grid_rowconfigure(2, weight=1)

            # small icon
            icon_row = CTkFrame(outer, fg_color="transparent")
            icon_row.grid(row=0, column=0, pady=(4, 2))
            CTkLabel(
                icon_row,
                text="⚡",
                font=("Segoe UI", 24),
                text_color=COLORS["accent"],
            ).pack()

            header = CTkFrame(outer, fg_color="transparent")
            header.grid(row=1, column=0, sticky="ew")
            header.grid_columnconfigure(0, weight=1)

            CTkLabel(
                header,
                text="Forgot Password?",
                font=("Segoe UI Semibold", 22, "bold"),
                text_color=COLORS["text_dark"],
            ).grid(row=0, column=0, pady=(0, 4))

            CTkLabel(
                header,
                text="We’ll verify your email, confirm the OTP, and then let you set a new password.",
                font=("Segoe UI", 10),
                text_color=COLORS["subtext"],
                wraplength=420,
                justify="center",
            ).grid(row=1, column=0, pady=(0, 8))

            CTkFrame(
                header,
                fg_color=COLORS["panel_edge"],
                height=1,
                corner_radius=999,
            ).grid(row=2, column=0, sticky="ew", padx=80, pady=(2, 4))

            card = CTkFrame(
                outer,
                fg_color=COLORS["panel"],
                corner_radius=22,
                border_width=1,
                border_color=COLORS["panel_edge"],
            )
            card.grid(row=2, column=0, sticky="nsew", padx=26, pady=(10, 15))
            card.grid_columnconfigure(0, weight=1)
            card.grid_rowconfigure(1, weight=1)

            # ------------ Tabs (non-clickable step indicator) ------------
            tabview = CTkTabview(
                master=card,
                fg_color=COLORS["panel"],
                corner_radius=10,
                segmented_button_fg_color=COLORS["frame"],  # bar background
                segmented_button_unselected_color=COLORS["frame"],  # normal tabs
                segmented_button_selected_color=COLORS["accent"],  # active tab
                segmented_button_selected_hover_color=COLORS["accent_hover"],
                segmented_button_unselected_hover_color=COLORS["panel_alt"],
                text_color=COLORS["text"],
            )
            tabview.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 6))

            for button in tabview._segmented_button._buttons_dict.values():
                button.configure(corner_radius=12, width=110, height=32,  font=("Segoe UI Semibold", 12), border_width=0)

            tab_email = tabview.add("Email")
            tab_otp = tabview.add("OTP")
            tab_pass = tabview.add("New Password")

            # user cannot click tabs
            try:
                tabview._segmented_button.configure(state="disabled")
            except Exception:
                pass

            def go_step(step: int):
                if step == 1:
                    tabview.set("Email")
                elif step == 2:
                    tabview.set("OTP")
                elif step == 3:
                    tabview.set("New Password")
                center(step)

            # helper for final messagebox to always be visible
            def topmost_info(title: str, msg: str):
                win.attributes("-topmost", False)
                try:
                    messagebox.showinfo(title, msg, parent=win)
                finally:
                    pass

            # ==================================================================
            # STEP 1: EMAIL
            # ==================================================================
            tab_email.grid_columnconfigure(0, weight=1)

            CTkLabel(
                tab_email,
                text="Email Address",
                font=("Segoe UI Semibold", 12),
                text_color=COLORS["text_dark"],
            ).grid(row=0, column=0, sticky="w", padx=24, pady=(6, 4))

            email_var = StringVar()
            email_entry = CTkEntry(
                tab_email,
                textvariable=email_var,
                fg_color=COLORS["bg_primary"],
                border_color=COLORS["select"],
                border_width=2,
                corner_radius=14,
                height=36,
                text_color=COLORS["text_dark"],
                placeholder_text="Enter your email",
            )
            email_entry.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 6))

            email_status = CTkLabel(
                tab_email,
                text="We’ll send a 6-digit code to this email.",
                font=("Segoe UI", 9),
                text_color=COLORS["muted"],
                wraplength=380,
                justify="left",
            )
            email_status.grid(row=2, column=0, sticky="w", padx=24, pady=(0, 4))

            def do_send_otp():
                nonlocal current_email, current_username, current_otp, otp_expires_at

                mail = email_var.get().strip()
                if not mail:
                    email_status.configure(
                        text="Please enter your email address.",
                        text_color=COLORS["danger"],
                    )
                    return

                rows = db.fetch_email_and_pass_for_login(mail)
                if not rows:
                    email_status.configure(
                        text="We couldn’t find an account with that email.",
                        text_color=COLORS["danger"],
                    )
                    return

                username, stored_email, _pwd = rows[0]
                current_email = stored_email
                current_username = username

                otp = f"{random.randint(0, 999999):06d}"
                current_otp = otp
                otp_expires_at = datetime.now() + timedelta(minutes=10)

                email_status.configure(
                    text=f"Sending OTP to {stored_email}…",
                    text_color=COLORS["muted"],
                )

                db.send_mail_for_otp(username, stored_email, otp, valid_minutes=10)

                email_status.configure(
                    text=f"OTP sent to {stored_email}. Code is valid for 10 minutes.",
                    text_color=COLORS["success"],
                )

                go_step(2)
                otp_entry.focus_set()

            send_otp_btn = CTkButton(
                tab_email,
                text="Send Reset Code",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color="white",
                corner_radius=18,
                height=38,
                font=("Segoe UI Semibold", 12, "bold"),
                command=do_send_otp,
            )
            send_otp_btn.grid(row=3, column=0, sticky="ew", padx=80, pady=(10, 12))

            # ==================================================================
            # STEP 2: OTP
            # ==================================================================
            tab_otp.grid_columnconfigure(0, weight=1)

            CTkLabel(
                tab_otp,
                text="Enter the 6-digit code we emailed to you.",
                font=("Segoe UI", 10),
                text_color=COLORS["subtext"],
                wraplength=380,
                justify="center",
            ).grid(row=0, column=0, sticky="n", padx=18, pady=(14, 6))

            otp_var = StringVar()
            otp_entry = CTkEntry(
                tab_otp,
                textvariable=otp_var,
                fg_color=COLORS["bg_primary"],
                border_color=COLORS["select"],
                border_width=2,
                corner_radius=14,
                height=40,
                text_color=COLORS["text_dark"],
                justify="center",
            )
            otp_entry.grid(row=1, column=0, sticky="ew", padx=80, pady=(0, 6))

            otp_status_lbl = CTkLabel(
                tab_otp,
                text="Didn’t get a code? Check spam folder or resend.",
                font=("Segoe UI", 9),
                text_color=COLORS["muted"],
                wraplength=380,
                justify="center",
            )
            otp_status_lbl.grid(row=2, column=0, padx=24, pady=(0, 4))

            def do_verify_otp():
                nonlocal current_otp, otp_expires_at

                if not current_email or not current_username or not current_otp:
                    otp_status_lbl.configure(
                        text="Session expired. Please restart the reset process.",
                        text_color=COLORS["danger"],
                    )
                    go_step(1)
                    email_entry.focus_set()
                    return

                code = otp_var.get().strip()
                if not code:
                    otp_status_lbl.configure(
                        text="Please enter the 6-digit code.",
                        text_color=COLORS["danger"],
                    )
                    return

                if otp_expires_at and datetime.now() > otp_expires_at:
                    otp_status_lbl.configure(
                        text="This code has expired. Please request a new one.",
                        text_color=COLORS["danger"],
                    )
                    go_step(1)
                    email_entry.focus_set()
                    return

                if code != current_otp:
                    otp_status_lbl.configure(
                        text="Incorrect code. Please try again.",
                        text_color=COLORS["danger"],
                    )
                    return

                otp_status_lbl.configure(
                    text="OTP verified. You can now set a new password.",
                    text_color=COLORS["success"],
                )
                go_step(3)
                new_entry.focus_set()

            def do_resend():
                if not email_var.get().strip():
                    otp_status_lbl.configure(
                        text="Enter your email on the first step to resend the code.",
                        text_color=COLORS["danger"],
                    )
                    go_step(1)
                    email_entry.focus_set()
                    return
                do_send_otp()
                otp_status_lbl.configure(
                    text="We’ve sent a new code to your email.",
                    text_color=COLORS["success"],
                )

            verify_btn = CTkButton(
                tab_otp,
                text="Verify Code",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color="white",
                corner_radius=18,
                height=38,
                font=("Segoe UI Semibold", 12, "bold"),
                command=do_verify_otp,
            )
            verify_btn.grid(row=3, column=0, sticky="ew", padx=80, pady=(10, 4))

            resend_link = CTkLabel(
                tab_otp,
                text="Resend code",
                font=("Segoe UI", 11, "underline"),
                text_color=COLORS["text_subtle"],
                cursor="hand2",
            )
            resend_link.grid(row=4, column=0, pady=(0, 8))
            resend_link.bind("<Button-1>", lambda _e: do_resend())

            # ==================================================================
            # STEP 3: NEW PASSWORD
            # ==================================================================
            tab_pass.grid_columnconfigure(0, weight=1)

            CTkLabel(
                tab_pass,
                text="Create a new password",
                font=("Segoe UI Semibold", 13, "bold"),
                text_color=COLORS["text_dark"],
            ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 2))

            CTkLabel(
                tab_pass,
                text="Use at least 8 characters including letters, numbers and symbols.",
                font=("Segoe UI", 10),
                text_color=COLORS["muted"],
                wraplength=380,
                justify="left",
            ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 8))

            new_var = StringVar()
            confirm_var = StringVar()
            show_var = StringVar(value="0")

            CTkLabel(
                tab_pass,
                text="New password:",
                font=("Segoe UI Semibold", 11),
                text_color=COLORS["text_dark"],
            ).grid(row=2, column=0, sticky="w", padx=24, pady=(4, 2))

            new_entry = CTkEntry(
                tab_pass,
                textvariable=new_var,
                show="*",
                fg_color=COLORS["bg_primary"],
                border_color=COLORS["select"],
                border_width=2,
                corner_radius=14,
                height=36,
                text_color=COLORS["text_dark"],
            )
            new_entry.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 6))

            CTkLabel(
                tab_pass,
                text="Confirm password:",
                font=("Segoe UI Semibold", 11),
                text_color=COLORS["text_dark"],
            ).grid(row=4, column=0, sticky="w", padx=24, pady=(4, 2))

            confirm_entry = CTkEntry(
                tab_pass,
                textvariable=confirm_var,
                show="*",
                fg_color=COLORS["bg_primary"],
                border_color=COLORS["select"],
                border_width=2,
                corner_radius=14,
                height=36,
                text_color=COLORS["text_dark"],
            )
            confirm_entry.grid(row=5, column=0, sticky="ew", padx=24, pady=(0, 4))

            pass_status = CTkLabel(
                tab_pass,
                text="",
                font=("Segoe UI", 9),
                text_color=COLORS["muted"],
                wraplength=380,
                justify="left",
            )
            pass_status.grid(row=6, column=0, sticky="w", padx=24, pady=(0, 4))

            def toggle_show():
                if show_var.get() == "1":
                    new_entry.configure(show="")
                    confirm_entry.configure(show="")
                else:
                    new_entry.configure(show="*")
                    confirm_entry.configure(show="*")

            show_chk = CTkCheckBox(
                tab_pass,
                text="Show password",
                variable=show_var,
                onvalue="1",
                offvalue="0",
                command=toggle_show,
                fg_color=COLORS["accent"],
                border_color=COLORS["panel_edge"],
                text_color=COLORS["muted"],
                checkbox_height=16,
                checkbox_width=16,
                corner_radius=4,
            )
            show_chk.grid(row=7, column=0, sticky="w", padx=24, pady=(0, 6))

            def do_save_password():
                if not current_email or not current_username:
                    pass_status.configure(
                        text="Session expired. Please restart the reset process.",
                        text_color=COLORS["danger"],
                    )
                    return

                new_pw = new_var.get().strip()
                conf_pw = confirm_var.get().strip()

                if not new_pw or not conf_pw:
                    pass_status.configure(
                        text="Please fill in both password fields.",
                        text_color=COLORS["danger"],
                    )
                    return

                if len(new_pw) < 8:
                    pass_status.configure(
                        text="Password should be at least 8 characters long.",
                        text_color=COLORS["danger"],
                    )
                    return

                if new_pw != conf_pw:
                    pass_status.configure(
                        text="New password and confirmation do not match.",
                        text_color=COLORS["danger"],
                    )
                    return

                # ---- update EXISTING user in DB (no new account is created) ----
                try:
                    conn = db.get_db_conn()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE users SET password = %s WHERE email = %s",
                        (new_pw, current_email),
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    pass_status.configure(
                        text=f"Could not update password: {e}",
                        text_color=COLORS["danger"],
                    )
                    return

                pass_status.configure(
                    text="Password updated successfully. You can close this window.",
                    text_color=COLORS["success"],
                )
                topmost_info("Password updated", "Your password has been successfully changed.")
                try:
                    win.grab_release()
                except Exception:
                    pass
                win.destroy()

            save_btn = CTkButton(
                tab_pass,
                text="Reset Password",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color="white",
                corner_radius=18,
                height=40,
                font=("Segoe UI Semibold", 12, "bold"),
                command=do_save_password,
            )
            save_btn.grid(row=8, column=0, sticky="ew", padx=80, pady=(8, 4))

            back_lbl = CTkLabel(
                tab_pass,
                text="Back to login",
                font=("Segoe UI", 11, "underline"),
                text_color=COLORS["text_subtle"],
                cursor="hand2",
            )
            back_lbl.grid(row=9, column=0, pady=(0, 10))
            back_lbl.bind("<Button-1>", lambda _e: (win.grab_release(), win.destroy()))

            # start
            go_step(1)
            email_entry.focus_set()

        # Fullscreen / maximized window
        try:
            self.root.state("zoomed")
        except:
            self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")

        self.root.title("Gaia Sentinel - Login")

        from tkinter import BooleanVar, messagebox

        for childing in self.root.winfo_children():
            childing.destroy()

        # ------------ BACKGROUND ------------
        self.root.configure(fg_color=COLORS["bg_primary"])

        # Outer wrapper
        shell = CTkFrame(self.root, fg_color=COLORS["bg_primary"], corner_radius=0)
        shell.pack(fill="both", expand=True)

        # Big central panel covering most of the page
        main_shadow = CTkFrame(
            shell,
            fg_color=COLORS["shadow"],
            corner_radius=32,
        )
        main_shadow.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.82)

        main_panel = CTkFrame(
            shell,
            fg_color=COLORS["panel"],
            corner_radius=28,
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        main_panel.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.82)

        main_panel.grid_rowconfigure(0, weight=1)
        main_panel.grid_columnconfigure(0, weight=7)  # left hero
        main_panel.grid_columnconfigure(1, weight=5)  # right form

        # ------------ LEFT HERO / ART SIDE ------------
        hero = CTkFrame(main_panel, fg_color="transparent")
        hero.grid(row=0, column=0, sticky="nsew", padx=(26, 10), pady=26)
        hero.grid_rowconfigure(3, weight=1)

        # Decorative gradient block (fake with solid color)
        top_banner = CTkFrame(
            hero,
            fg_color=COLORS["accent1"],
            corner_radius=20,
        )
        top_banner.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        top_banner.grid_columnconfigure(0, weight=1)

        CTkLabel(
            top_banner,
            text="GAIA SENTINEL",
            font=("Segoe UI Semibold", 20, "bold"),
            text_color=COLORS["text_main"],
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))

        CTkLabel(
            top_banner,
            text="Environmental Intelligence • Secured Access",
            font=("Segoe UI", 13),
            text_color=COLORS["text_subtle"],
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))

        # Big title + tagline
        CTkLabel(
            hero,
            text="Defend the planet.\nShape the future.",
            font=("Segoe UI Semibold", 33, "bold"),
            text_color=COLORS["text"],
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 10))

        CTkLabel(
            hero,
            text="Sign in to monitor air, water and field nodes from a single, secure command center.",
            font=("Segoe UI", 15),
            text_color=COLORS["subtext"],
            wraplength=520,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(0, 18))

        # Feature bullets
        bullets = CTkFrame(hero, fg_color="transparent")
        bullets.grid(row=3, column=0, sticky="nw")

        def bullet(text):
            r = bullets.grid_size()[1]
            CTkLabel(
                bullets,
                text="●",
                font=("Segoe UI", 13, "bold"),
                text_color=COLORS["accent3"],
            ).grid(row=r, column=0, sticky="ne", padx=(0, 6), pady=3)
            CTkLabel(
                bullets,
                text=text,
                font=("Segoe UI", 13),
                text_color=COLORS["text"],
                wraplength=430,
                justify="left",
            ).grid(row=r, column=1, sticky="w", pady=3)

        bullet("Real‑time insights from air, water and drone nodes.")
        bullet("Secure OTP-based login to protect your data.")
        bullet("Designed for guardians of forests, coasts and cities.")

        # Tiny footer
        CTkLabel(
            hero,
            text="© 2025 Gaia Sentinel • Built for those who protect nature",
            font=("Segoe UI", 13),
            text_color=COLORS["subtext"],
        ).grid(row=4, column=0, sticky="sw", pady=(18, 0))

        # ------------ RIGHT LOGIN SIDE (GLASS CARD) ------------
        form_wrap = CTkFrame(main_panel, fg_color="transparent")
        form_wrap.grid(row=0, column=1, sticky="nsew", padx=(10, 26), pady=26)
        form_wrap.grid_rowconfigure(0, weight=1)
        form_wrap.grid_columnconfigure(0, weight=1)

        # Outer “glass” look
        glass = CTkFrame(
            form_wrap,
            fg_color=COLORS["panel_alt"],
            corner_radius=24,
            border_width=1,
            border_color=COLORS["border"],
        )
        glass.grid(row=0, column=0, sticky="", padx=8, pady=8)

        # Slight inner padding
        inner = CTkFrame(glass, fg_color="transparent")
        inner.pack(expand=True, fill="y", anchor='center', padx=26, pady=24)

        # ------------ LOGIN LOGIC (same behaviour) ------------
        def login():
            username = username_entry.get().strip()  # here you are treating as email
            pwd = password_entry.get().strip()

            if not username or not pwd:
                messagebox.showwarning("Error", "All fields are required.")
                return

            try:
                details = fetch_email_and_pass_for_login(username)
                if details and pwd == details[0][2]:
                    self.otp_page(details[0][0], details[0][1], 'log')
                else:
                    messagebox.showerror('Error', 'Invalid Details')
            except Exception as e:
                print("Login error:", e)
                messagebox.showerror('Error', 'Invalid Details')

        def go_back():
            for child in self.root.winfo_children():
                child.destroy()
            self.welcome_page()

        # ------------ FORM UI ------------
        # Title
        CTkLabel(
            inner,
            text="Log in",
            font=("Tahoma", 30, "bold"),
            text_color=COLORS["text"],
        ).pack(pady=(4, 2), anchor="center")

        CTkLabel(
            inner,
            text="Access your Gaia Sentinel workspace.",
            font=("Tahoma", 13),
            text_color=COLORS["subtext"],
        ).pack(pady=(0, 18), anchor="center")

        # Email / username field
        username_entry = CTkEntry(
            inner,
            placeholder_text="Email",
            width=360,
            height=44,
            corner_radius=16,
            fg_color=COLORS["frame"],
            border_color=COLORS["border"],
            border_width=2,
            text_color=COLORS["text_dark"],
            placeholder_text_color=COLORS["muted"],
        )
        username_entry.pack(pady=6)

        # Password field
        password_entry = CTkEntry(
            inner,
            placeholder_text="Password",
            show="*",
            width=360,
            height=44,
            corner_radius=16,
            fg_color=COLORS["frame"],
            border_color=COLORS["border"],
            border_width=2,
            text_color=COLORS["text_dark"],
            placeholder_text_color=COLORS["muted"])
        password_entry.pack(pady=6)

        # Remember + Forgot row
        options_row = CTkFrame(inner, fg_color="transparent")
        options_row.pack(pady=(6, 12), fill="x")

        remember_var = BooleanVar()
        remember_cb = CTkCheckBox(options_row,
            text="Remember me",
            variable=remember_var,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["subtext"])
        remember_cb.pack(side="left")

        forgot_label = CTkLabel(options_row, text="Forgot password?", text_color=COLORS["accent"], font=("Tahoma", 12))
        forgot_label.pack(side="right")

        forgot_label.bind("<Button-1>", change_password)
        forgot_label.bind("<Enter>", lambda e: forgot_label.configure(text_color=COLORS["accent_hover"], font=("Tahoma", 12, "underline")))
        forgot_label.bind("<Leave>", lambda e: forgot_label.configure(text_color=COLORS["accent"], font=("Tahoma", 12)))

        # Login button
        login_btn = CTkButton(inner, text="Continue", command=login, width=280, height=44, corner_radius=22, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color="white", font=("Tahoma", 16, "bold"))
        login_btn.pack(pady=(6, 4))

        # Back button (subtle)
        back_btn = CTkButton(inner, text="← Back to welcome", command=go_back, width=280, height=40, corner_radius=20, fg_color="transparent", border_width=2, border_color=COLORS["border"], text_color=COLORS["text"], hover_color=COLORS["panel"], font=("Tahoma", 13, "bold"))
        back_btn.pack(pady=(4, 14))

        # Divider
        CTkLabel(inner, text="──────────  OR  ──────────", font=("Segoe UI", 10), text_color=COLORS["muted"]).pack(pady=(2, 8))

        # Signup link
        bottom = CTkFrame(inner, fg_color="transparent")
        bottom.pack(pady=(0, 4))

        CTkLabel(bottom, text="New here?", font=("Tahoma", 12), text_color=COLORS["subtext"]).pack(side="left", padx=(0, 4))

        signup_link = CTkLabel(bottom, text="Create a Gaia Sentinel account", text_color=COLORS["accent"], font=("Tahoma", 12, "bold"))
        signup_link.pack(side="left")

        signup_link.bind("<Button-1>", lambda e: self.signup_page())
        signup_link.bind("<Enter>", lambda e: signup_link.configure(text_color=COLORS["accent_hover"], font=("Tahoma", 12, "underline")))
        signup_link.bind("<Leave>", lambda e: signup_link.configure(text_color=COLORS["accent"], font=("Tahoma", 12, "bold")))

    def signup_page(self):
        from tkinter import messagebox

        try:
            self.root.state("zoomed")
        except:
            self.root.geometry(
                f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0"
            )

        self.root.title("Gaia Sentinel - Sign Up")

        # Clear old widgets
        for childing in self.root.winfo_children():
            childing.destroy()

        # ------------ BACKGROUND ------------
        self.root.configure(fg_color=COLORS["bg_primary"])

        shell = CTkFrame(self.root, fg_color=COLORS["bg_primary"], corner_radius=0)
        shell.pack(fill="both", expand=True)

        # Big central panel
        main_shadow = CTkFrame(
            shell,
            fg_color=COLORS["shadow"],
            corner_radius=32,
        )
        main_shadow.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.82)

        main_panel = CTkFrame(
            shell,
            fg_color=COLORS["panel"],
            corner_radius=28,
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        main_panel.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.82)

        main_panel.grid_rowconfigure(0, weight=1)
        main_panel.grid_columnconfigure(0, weight=7)  # left hero
        main_panel.grid_columnconfigure(1, weight=5)  # right form

        # ------------ LEFT HERO SIDE ------------
        hero = CTkFrame(main_panel, fg_color="transparent")
        hero.grid(row=0, column=0, sticky="nsew", padx=(26, 10), pady=26)
        hero.grid_rowconfigure(3, weight=1)

        # Top banner
        top_banner = CTkFrame(
            hero,
            fg_color=COLORS["accent1"],
            corner_radius=20,
        )
        top_banner.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        top_banner.grid_columnconfigure(0, weight=1)

        CTkLabel(
            top_banner,
            text="Join Gaia Sentinel",
            font=("Segoe UI Semibold", 30, "bold"),
            text_color=COLORS["text_main"],
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))

        CTkLabel(
            top_banner,
            text="Create a secure account for environmental monitoring.",
            font=("Segoe UI", 13),
            text_color=COLORS["text_subtle"],
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))

        # Main hero text
        CTkLabel(
            hero,
            text="Create your\nGaia Sentinel account.",
            font=("Segoe UI Semibold", 30, "bold"),
            text_color=COLORS["text"],
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 10))

        CTkLabel(
            hero,
            text="Set up a secure profile to receive OTP‑protected access and keep your sensor data safe.",
            font=("Segoe UI", 13),
            text_color=COLORS["subtext"],
            wraplength=520,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(0, 18))

        # Bullets
        bullets = CTkFrame(hero, fg_color="transparent")
        bullets.grid(row=3, column=0, sticky="nw")

        def bullet(text):
            r = bullets.grid_size()[1]
            CTkLabel(
                bullets,
                text="●",
                font=("Segoe UI", 13, "bold"),
                text_color=COLORS["accent3"],
            ).grid(row=r, column=0, sticky="ne", padx=(0, 6), pady=3)
            CTkLabel(
                bullets,
                text=text,
                font=("Segoe UI", 13),
                text_color=COLORS["text"],
                wraplength=430,
                justify="left",
            ).grid(row=r, column=1, sticky="w", pady=3)

        bullet("Single sign‑in for all air, water and drone nodes.")
        bullet("OTP verification on signup to prevent unauthorized access.")
        bullet("Designed for teams protecting forests, coasts and cities.")

        CTkLabel(
            hero,
            text="© 2025 Gaia Sentinel • Built for those who protect nature",
            font=("Segoe UI", 13),
            text_color=COLORS["subtext"],
        ).grid(row=4, column=0, sticky="sw", pady=(18, 0))

        # ------------ RIGHT SIGNUP FORM (GLASS CARD) ------------
        form_wrap = CTkFrame(main_panel, fg_color="transparent")
        form_wrap.grid(row=0, column=1, sticky="nsew", padx=(10, 26), pady=26)
        form_wrap.grid_rowconfigure(0, weight=1)
        form_wrap.grid_columnconfigure(0, weight=1)

        glass = CTkFrame(
            form_wrap,
            fg_color=COLORS["panel_alt"],
            corner_radius=24,
            border_width=1,
            border_color=COLORS["border"],
        )
        glass.grid(row=0, column=0, sticky="", padx=8, pady=8)

        inner = CTkFrame(glass, fg_color="transparent")
        inner.pack(expand=True, fill="y", padx=26, pady=24)

        # ---------- LOGIC (unchanged from your original) ----------
        def signup():
            username = username_entry.get().strip()
            email = email_entry.get().strip()
            pwd = password_entry.get().strip()
            confirm = password_cf_entry.get().strip()

            if not username or not email or not pwd or not confirm:
                messagebox.showwarning("Error", "All fields are required.")
                return
            if pwd != confirm:
                messagebox.showerror("Error", "Passwords do not match.")
                return
            if '@' not in email:
                messagebox.showerror("Error", "Email not found")
                return

            # same call as before
            self.otp_page(username, email, 'sin', pwd)

        def go_back():
            for child in self.root.winfo_children():
                child.destroy()
            self.welcome_page()

        # ---------- FORM UI ----------
        CTkLabel(
            inner,
            text="Sign up",
            font=('Tahoma', 32, 'bold'),
            text_color=COLORS["text"],
        ).pack(pady=(4, 2), anchor="center")

        CTkLabel(
            inner,
            text="Create your Gaia Sentinel account.",
            font=('Tahoma', 13),
            text_color=COLORS["subtext"],
        ).pack(pady=(0, 18), anchor="center")

        username_entry = CTkEntry(
            inner,
            placeholder_text="Username",
            width=360,
            height=44,
            corner_radius=16,
            fg_color=COLORS["frame"],
            border_color=COLORS["border"],
            border_width=2,
            text_color=COLORS["text_dark"],
            placeholder_text_color=COLORS["muted"],
        )
        username_entry.pack(pady=6)

        email_entry = CTkEntry(
            inner,
            placeholder_text="Email ID",
            width=360,
            height=44,
            corner_radius=16,
            fg_color=COLORS["frame"],
            border_color=COLORS["border"],
            border_width=2,
            text_color=COLORS["text_dark"],
            placeholder_text_color=COLORS["muted"],
        )
        email_entry.pack(pady=6)

        password_entry = CTkEntry(
            inner,
            placeholder_text="Password",
            show="*",
            width=360,
            height=44,
            corner_radius=16,
            fg_color=COLORS["frame"],
            border_color=COLORS["border"],
            border_width=2,
            text_color=COLORS["text_dark"],
            placeholder_text_color=COLORS["muted"],
        )
        password_entry.pack(pady=6)

        password_cf_entry = CTkEntry(
            inner,
            placeholder_text="Confirm Password",
            show="*",
            width=360,
            height=44,
            corner_radius=16,
            fg_color=COLORS["frame"],
            border_color=COLORS["border"],
            border_width=2,
            text_color=COLORS["text_dark"],
            placeholder_text_color=COLORS["muted"],
        )
        password_cf_entry.pack(pady=6)

        signup_btn = CTkButton(
            inner,
            text="Create account",
            width=280,
            height=44,
            font=('Tahoma', 16, 'bold'),
            corner_radius=22,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            command=signup,
        )
        signup_btn.pack(pady=(12, 6))

        back_btn = CTkButton(
            inner,
            text="← Back to welcome",
            command=go_back,
            width=280,
            height=40,
            font=('Tahoma', 14, 'bold'),
            corner_radius=20,
            fg_color="transparent",
            border_width=2,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            hover_color=COLORS["panel"],
        )
        back_btn.pack(pady=(4, 10))

        bottom = CTkFrame(inner, fg_color="transparent")
        bottom.pack(pady=(0, 4))

        CTkLabel(
            bottom,
            text="Already have an account?",
            font=('Tahoma', 12),
            text_color=COLORS["subtext"],
        ).pack(side="left", padx=(0, 4))

        login_link = CTkLabel(
            bottom,
            text="Log in",
            text_color=COLORS["accent"],
            font=('Tahoma', 12, 'bold'),
        )
        login_link.pack(side="left")

        login_link.bind("<Button-1>", lambda e: self.login_page())
        login_link.bind(
            "<Enter>",
            lambda e: login_link.configure(
                text_color=COLORS["accent_hover"],
                font=('Tahoma', 12, 'underline'),
            )
        )
        login_link.bind(
            "<Leave>",
            lambda e: login_link.configure(
                text_color=COLORS["accent"],
                font=('Tahoma', 12, 'bold'),
            )
        )

    def welcome_page(self):
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight() - 73}+0+0")

        self.root.title("Gaia Sentinel - Welcome")
        self.root.minsize(900, 600)

        for childing in self.root.winfo_children():
            childing.destroy()

        def open_login():
            for child in self.root.winfo_children():
                child.destroy()
            self.login_page()

        def open_signup():
            for child in self.root.winfo_children():
                child.destroy()
            self.signup_page()

        # --------- BACKGROUND LAYER ---------
        super_frame = CTkFrame(self.root, fg_color="transparent", corner_radius=25)
        super_frame.pack(fill="both", expand=True)

        main_panel = CTkFrame(
            super_frame,
            fg_color=COLORS["panel_alt"],
            corner_radius=50,
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        main_panel.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.82)

        main_panel.grid_rowconfigure(0, weight=1)
        main_panel.grid_columnconfigure(0, weight=2)  # left hero
        main_panel.grid_columnconfigure(1, weight=3)  # right glass card

        # ----- LEFT HERO TEXT -----
        hero = CTkFrame(main_panel, fg_color="transparent")
        hero.grid(row=0, column=0, sticky="nsew", padx=(24, 12), pady=22)
        hero.grid_rowconfigure(3, weight=1)

        accent_bar = CTkFrame(hero, fg_color='transparent')
        accent_bar.grid(row=0, column=0, sticky="w", ipadx=40)

        image = CTkImage(light_image=Image.open("in_app_logo.png"), size=(90, 90))
        logo = CTkLabel(accent_bar, image=image, text='')
        logo.grid(row=0, column=0, padx=(10, 0), pady=5)

        CTkLabel(
            hero,
            text="Gaia Sentinel",
            font=("Segoe UI Semibold", 41, "bold"),
            text_color=COLORS["text_main"],
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

        CTkLabel(
            hero,
            text="Defend the planet. Shape the future.",
            font=("Segoe UI", 17),
            text_color=COLORS["subtext"],
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(0, 14))

        # a few feature bullets
        bullets = CTkFrame(hero, fg_color="transparent")
        bullets.grid(row=3, column=0, sticky="nw")

        def bullet(text):
            r = bullets.grid_size()[1]
            CTkLabel(
                bullets,
                text="●",
                font=("Segoe UI", 13, "bold"),
                text_color=COLORS["accent3"],
            ).grid(row=r, column=0, sticky="ne", padx=(0, 6), pady=3)
            CTkLabel(
                bullets,
                text=text,
                font=("Segoe UI", 13),
                text_color=COLORS["text"],
                wraplength=380,
                justify="left",
            ).grid(row=r, column=1, sticky="w", pady=3)

        bullet("Monitor air, water and drone nodes from one unified dashboard.")
        bullet("Stay ahead of critical environmental changes with smart alerts.")
        bullet("Built for teams safeguarding forests, coasts and cities.")

        CTkLabel(
            hero,
            text="© 2025 Gaia Sentinel • Built for those who protect nature.",
            font=("Segoe UI", 13),
            text_color=COLORS["subtext"],
        ).grid(row=4, column=0, sticky="sw", pady=(18, 0))

        # ----- RIGHT GLASS CARD WITH BUTTONS -----
        card_wrap = CTkFrame(main_panel, fg_color="transparent")
        card_wrap.grid(row=0, column=1, sticky="nsew", padx=(12, 24), pady=22)
        card_wrap.grid_rowconfigure(0, weight=1)
        card_wrap.grid_columnconfigure(0, weight=1)

        card_shadow = CTkFrame(
            card_wrap,
            fg_color=COLORS["shadow"],
            corner_radius=26,
        )
        card_shadow.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

        main_frame = CTkFrame(
            card_wrap,
            corner_radius=40,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
        )
        main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

        inner = CTkFrame(main_frame, fg_color="transparent")
        inner.pack(expand=True, fill="y", padx=28, pady=28)

        # Title + subtitle (using your text)
        title_label = CTkLabel(
            inner,
            text="Welcome to Gaia Sentinel",
            font=("Tahoma", 28, "bold"),
            text_color=COLORS["text"],
        )
        title_label.pack(pady=(20, 6), anchor="w")

        subtitle_label = CTkLabel(
            inner,
            text="Sign in or create a new account to start monitoring your environment.",
            font=("Tahoma", 12),
            text_color=COLORS["subtext"],
            justify="left",
            wraplength=360,
        )
        subtitle_label.pack(pady=(0, 20), anchor="w")

        # Primary actions
        login_button = CTkButton(
            inner,
            text="Login",
            command=open_login,
            font=('Tahoma', 17, 'bold'),
            width=290,
            height=42,
            corner_radius=22,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
        )
        login_button.pack(pady=(10, 8))

        create_button = CTkButton(
            inner,
            text="Create New Account",
            command=open_signup,
            font=('Tahoma', 17, 'bold'),
            width=290,
            height=42,
            corner_radius=22,
            fg_color=COLORS["frame"],
            hover_color=COLORS["panel_alt"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["border"],
        )
        create_button.pack(pady=(4, 12))

        # Small hint text or tagline under buttons
        CTkLabel(
            inner,
            text="OTP-secured access. Your data stays protected.",
            font=("Segoe UI", 12),
            text_color=COLORS["muted"],
        ).pack(pady=(0, 18))

        # Footer inside card (you had this before)
        footer_label = CTkLabel(
            inner,
            text="© 2025 Gaia Sentinel. Built for those who protect nature.",
            font=('Tahoma', 13),
            text_color=COLORS["subtext"],
            fg_color='transparent',
        )
        footer_label.pack(side="bottom", pady=6)


if __name__ == "__main__":
    RUN = IPropellerUserApp()
