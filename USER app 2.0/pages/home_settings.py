from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkOptionMenu, CTkCheckBox, CTkButton
from tkinter import messagebox

def build_settings_page(app):
    for child in app.main_frame.winfo_children():
        if id(child) != app.home_back_img_id:
            child.destroy()

    colors = {
        "bg": "#b0c6cb",
        "frame": "#E8E8E8",
        "accent": "#3A7CA5",
        "accent_hover": "#2E6A8C",
        "text_dark": "#000000",
    }

    app.main_frame.configure(fg_color="#9fafaa")

    profile1_frame = CTkFrame(app.main_frame, width=500, fg_color="#c4c4c4", corner_radius=15)
    profile1_frame.pack(padx=25, pady=15)

    CTkLabel(
        profile1_frame,
        text="⚙️ SETTINGS",
        font=("tahoma", 32, "bold"),
        text_color=colors["text_dark"],
    ).pack(pady=(10, 20))

    profile_frame = CTkFrame(profile1_frame, fg_color=colors["frame"], corner_radius=15)
    profile_frame.pack(padx=25, pady=15, fill="x")

    CTkLabel(
        profile_frame,
        text="👤 User Profile",
        font=("tahoma", 22, "bold"),
        text_color=colors["text_dark"],
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 5))

    CTkLabel(
        profile_frame,
        text="Username:",
        font=("tahoma", 15),
        text_color=colors["text_dark"],
    ).grid(row=1, column=0, sticky="w", padx=25, pady=5)
    name_entry = CTkEntry(profile_frame, width=250)
    name_entry.insert(0, "self.username")
    name_entry.grid(row=1, column=1, padx=20, pady=5, sticky="e")

    CTkLabel(
        profile_frame,
        text="Email:",
        font=("tahoma", 15),
        text_color=colors["text_dark"],
    ).grid(row=2, column=0, sticky="w", padx=25, pady=5)
    email_entry = CTkEntry(profile_frame, width=250)
    email_entry.insert(0, "self.email")
    email_entry.grid(row=2, column=1, padx=20, pady=(5, 20), sticky="e")

    personal_frame = CTkFrame(profile1_frame, fg_color=colors["frame"], corner_radius=15)
    personal_frame.pack(padx=25, pady=15, fill="x")

    CTkLabel(
        personal_frame,
        text="🎨 Personalization",
        font=("tahoma", 22, "bold"),
        text_color=colors["text_dark"],
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 5))

    from tkinter import StringVar, BooleanVar

    theme_var = StringVar(value="Light")
    CTkLabel(
        personal_frame,
        text="Theme:",
        font=("tahoma", 15),
        text_color=colors["text_dark"],
    ).grid(row=1, column=0, sticky="w", padx=25, pady=5)

    CTkOptionMenu(
        personal_frame,
        variable=theme_var,
        values=["Light", "Dark"],
        fg_color=colors["accent"],
        button_color=colors["accent_hover"],
        dropdown_fg_color="#E8E8E8",
        dropdown_hover_color="#b0c6cb",
        dropdown_text_color="black",
        text_color="black",
    ).grid(row=1, column=1, padx=20, pady=(10, 5), sticky="e")

    color_var = StringVar(value="Blue")
    CTkLabel(
        personal_frame,
        text="Accent Color:",
        font=("tahoma", 15),
        text_color=colors["text_dark"],
    ).grid(row=2, column=0, sticky="w", padx=25, pady=5)

    CTkOptionMenu(
        personal_frame,
        variable=color_var,
        values=["Blue", "Green", "Purple", "Orange"],
        fg_color=colors["accent"],
        button_color=colors["accent_hover"],
        dropdown_fg_color="#E8E8E8",
        dropdown_hover_color="#b0c6cb",
        dropdown_text_color="black",
        text_color="black",
    ).grid(row=2, column=1, padx=20, pady=5, sticky="e")

    font_var = StringVar(value="Medium")
    CTkLabel(
        personal_frame,
        text="Font Size:",
        font=("tahoma", 15),
        text_color=colors["text_dark"],
    ).grid(row=3, column=0, sticky="w", padx=25, pady=5)

    CTkOptionMenu(
        personal_frame,
        variable=font_var,
        values=["Small", "Medium", "Large"],
        fg_color=colors["accent"],
        button_color=colors["accent_hover"],
        dropdown_fg_color="#E8E8E8",
        dropdown_hover_color="#b0c6cb",
        dropdown_text_color="black",
        text_color="black",
    ).grid(row=3, column=1, padx=20, pady=(5, 20), sticky="e")

    system_frame = CTkFrame(profile1_frame, fg_color=colors["frame"], corner_radius=15)
    system_frame.pack(padx=25, pady=15, fill="x")

    CTkLabel(
        system_frame,
        text="🖥️ System Settings",
        font=("tahoma", 22, "bold"),
        text_color=colors["text_dark"],
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 5))

    notif_var = BooleanVar(value=True)
    CTkCheckBox(
        system_frame,
        text="Enable Notifications",
        font=("tahoma", 15),
        text_color="black",
        variable=notif_var,
    ).grid(row=1, column=0, sticky="w", padx=25, pady=(10, 5))

    autosave_var = BooleanVar(value=True)
    CTkCheckBox(
        system_frame,
        text="Auto-Save Progress",
        font=("tahoma", 15),
        text_color="black",
        variable=autosave_var,
    ).grid(row=2, column=0, sticky="w", padx=25, pady=(5, 20))

    button_frame = CTkFrame(profile1_frame, fg_color="transparent")
    button_frame.pack(pady=20)

    def save_settings():
        messagebox.showinfo("✅ Saved", "Settings saved!")

    def reset_defaults():
        theme_var.set("Light")
        color_var.set("Blue")
        font_var.set("Medium")
        notif_var.set(True)
        autosave_var.set(True)
        messagebox.showinfo("Reset", "Settings have been reset to default values.")

    CTkButton(
        button_frame,
        text="Save Changes",
        fg_color=colors["accent"],
        hover_color=colors["accent_hover"],
        height=30,
        font=("tahoma", 16),
        text_color="black",
        width=220,
        command=save_settings,
    ).grid(row=0, column=0, padx=10)

    CTkButton(
        button_frame,
        text="Reset Defaults",
        text_color="black",
        fg_color=colors["accent"],
        hover_color=colors["accent_hover"],
        height=30,
        font=("tahoma", 16),
        width=220,
        command=reset_defaults,
    ).grid(row=0, column=1, padx=10)
