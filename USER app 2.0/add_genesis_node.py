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


class AddGenesisNodeTopLevel(CTkToplevel):
    def __init__(self, master, on_connect=None):
        super().__init__(master)
        self.on_connect = on_connect

        # --- WINDOW CONFIG ---
        self.title("Add Genesis Bio-Node")
        self.resizable(False, False)

        # keep it on top of parent & modal-ish
        self.transient(master)  # stay above parent
        self.grab_set()  # block parent input
        self.focus()  # focus this window

        # nice default size + centering relative to parent
        w, h = 480, 520
        self._center_over_parent(master, w, h)

        self.colors = {
            "bg": THEME['LAVENDER_MIST'],  # main background (cream)
            "panel": THEME['WISTERIA'],  # secondary panel background
            "inner": THEME['PANEL_ALT'],  # card inner / strong accent
            "text": THEME['COFFEE_BEAN'],  # main text (dark)
            "muted": THEME['PANEL_SUBTEXT'],  # subtle text
            "accent": THEME['VELVET_ORCHID'],  # primary accent
            "accent_hover": THEME['DARK_AMETHYST'],  # hover accent
            "success": THEME.get('SUCCESS', '#2d8659'),  # success green
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
            text="🌿",
            font=("Tahoma", 32),
        ).pack(side="left", padx=(0, 8))

        CTkLabel(
            header_frame,
            text="ADD GENESIS BIO-NODE",
            font=("Tahoma", 24, "bold"),
            text_color=self.colors["text"],
        ).pack(side="left")

        # Subtitle
        CTkLabel(
            panel,
            text="Algae-based oxygen generation & air purification",
            font=("Tahoma", 12),
            text_color=self.colors["muted"],
        ).grid(row=1, column=0, padx=18, pady=(0, 10))

        CTkFrame(panel, fg_color=self.colors["inner"], height=2).grid(
            row=2, column=0, sticky="ew", padx=18, pady=(0, 20)
        )

        # --- NODE ID ENTRY ---
        CTkLabel(
            panel,
            text="Genesis Node ID:",
            font=("Tahoma", 16, "bold"),
            text_color=self.colors["muted"],
        ).grid(row=3, column=0, sticky="w", padx=25, pady=(5, 2))

        self.node_id_entry = CTkEntry(
            panel,
            placeholder_text="e.g., GS-GENESIS-KVKHGS",
            fg_color=self.colors["inner"],
            border_color="#2a5f55",
            border_width=2,
            text_color=self.colors["text"],
            placeholder_text_color="#7fa69d",
            corner_radius=10,
            height=40,
        )
        self.node_id_entry.grid(row=4, column=0, padx=25, pady=(0, 15), sticky="ew")

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
            text="ℹ️  Genesis nodes use photosynthetic algae to absorb\nCO₂ and generate oxygen while monitoring air quality.",
            font=("Tahoma", 11),
            text_color=self.colors["muted"],
            justify="left",
        ).pack(padx=12, pady=10)

        # --- CONNECT BUTTON ---
        self.connect_btn = CTkButton(
            panel,
            text="CONNECT GENESIS NODE",
            fg_color=self.colors["success"],
            hover_color="#25704d",
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
        self.after(100, lambda: self.node_id_entry.focus_set())

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
        node_id = self.node_id_entry.get().strip()
        pwd = self.pass_entry.get().strip()

        if not node_id or not pwd:
            messagebox.showwarning("Missing Data", "Please enter both Genesis Node ID and password.")
            self.connect_btn.configure(state='normal')
            return

        # Validate Genesis node credentials
        real_check = iPT_UA_database.check_genesis_node_add_to_app(node_id, pwd)
        if real_check:
            iPT_UA_database.add_genesis_node_offline(node_id)

            # Update node ownership online
            try:
                # Get user email from local database
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
                        UPDATE genesis_node 
                        SET avaliable_to_connect='{user_email}' 
                        WHERE genesis_node_name='{node_id}'
                    """)
                    connection.commit()
                    conn.close()
                    connection.close()
            except Exception as e:
                print(f"Error updating Genesis node ownership: {e}")

            # Trigger callback to refresh UI
            if self.on_connect:
                self.on_connect()

            self.destroy()
            messagebox.showinfo('SUCCESS',
                                'Genesis Bio-Node Added Successfully!\n\n🌿 Your algae-powered air purification system is now connected.')
        else:
            messagebox.showwarning('Authentication Failed',
                                   'Genesis Node ID or Password is incorrect.\n\nPlease verify your credentials and try again.')
            self.connect_btn.configure(state='normal')

    def _forgot(self):
        messagebox.showinfo(
            "Forgot Password",
            "To reset your Genesis Bio-Node credentials:\n\n"
            "1. Contact your system administrator\n"
            "2. Or access the node's physical reset button\n"
            "3. Email support: gaia.sentinel@gmail.com"
        )
