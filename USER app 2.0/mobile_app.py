from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import Clock
from kivy.graphics.texture import Texture

import cv2
import datetime
import os
import threading


class CameraWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capture = None
        self.running = False

    def start(self):
        self.capture = cv2.VideoCapture(0)
        self.running = True
        Clock.schedule_interval(self.update, 1 / 30)

    def stop(self):
        self.running = False
        if self.capture:
            self.capture.release()

    def update(self, dt):
        if not self.running:
            return

        ret, frame = self.capture.read()
        if not ret:
            return

        frame = cv2.flip(frame, 0)
        buf = frame.tobytes()
        texture = Texture.create(
            size=(frame.shape[1], frame.shape[0]),
            colorfmt='bgr'
        )
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.texture = texture


class LogBox(TextInput):
    def log(self, text):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.text += f"[{ts}] {text}\n"
        self.cursor = (0, len(self.text))


class MainUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        self.camera = CameraWidget(size_hint=(1, 0.7))
        self.log = LogBox(size_hint=(1, 0.3), readonly=True)

        self.add_widget(self.camera)

        controls = BoxLayout(size_hint=(1, 0.15))

        self.start_btn = Button(text="Start Camera")
        self.capture_btn = Button(text="Capture Frame")
        self.stop_btn = Button(text="Stop Camera")

        self.start_btn.bind(on_press=self.start_camera)
        self.capture_btn.bind(on_press=self.capture_frame)
        self.stop_btn.bind(on_press=self.stop_camera)

        controls.add_widget(self.start_btn)
        controls.add_widget(self.capture_btn)
        controls.add_widget(self.stop_btn)

        self.add_widget(controls)
        self.add_widget(self.log)

    def start_camera(self, *_):
        self.camera.start()
        self.log.log("Camera started")

    def stop_camera(self, *_):
        self.camera.stop()
        self.log.log("Camera stopped")

    def capture_frame(self, *_):
        if not self.camera.capture:
            self.log.log("Camera not running")
            return

        ret, frame = self.camera.capture.read()
        if not ret:
            self.log.log("Failed to capture frame")
            return

        self._open_save_dialog(frame)

    def _open_save_dialog(self, frame):
        chooser = FileChooserIconView()
        popup = Popup(
            title="Save Image",
            content=chooser,
            size_hint=(0.9, 0.9)
        )

        def save_file(instance, selection):
            if selection:
                path = selection[0]
                cv2.imwrite(path, frame)
                self.log.log(f"Image saved: {path}")
                popup.dismiss()

        chooser.bind(on_submit=save_file)
        popup.open()


class GaiaApp(App):
    def build(self):
        return MainUI()


if __name__ == "__main__":
    GaiaApp().run()
