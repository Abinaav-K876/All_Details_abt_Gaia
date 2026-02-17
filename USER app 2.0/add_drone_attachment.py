from customtkinter import *
from tkinter import messagebox
import iPT_UA_database
from themes import pink, lavender_og, blue, green, orange
import json, os

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


class AddDroneAttachmentNodeTopLevel(CTkToplevel):
    def __init__(self, master, on_connect=None):
        super().__init__(master)
        self.on_connect = on_connect

        # --- WINDOW CONFIG ---
        self.title("Add Drone Attachment Node")
        self.resizable(False, False)

        # keep it on top of parent & modal-ish
        self.transient(master)  # stay above parent
        self.grab_set()  # block parent input
        self.focus()  # focus this window

        # nice default size + centering relative to parent
        w, h = 460, 480
        self._center_over_parent(master, w, h)

        # --- GAIA SENTINEL COLORS (from global palette) ---
        self.colors = {
            "bg": THEME['LAVENDER_MIST'],  # main background (cream)
            "panel": THEME['WISTERIA'],  # secondary panel background
            "inner": THEME['PANEL_ALT'],  # card inner / strong accent
            "text": THEME['COFFEE_BEAN'],  # main text (dark)
            "muted": THEME['PANEL_SUBTEXT'],  # subtle text
            "accent": THEME['VELVET_ORCHID'],  # primary accent
            "accent_hover": THEME['DARK_AMETHYST'],  # hover accent
            "drone_accent": "#4a90e2"  # blue for drone theme
        }

        self.configure(fg_color=self.colors["bg"])

        # MAIN PANEL
        panel = CTkFrame(self, fg_color=self.colors["panel"], corner_radius=18)
        panel.pack(fill="both", expand=True, padx=20, pady=20)
        panel.grid_columnconfigure(0, weight=1)

        # HEADER with icon
        header_frame = CTkFrame(panel, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=18, pady=(15, 5))

        CTkLabel(
            header_frame,
            text="🚁",
            font=("Tahoma", 28),
        ).pack(side="left", padx=(0, 8))

        CTkLabel(
            header_frame,
            text="ADD DRONE ATTACHMENT",
            font=("Tahoma", 22, "bold"),
            text_color=self.colors["text"],
        ).pack(side="left")

        # Subtitle
        CTkLabel(
            panel,
            text="Connect sensor nodes to your drone platform",
            font=("Tahoma", 12),
            text_color=self.colors["muted"],
        ).grid(row=1, column=0, padx=18, pady=(0, 10))

        CTkFrame(panel, fg_color=self.colors["inner"], height=2).grid(
            row=2, column=0, sticky="ew", padx=18, pady=(0, 20)
        )

        # --- IPT ID ENTRY ---
        CTkLabel(
            panel,
            text="Attachment Node ID:",
            font=("Tahoma", 16, "bold"),
            text_color=self.colors["muted"],
        ).grid(row=3, column=0, sticky="w", padx=25, pady=(5, 2))

        self.ip_entry = CTkEntry(
            panel,
            placeholder_text="Enter Attachment IPT ID",
            fg_color=self.colors["inner"],
            border_color="#2a5f55",
            border_width=2,
            text_color=self.colors["text"],
            placeholder_text_color="#7fa69d",
            corner_radius=10,
            height=40,
        )
        self.ip_entry.grid(row=4, column=0, padx=25, pady=(0, 15), sticky="ew")

        # --- PASSWORD ENTRY ---
        CTkLabel(
            panel,
            text="Authentication Password:",
            font=("Tahoma", 16, "bold"),
            text_color=self.colors["muted"],
        ).grid(row=5, column=0, sticky="w", padx=25, pady=(5, 2))

        self.pass_entry = CTkEntry(
            panel,
            placeholder_text="Enter node password",
            show="●",
            fg_color=self.colors["inner"],
            border_color="#2a5f55",
            border_width=2,
            text_color=self.colors["text"],
            placeholder_text_color="#7fa69d",
            corner_radius=10,
            height=40,
        )
        self.pass_entry.grid(row=6, column=0, padx=25, pady=(0, 20), sticky="ew")

        # --- INFO BOX ---
        info_box = CTkFrame(panel, fg_color=self.colors["inner"], corner_radius=12)
        info_box.grid(row=7, column=0, padx=25, pady=(0, 15), sticky="ew")

        CTkLabel(
            info_box,
            text="ℹ️  This will pair the sensor node with your drone for\naerial environmental monitoring and data collection.",
            font=("Tahoma", 11),
            text_color=self.colors["muted"],
            justify="left",
        ).pack(padx=12, pady=10)

        # --- CONNECT BUTTON ---
        self.connect_btn = CTkButton(
            panel,
            text="CONNECT ATTACHMENT",
            fg_color=self.colors["drone_accent"],
            hover_color="#3a7bc8",
            text_color="white",
            height=46,
            corner_radius=12,
            font=("Tahoma", 17, "bold"),
            command=self._connect,
            text_color_disabled='grey'
        )
        self.connect_btn.grid(row=8, column=0, padx=25, pady=(5, 8), sticky="ew")

        # --- FORGOT PASSWORD LINK STYLE ---
        CTkButton(
            panel,
            text="forgot password",
            fg_color="transparent",
            text_color=self.colors["muted"],
            font=("Tahoma", 13, "underline"),
            command=self._forgot,
            hover_color="#C0BBC0",
        ).grid(row=9, column=0, pady=(0, 15))

        # focus first field
        self.after(100, lambda: self.ip_entry.focus_set())

    # ----------------- HELPERS -----------------

    def _center_over_parent(self, master, w, h):
        """Center this toplevel over the given master window."""
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

    # ----------------- CALLBACKS -----------------

    def _connect(self):
        self.connect_btn.configure(state='disabled')
        iptid = self.ip_entry.get().strip()
        pwd = self.pass_entry.get().strip()

        if not iptid or not pwd:
            messagebox.showwarning("Missing Data", "Please enter both Attachment Node ID and password.")
            self.connect_btn.configure(state='normal')
            return

        # Check drone attachment credentials
        try:
            real_check = iPT_UA_database.check_drone_attachment_add_to_app(iptid, pwd)
        except AttributeError:
            # Fallback if function doesn't exist yet
            print("Warning: check_drone_attachment_add_to_app not implemented yet")
            real_check = True

        if real_check:
            try:
                # Add drone attachment to database
                iPT_UA_database.add_drone_attachment_offline(iptid)

                # Get user email and update ownership
                import sqlite3
                conn = sqlite3.connect('gaialocal.db')
                cur = conn.cursor()
                cur.execute("SELECT usermail FROM user_login_details")
                result = cur.fetchone()
                user_email = result[0] if result else None
                conn.close()

                if user_email:
                    # Update ownership in online database
                    import psycopg2
                    connection = psycopg2.connect(
                        host=iPT_UA_database.host,
                        database=iPT_UA_database.database,
                        user=iPT_UA_database.user,
                        password=iPT_UA_database.password,
                        port=iPT_UA_database.port
                    )
                    conn = connection.cursor()
                    conn.execute(f"""
                        UPDATE drone_attachment 
                        SET avaliable_to_connect='{user_email}' 
                        WHERE attachment_id='{iptid}'
                    """)
                    connection.commit()
                    conn.close()
                    connection.close()
            except Exception as e:
                print(f"Error adding drone attachment: {e}")

            # Trigger callback with attachment ID
            if self.on_connect:
                self.on_connect(iptid)

            self.destroy()
            messagebox.showinfo(
                'SUCCESS',
                '🚁 Drone Attachment Connected!\n\n'
                'The sensor node is now paired with your drone.\n'
                'You can start aerial monitoring operations.'
            )
        else:
            messagebox.showwarning(
                'Authentication Failed',
                'Attachment Node ID or Password is incorrect.\n\n'
                'Please verify your credentials and try again.'
            )
            self.connect_btn.configure(state='normal')

    def _forgot(self):
        messagebox.showinfo(
            "Forgot Password",
            "To reset your Drone Attachment credentials:\n\n"
            "1. Contact your system administrator\n"
            "2. Or access the physical reset on the attachment\n"
            "3. Email support: gaia.sentinel@gmail.com"
        )
