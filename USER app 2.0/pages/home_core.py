import customtkinter as ctk
import threading
import time
import json
import os
import math
from datetime import datetime

# Database imports
from iPT_UA_database import (
    get_all_air_nodes_data_bulk,
    get_all_water_nodes_data_bulk,
    get_all_hepa_nodes_data_bulk,
)

# Try importing Genesis function
try:
    from iPT_UA_database import get_all_genesis_nodes_data_bulk
except ImportError:
    def get_all_genesis_nodes_data_bulk():
        return []

# Try importing DRONES
try:
    from iPT_Drone_Page import DRONES
except ImportError:
    DRONES = []

CACHE_FILE = "dashboard_cache.json"


def hex_to_rgb_with_opacity(hex_color, opacity=0.2):
    """Convert hex color to RGB with opacity simulation using background blending"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Blend with dark background (#1e1e1e)
    bg_r, bg_g, bg_b = 30, 30, 30
    final_r = int(r * opacity + bg_r * (1 - opacity))
    final_g = int(g * opacity + bg_g * (1 - opacity))
    final_b = int(b * opacity + bg_b * (1 - opacity))

    return f"#{final_r:02x}{final_g:02x}{final_b:02x}"


class RadialGauge(ctk.CTkCanvas):
    """Modern radial gauge with smooth animations"""

    def __init__(self, master, bg_color, **kwargs):
        super().__init__(master, background=bg_color, highlightthickness=0, **kwargs)
        self.current_value = 0
        self.target_value = 0
        self.segments = [
            (0, 50, "#00e676"),  # Vibrant green
            (50, 100, "#ffd600"),  # Bright yellow
            (100, 200, "#ff6f00"),  # Vivid orange
            (200, 300, "#d500f9"),  # Purple
            (300, 500, "#c62828")  # Deep red
        ]
        self.bind("<Configure>", lambda e: self.draw())
        self._animate()

    def set_value(self, value):
        """Smooth value transition"""
        self.target_value = max(0, min(value, 500))

    def _animate(self):
        """Animate value changes"""
        if abs(self.current_value - self.target_value) > 1:
            self.current_value += (self.target_value - self.current_value) * 0.15
            self.draw()
        self.after(30, self._animate)

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return

        cx, cy = w // 2, h - 15
        r, width = min(w // 2, h) - 30, 18

        # Background arc (dark gray)
        self.create_arc(cx - r, cy - r, cx + r, cy + r,
                        start=180, extent=-180, outline="#2a2a2a",
                        width=width, style='arc')

        # Colored segments
        start_angle = 180
        for start, end, color in self.segments:
            extent = -((end - start) / 500) * 180
            self.create_arc(cx - r, cy - r, cx + r, cy + r,
                            start=start_angle, extent=extent,
                            outline=color, width=width, style='arc')
            start_angle += extent

        # Calculate needle position
        val = self.current_value
        angle = math.radians(180 - (val / 500 * 180))
        nx, ny = cx + (r - 10) * math.cos(angle), cy - (r - 10) * math.sin(angle)

        # Needle shadow (dark gray instead of transparent black)
        self.create_line(cx + 2, cy - 3, nx + 2, ny + 2,
                         fill="#333333", width=5, capstyle="round")

        # Needle (white)
        self.create_line(cx, cy - 5, nx, ny,
                         fill="#ffffff", width=5, capstyle="round")

        # Center hub with gradient effect
        self.create_oval(cx - 12, cy - 17, cx + 12, cy + 7,
                         fill="#1a1a1a", outline="#444444", width=2)
        self.create_oval(cx - 8, cy - 13, cx + 8, cy + 3,
                         fill="#2d2d2d", outline="")


class Dashboard:
    def __init__(self, parent, app, colors):
        self.parent = parent
        self.app = app
        self.colors = colors
        self.running = True
        self.drones = DRONES
        self.cache_data = {
            "air_val": 0, "air_on": 0, "air_tot": 0,
            "water_val": 0, "water_on": 0, "water_tot": 0,
            "hepa_on": 0, "hepa_tot": 0,
            "genesis_on": 0, "genesis_tot": 0,
            "drone_on": 0
        }

        self.metric_cards = {}
        self.pollution_gauge = self.pollution_status_lbl = self.pollution_detail_lbl = None
        self.drink_status_lbl = self.drink_detail_lbl = None

        self._build_ui()
        self._load_cache()
        self._start_data_loop()

    def destroy(self):
        self.running = False

    def _build_ui(self):
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.parent,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=self.colors.get("panel_edge", "#3a3a3a"),
            scrollbar_button_hover_color=self.colors.get("select", "#505050")
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self._build_header()
        self._build_metrics_grid()
        self._build_analysis_section()
        self._build_quick_actions()
        self._build_info_cards()
        self._build_footer()

    def _build_header(self):
        header = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=120)
        header.pack(fill="x", padx=30, pady=(30, 20))

        txt_frame = ctk.CTkFrame(header, fg_color="transparent")
        txt_frame.pack(side="left", anchor="w")

        name = self.app.user.split(' ')[0] if hasattr(self.app, 'user') else "User"

        welcome = ctk.CTkLabel(
            txt_frame,
            text=f"Welcome back, {name} 👋",
            font=("Segoe UI", 36, "bold"),
            text_color=self.colors.get("text_main", "#ffffff")
        )
        welcome.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            txt_frame,
            text=f"Today is {datetime.now().strftime('%A, %B %d, %Y')}",
            font=("Segoe UI", 14),
            text_color=self.colors.get("subtext", "#999999")
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        status_container = ctk.CTkFrame(header, fg_color="transparent")
        status_container.pack(side="right", anchor="e")

        self.status_pill = ctk.CTkFrame(
            status_container,
            fg_color=self.colors.get("panel", "#2a2a2a"),
            corner_radius=20,
            border_width=1,
            border_color=self.colors.get("panel_edge", "#3a3a3a")
        )
        self.status_pill.pack()

        self.sys_status_lbl = ctk.CTkLabel(
            self.status_pill,
            text="● INITIALIZING",
            font=("Segoe UI", 12, "bold"),
            text_color=self.colors.get("warn", "#ffa726")
        )
        self.sys_status_lbl.pack(padx=20, pady=12)

    def _build_metrics_grid(self):
        container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=10)

        for i in range(5):
            container.grid_columnconfigure(i, weight=1)

        metrics = [
            ("air", "Air Quality", "💨", "Air Node", self.app.home_air_node_page, "#5BA3D0"),
            ("water", "Water Quality", "💧", "Water Node", self.app.home_water_node_page, "#4CAFE8"),
            ("genesis", "Genesis Bio", "🌿", "Genesis Node", getattr(self.app, 'home_genesis_node_page', None),
             "#2d8659"),
            ("hepa", "HEPA Units", "🔄", "Hepa Node", self.app.home_hepa_node_page, "#9C27B0"),
            ("drone", "Drone Fleet", "🚁", "Drone", self.app.home_drone_page, "#4a90e2")
        ]

        for idx, (key, title, icon, nav_title, nav_func, accent) in enumerate(metrics):
            if nav_func:  # Only create card if function exists
                card = self._create_modern_card(
                    container, 0, idx, title, icon,
                    lambda nf=nav_func, nt=nav_title, ic=icon: self.app.navigate(f"{ic}  {nt}", nf),
                    accent
                )
                self.metric_cards[key] = card

    def _create_modern_card(self, parent, r, c, title, icon, command, accent_color):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.colors.get("panel", "#1e1e1e"),
            corner_radius=18,
            border_width=1,
            border_color=self.colors.get("panel_edge", "#2a2a2a")
        )
        card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")

        def on_enter(e):
            if command:
                card.configure(
                    fg_color=self.colors.get("panel_alt", "#252525"),
                    border_color=accent_color,
                    border_width=2
                )

        def on_leave(e):
            if command:
                card.configure(
                    fg_color=self.colors.get("panel", "#1e1e1e"),
                    border_width=1,
                    border_color=self.colors.get("panel_edge", "#2a2a2a")
                )

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        if command:
            card.bind("<Button-1>", lambda e: command())
            card.configure(cursor="hand2")

        # Icon with colored background (using opacity simulation)
        icon_bg_color = hex_to_rgb_with_opacity(accent_color, 0.15)
        icon_frame = ctk.CTkFrame(
            card,
            fg_color=icon_bg_color,
            corner_radius=12,
            width=50,
            height=50
        )
        icon_frame.pack(anchor="w", padx=20, pady=(20, 10))
        icon_frame.pack_propagate(False)

        icon_lbl = ctk.CTkLabel(
            icon_frame,
            text=icon,
            font=("Segoe UI", 24)
        )
        icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

        title_lbl = ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 13, "bold"),
            text_color=self.colors.get("text_subtle", "#cccccc")
        )
        title_lbl.pack(anchor="w", padx=20, pady=(0, 5))

        val_lbl = ctk.CTkLabel(
            card,
            text="--",
            font=("Segoe UI", 32, "bold"),
            text_color=self.colors.get("text_main", "#ffffff")
        )
        val_lbl.pack(anchor="w", padx=20, pady=(0, 5))

        pill = ctk.CTkFrame(
            card,
            fg_color=self.colors.get("frame", "#2a2a2a"),
            corner_radius=12
        )
        pill.pack(anchor="w", padx=20, pady=(0, 20))

        sub_lbl = ctk.CTkLabel(
            pill,
            text="Syncing...",
            font=("Segoe UI", 11),
            text_color=self.colors.get("subtext", "#888888")
        )
        sub_lbl.pack(padx=12, pady=6)

        for w in [icon_frame, icon_lbl, title_lbl, val_lbl, pill, sub_lbl]:
            if command:
                w.bind("<Button-1>", lambda e: command())
                w.configure(cursor="hand2")

        card.val_lbl = val_lbl
        card.sub_lbl = sub_lbl
        return card

    def _build_analysis_section(self):
        container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=15)
        container.grid_columnconfigure((0, 1), weight=1, uniform="equal")

        # Air Quality Analysis
        air_card = self._create_analysis_card(
            container, 0, 0,
            "🌫  Air Quality Analysis",
            "Real-time AQI monitoring and impact assessment"
        )

        content = ctk.CTkFrame(air_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=(10, 25))
        content.grid_columnconfigure(1, weight=1)

        legend = ctk.CTkFrame(content, fg_color="transparent")
        legend.grid(row=0, column=0, sticky="nsw", padx=(0, 15))

        keys = [
            ("#00e676", "Good", "0-50"),
            ("#ffd600", "Moderate", "51-100"),
            ("#ff6f00", "Unhealthy", "101-200"),
            ("#d500f9", "Very Unhealthy", "201-300"),
            ("#c62828", "Hazardous", "301+")
        ]

        for color, txt, range_txt in keys:
            row = ctk.CTkFrame(legend, fg_color="transparent")
            row.pack(anchor="w", pady=4)

            indicator = ctk.CTkFrame(row, width=12, height=12, corner_radius=6, fg_color=color)
            indicator.pack(side="left", padx=(0, 10))

            label_frame = ctk.CTkFrame(row, fg_color="transparent")
            label_frame.pack(side="left")

            ctk.CTkLabel(
                label_frame,
                text=txt,
                font=("Segoe UI", 12, "bold"),
                text_color=self.colors.get("text_main", "#ffffff")
            ).pack(anchor="w")

            ctk.CTkLabel(
                label_frame,
                text=range_txt,
                font=("Segoe UI", 10),
                text_color=self.colors.get("subtext", "#888888")
            ).pack(anchor="w")

        gauge_container = ctk.CTkFrame(content, fg_color="transparent")
        gauge_container.grid(row=0, column=1, sticky="nse", padx=(15, 0))

        self.pollution_gauge = RadialGauge(
            gauge_container,
            bg_color=self.colors.get("panel", "#1e1e1e"),
            height=160,
            width=220
        )
        self.pollution_gauge.pack(anchor="center", pady=(10, 0))

        self.pollution_status_lbl = ctk.CTkLabel(
            gauge_container,
            text="ANALYZING",
            font=("Segoe UI", 24, "bold"),
            text_color=self.colors.get("muted", "#666666")
        )
        self.pollution_status_lbl.pack(anchor="center", pady=(10, 0))

        self.pollution_detail_lbl = ctk.CTkLabel(
            gauge_container,
            text="Evaluating air quality...",
            font=("Segoe UI", 13),
            text_color=self.colors.get("subtext", "#888888")
        )
        self.pollution_detail_lbl.pack(anchor="center", pady=(5, 0))

        # Water Safety Analysis
        water_card = self._create_analysis_card(
            container, 0, 1,
            "🚰  Water Safety Assessment",
            "TDS-based potability and quality evaluation"
        )

        status_container = ctk.CTkFrame(water_card, fg_color="transparent")
        status_container.pack(fill="both", expand=True, padx=25, pady=(10, 25))

        self.drink_status_lbl = ctk.CTkLabel(
            status_container,
            text="ANALYZING",
            font=("Segoe UI", 28, "bold"),
            text_color=self.colors.get("muted", "#666666")
        )
        self.drink_status_lbl.pack(anchor="center", pady=(30, 10))

        self.drink_detail_lbl = ctk.CTkLabel(
            status_container,
            text="Evaluating water quality levels...",
            font=("Segoe UI", 14),
            text_color=self.colors.get("subtext", "#888888"),
            wraplength=350
        )
        self.drink_detail_lbl.pack(anchor="center", pady=(0, 30))

    def _create_analysis_card(self, parent, r, c, title, subtitle):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.colors.get("panel", "#1e1e1e"),
            corner_radius=18,
            border_width=1,
            border_color=self.colors.get("panel_edge", "#2a2a2a")
        )
        card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(25, 5))

        ctk.CTkLabel(
            header,
            text=title,
            font=("Segoe UI", 20, "bold"),
            text_color=self.colors.get("text_main", "#ffffff")
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=subtitle,
            font=("Segoe UI", 13),
            text_color=self.colors.get("subtext", "#888888")
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkFrame(
            card,
            height=1,
            fg_color=self.colors.get("panel_edge", "#2a2a2a")
        ).pack(fill="x", padx=25, pady=(10, 0))

        return card

    def _build_quick_actions(self):
        container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=15)

        actions_card = ctk.CTkFrame(
            container,
            fg_color=self.colors.get("panel", "#1e1e1e"),
            corner_radius=18,
            border_width=1,
            border_color=self.colors.get("panel_edge", "#2a2a2a")
        )
        actions_card.pack(fill="x", padx=10, pady=10)

        header = ctk.CTkFrame(actions_card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))

        ctk.CTkLabel(
            header,
            text="⚡ Quick Actions",
            font=("Segoe UI", 18, "bold"),
            text_color=self.colors.get("text_main", "#ffffff")
        ).pack(anchor="w")

        btn_container = ctk.CTkFrame(actions_card, fg_color="transparent")
        btn_container.pack(fill="x", padx=25, pady=(0, 20))
        btn_container.grid_columnconfigure((0, 1, 2, 3), weight=1)

        actions = [
            ("📊 View Analytics", "#5BA3D0"),
            ("🔔 Check Alerts", "#ff6f00"),
            ("⚙️ Settings", "#9C27B0"),
            ("📖 Documentation", "#4CAFE8")
        ]

        for idx, (text, color) in enumerate(actions):
            btn_bg = hex_to_rgb_with_opacity(color, 0.2)
            btn_hover = hex_to_rgb_with_opacity(color, 0.3)

            btn = ctk.CTkButton(
                btn_container,
                text=text,
                font=("Segoe UI", 13, "bold"),
                fg_color=btn_bg,
                hover_color=btn_hover,
                text_color=color,
                corner_radius=12,
                height=42
            )
            btn.grid(row=0, column=idx, padx=6, pady=0, sticky="ew")

    def _build_info_cards(self):
        container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=15)
        container.grid_columnconfigure((0, 1), weight=1)

        tips_card = self._create_info_card(
            container, 0, 0,
            "🛠  Maintenance & Eco-Tips",
            [
                ("🧹", "Clean sensor inlets every 14 days for accuracy"),
                ("⚙️", "Calibrate Air Nodes if data appears static"),
                ("💧", "Conserve water when TDS levels exceed 500"),
                ("🚁", "Inspect drone propellers before each mission")
            ]
        )

        guidelines_card = self._create_info_card(
            container, 0, 1,
            "⚖️  System Guidelines",
            [
                ("🔒", "All telemetry data is end-to-end encrypted"),
                ("🛡️", "Drones follow strict ethical flight paths"),
                ("👤", "Privacy: Human face masking is enabled"),
                ("📞", "Report sensor anomalies via Support panel")
            ]
        )

    def _create_info_card(self, parent, r, c, title, items):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.colors.get("panel", "#1e1e1e"),
            corner_radius=18,
            border_width=1,
            border_color=self.colors.get("panel_edge", "#2a2a2a")
        )
        card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 18, "bold"),
            text_color=self.colors.get("text_main", "#ffffff")
        ).pack(anchor="w", padx=25, pady=(25, 15))

        for icon, text in items:
            item_frame = ctk.CTkFrame(
                card,
                fg_color=self.colors.get("panel_alt", "#252525"),
                corner_radius=12
            )
            item_frame.pack(fill="x", padx=20, pady=(0, 12))

            content = ctk.CTkFrame(item_frame, fg_color="transparent")
            content.pack(fill="x", padx=15, pady=12)

            ctk.CTkLabel(
                content,
                text=icon,
                font=("Segoe UI", 18)
            ).pack(side="left", padx=(0, 12))

            ctk.CTkLabel(
                content,
                text=text,
                font=("Segoe UI", 13),
                text_color=self.colors.get("text_main", "#ffffff"),
                wraplength=320,
                justify="left"
            ).pack(side="left", fill="x", expand=True)

        ctk.CTkFrame(card, height=13, fg_color="transparent").pack()

    def _build_footer(self):
        footer = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=60)
        footer.pack(fill="x", padx=30, pady=(20, 30))

        left_frame = ctk.CTkFrame(footer, fg_color="transparent")
        left_frame.pack(side="left")

        ctk.CTkLabel(
            left_frame,
            text="Gaia Sentinel Dashboard v2.1",
            font=("Segoe UI", 11),
            text_color=self.colors.get("muted", "#666666")
        ).pack(anchor="w")

        self.last_update_lbl = ctk.CTkLabel(
            footer,
            text="Initializing...",
            font=("Segoe UI", 11, "bold"),
            text_color=self.colors.get("subtext", "#888888")
        )
        self.last_update_lbl.pack(side="right")

    def _is_true(self, val):
        return str(val).lower().strip() in ('true', '1', 'online', 'yes', 'on', 't') if val else False

    def _load_cache(self):
        if not os.path.exists(CACHE_FILE):
            return
        try:
            with open(CACHE_FILE, 'r') as f:
                self.cache_data = json.load(f)
            self._update_display(self.cache_data, is_live=False, status_msg="● CACHED")
        except:
            pass

    def _save_cache(self, data):
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def _start_data_loop(self):
        def worker():
            while self.running:
                try:
                    air_data = get_all_air_nodes_data_bulk()
                    water_data = get_all_water_nodes_data_bulk()
                    hepa_data = get_all_hepa_nodes_data_bulk()
                    genesis_data = get_all_genesis_nodes_data_bulk()

                    # Process air data
                    air_vals, air_on = [], 0
                    for r in air_data:
                        try:
                            v = float(str(r[1]).replace("ppm", "").strip()) if r[1] and r[1] != "-" else 0
                            if v > 0:
                                air_vals.append(v)
                        except:
                            pass
                        if self._is_true(r[2]):
                            air_on += 1
                    avg_air = int(sum(air_vals) / len(air_vals)) if air_vals else 0

                    # Process water data
                    water_vals, water_on = [], 0
                    for r in water_data:
                        try:
                            v = float(str(r[1]).replace("ppm", "").strip()) if r[1] and r[1] != "-" else 0
                            if v > 0:
                                water_vals.append(v)
                        except:
                            pass
                        if self._is_true(r[2]):
                            water_on += 1
                    avg_water = int(sum(water_vals) / len(water_vals)) if water_vals else 0

                    # Process HEPA data
                    hepa_on = sum(1 for r in hepa_data if self._is_true(r[2]))

                    # Process Genesis data
                    genesis_on = sum(1 for r in genesis_data if self._is_true(r[2]))

                    # Process drone data
                    drone_on = sum(1 for d in self.drones if str(d.get('status', '')).upper() == 'ONLINE')

                    self.cache_data.update({
                        "air_val": avg_air, "air_on": air_on, "air_tot": len(air_data),
                        "water_val": avg_water, "water_on": water_on, "water_tot": len(water_data),
                        "hepa_on": hepa_on, "hepa_tot": len(hepa_data),
                        "genesis_on": genesis_on, "genesis_tot": len(genesis_data),
                        "drone_on": drone_on
                    })

                    self._save_cache(self.cache_data)

                    if self.running:
                        self.parent.after(0, lambda: self._update_display(
                            self.cache_data, is_live=True, status_msg="● LIVE"
                        ))

                except Exception as e:
                    print(f"Data Loop Error: {e}")
                    if self.running:
                        self.parent.after(0, lambda: self._update_display(
                            self.cache_data, is_live=False, status_msg="● OFFLINE"
                        ))

                time.sleep(3)

        threading.Thread(target=worker, daemon=True).start()

    def _update_display(self, d, is_live, status_msg):
        if not self.parent.winfo_exists():
            return

        try:
            air_val, air_on, air_tot = d.get("air_val", 0), d.get("air_on", 0), d.get("air_tot", 0)
            water_val, water_on, water_tot = d.get("water_val", 0), d.get("water_on", 0), d.get("water_tot", 0)
            hepa_on, hepa_tot = d.get("hepa_on", 0), d.get("hepa_tot", 0)
            genesis_on, genesis_tot = d.get("genesis_on", 0), d.get("genesis_tot", 0)
            drone_on = d.get("drone_on", 0)

            # Update metric cards
            if "air" in self.metric_cards and self.metric_cards["air"].winfo_exists():
                self.metric_cards["air"].val_lbl.configure(text=f"{air_val}")
                self.metric_cards["air"].sub_lbl.configure(text=f"{air_on}/{air_tot} Nodes Active")

            if "water" in self.metric_cards and self.metric_cards["water"].winfo_exists():
                self.metric_cards["water"].val_lbl.configure(text=f"{water_val}")
                self.metric_cards["water"].sub_lbl.configure(text=f"{water_on}/{water_tot} Nodes Active")

            if "genesis" in self.metric_cards and self.metric_cards["genesis"].winfo_exists():
                self.metric_cards["genesis"].val_lbl.configure(text=f"{genesis_on}/{genesis_tot}")
                self.metric_cards["genesis"].sub_lbl.configure(text=f"{genesis_on} Bio-Units Active")

            if "hepa" in self.metric_cards and self.metric_cards["hepa"].winfo_exists():
                self.metric_cards["hepa"].val_lbl.configure(text=f"{hepa_on}/{hepa_tot}")
                self.metric_cards["hepa"].sub_lbl.configure(text=f"{hepa_on} Units Online")

            if "drone" in self.metric_cards and self.metric_cards["drone"].winfo_exists():
                self.metric_cards["drone"].val_lbl.configure(text=f"{drone_on}")
                self.metric_cards["drone"].sub_lbl.configure(text=f"{drone_on}/{len(self.drones)} Drones Active")

            # Update air quality gauge
            if self.pollution_gauge and self.pollution_gauge.winfo_exists():
                aqi = min(air_val / 2, 500)
                self.pollution_gauge.set_value(aqi)

                if aqi < 50:
                    msg, color = "GOOD", "#00e676"
                elif aqi < 100:
                    msg, color = "MODERATE", "#ffd600"
                elif aqi < 200:
                    msg, color = "UNHEALTHY", "#ff6f00"
                elif aqi < 300:
                    msg, color = "VERY UNHEALTHY", "#d500f9"
                else:
                    msg, color = "HAZARDOUS", "#c62828"

                self.pollution_status_lbl.configure(text=msg, text_color=color)
                cache_note = " (cached)" if not is_live else ""
                self.pollution_detail_lbl.configure(
                    text=f"Average: {air_val} PPM • AQI: {int(aqi)}{cache_note}"
                )

            # Update water safety
            if self.drink_status_lbl and self.drink_status_lbl.winfo_exists():
                if water_val < 300:
                    msg, color = "SAFE TO DRINK ✓", "#00e676"
                    detail = f"TDS level of {water_val} ppm is within safe range"
                elif water_val < 600:
                    msg, color = "CAUTION ADVISED ⚠", "#ffd600"
                    detail = f"TDS level of {water_val} ppm is elevated • Filter recommended"
                else:
                    msg, color = "UNSAFE • DO NOT DRINK ✗", "#c62828"
                    detail = f"TDS level of {water_val} ppm is hazardous • Immediate action required"

                cache_note = " (cached data)" if not is_live else ""
                self.drink_status_lbl.configure(text=msg, text_color=color)
                self.drink_detail_lbl.configure(text=detail + cache_note)

            # Update system status
            if self.sys_status_lbl and self.sys_status_lbl.winfo_exists():
                status_color = "#00e676" if is_live else "#ff6f00"
                self.sys_status_lbl.configure(text=status_msg, text_color=status_color)

            # Update footer timestamp
            if self.last_update_lbl and self.last_update_lbl.winfo_exists():
                if is_live:
                    timestamp = datetime.now().strftime('%I:%M:%S %p')
                    self.last_update_lbl.configure(text=f"Last updated: {timestamp}")
                else:
                    self.last_update_lbl.configure(text="Showing cached data • Reconnecting...")

        except Exception as e:
            print(f"Display update error: {e}")
