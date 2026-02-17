# ai_detector_gui.py
import cv2
import threading
import time
from PIL import Image
from customtkinter import *


# ---------- AI DETECTOR (OpenCV + Haar Cascade) ----------

class AIDetector:
    def __init__(self):
        # Built-in face detector (ships with OpenCV)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def detect(self, frame_bgr):
        """Detect faces in a BGR frame, return annotated frame + count."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(40, 40)
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return frame_bgr, len(faces)


# ---------- CUSTOMTKINTER APP ----------

class GaiaVisionApp(CTk):
    def __init__(self, cam_index=0):
        super().__init__()

        # ---- Gaia Sentinel theme ----
        set_appearance_mode("dark")
        set_default_color_theme("dark-blue")

        self.colors = {
            "bg_primary": "#0f2b2a",
            "panel": "#163836",
            "accent": "#3AD29F",
            "accent_hover": "#2CB587",
            "text": "#E7F6F2",
            "subtext": "#9cc7bc",
        }

        self.title("Gaia Sentinel • Vision AI")
        self.geometry("960x600+150+80")
        self.configure(fg_color=self.colors["bg_primary"])

        # ---- OpenCV camera ----
        self.cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

        self.detector = AIDetector()
        self.running = True
        self.current_img = None   # keep reference so CTkImage isn't GC'ed

        # ---------- LAYOUT ----------

        # root grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        # Video area
        video_frame = CTkFrame(self, fg_color=self.colors["panel"], corner_radius=16)
        video_frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        video_frame.grid_rowconfigure(0, weight=1)
        video_frame.grid_columnconfigure(0, weight=1)

        self.video_label = CTkLabel(video_frame, text="")
        self.video_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Sidebar
        side = CTkFrame(self, fg_color="#122620", corner_radius=16)
        side.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        for r in range(6):
            side.grid_rowconfigure(r, weight=0)
        side.grid_rowconfigure(5, weight=1)

        CTkLabel(
            side, text="Gaia Vision AI",
            font=("Segoe UI Semibold", 24, "bold"),
            text_color=self.colors["text"]
        ).grid(row=0, column=0, padx=16, pady=(18, 4), sticky="w")

        CTkLabel(
            side, text="Real-time detection\npowered by OpenCV",
            font=("Segoe UI", 13),
            text_color=self.colors["subtext"],
            justify="left"
        ).grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        # Detection status labels
        self.status_label = CTkLabel(
            side, text="Status: Initializing…",
            font=("Segoe UI", 13),
            text_color=self.colors["subtext"]
        )
        self.status_label.grid(row=2, column=0, padx=16, pady=(6, 4), sticky="w")

        self.count_label = CTkLabel(
            side, text="Detected: 0",
            font=("Segoe UI", 14, "bold"),
            text_color=self.colors["accent"]
        )
        self.count_label.grid(row=3, column=0, padx=16, pady=(2, 12), sticky="w")

        # Control buttons
        btn_row = CTkFrame(side, fg_color="transparent")
        btn_row.grid(row=4, column=0, padx=12, pady=(8, 12), sticky="ew")
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.pause_btn = CTkButton(
            btn_row, text="Pause",
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            text_color="black",
            command=self.toggle_run,
            corner_radius=10,
            height=32
        )
        self.pause_btn.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        CTkButton(
            btn_row, text="Snapshot",
            fg_color="#F59E0B",
            hover_color="#D97706",
            text_color="black",
            command=self.save_snapshot,
            corner_radius=10,
            height=32
        ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        CTkLabel(
            side,
            text="Tip: This demo detects faces.\n"
                 "You can replace the detector\n"
                 "with your own AI model later.",
            font=("Segoe UI", 11),
            text_color=self.colors["subtext"],
            justify="left"
        ).grid(row=5, column=0, padx=16, pady=(10, 16), sticky="sw")

        # Start capture thread
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- CAMERA + DETECTION LOOP ----------

    def _capture_loop(self):
        while True:
            if not self.running:
                time.sleep(0.05)
                continue

            ret, frame = self.cap.read()
            if not ret:
                self.status_label.configure(text="Status: Camera error")
                break

            # AI detection
            frame, count = self.detector.detect(frame)
            self.status_label.configure(text="Status: Running")
            self.count_label.configure(text=f"Detected: {count}")

            # Convert BGR → RGB → PIL → CTkImage
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = frame_rgb.shape

            # Resize to fit nicely in GUI
            max_w, max_h = 800, 500
            scale = min(max_w / w, max_h / h)
            new_size = (int(w * scale), int(h * scale))
            pil_img = Image.fromarray(frame_rgb).resize(new_size)

            ctk_img = CTkImage(light_image=pil_img, size=new_size)
            self.current_img = ctk_img

            # Update label in UI thread
            self.video_label.configure(image=ctk_img)

            time.sleep(0.03)  # ~30 FPS cap

    # ---------- BUTTON ACTIONS ----------

    def toggle_run(self):
        self.running = not self.running
        if self.running:
            self.status_label.configure(text="Status: Running")
            self.pause_btn.configure(text="Pause")
        else:
            self.status_label.configure(text="Status: Paused")
            self.pause_btn.configure(text="Resume")

    def save_snapshot(self):
        # Grab a fresh frame from camera and save it
        ret, frame = self.cap.read()
        if not ret:
            self.status_label.configure(text="Snapshot failed (no frame)")
            return
        ts = int(time.time())
        filename = f"snapshot_{ts}.jpg"
        cv2.imwrite(filename, frame)
        self.status_label.configure(text=f"Saved: {filename}")

    def on_close(self):
        self.running = False
        try:
            if self.cap and self.cap.isOpened():
                self.cap.release()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = GaiaVisionApp(cam_index=0)  # 0 = default webcam
    app.mainloop()
