import cv2
import tkinter as tk
from tkinter import ttk, filedialog
from threading import Thread
import datetime
import os
from PIL import Image, ImageTk
import subprocess

class SmartTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartTerminal Webcam")
        self.root.geometry("800x600")
        self.root.update_idletasks()
        self.root.minsize(640, 480)
        self.root.configure(bg="black")

        self.capture = None
        self.current_cam_index = 0
        self.running = False
        self.recording = False
        self.out = None

        # UI Setup
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<Configure>', self.on_resize)

        control_frame = tk.Frame(self.root, bg="black")
        control_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.cam_selector = ttk.Combobox(control_frame, state="readonly")
        self.cam_selector.pack(side=tk.LEFT, padx=5)
        self.cam_selector.bind("<<ComboboxSelected>>", self.change_camera)

        self.record_btn = tk.Button(control_frame, text="Start Recording", command=self.toggle_recording)
        self.record_btn.pack(side=tk.LEFT, padx=5)

        self.snapshot_btn = tk.Button(control_frame, text="Take Picture", command=self.take_snapshot)
        self.snapshot_btn.pack(side=tk.LEFT, padx=5)

        self.display_width = 640
        self.display_height = 480
        self.frame_width = 640
        self.frame_height = 480

        self.cam_indices = []
        self.cam_names = []
        self.detect_cameras()
        self.start_camera(self.current_cam_index)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def detect_cameras(self):
        index = 0
        available = []
        self.cam_indices = []
        self.cam_names = []

        while index < 10:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                name = self.get_device_name(index)
                self.cam_indices.append(index)
                self.cam_names.append(name)
                available.append(name)
                cap.release()
            index += 1

        if not available:
            available = ["No Cameras Found"]

        self.cam_selector['values'] = available
        self.cam_selector.current(0)

    def get_device_name(self, index):
        try:
            result = subprocess.run(
                ["ffmpeg", "-f", "dshow", "-list_devices", "true", "-i", "dummy"],
                stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True
            )
            lines = result.stderr.split('\n')
            device_lines = [line for line in lines if "DirectShow video devices" in line or "" in line]
            names = [line.strip().split('"')[1] for line in lines if '"' in line and 'video devices' not in line]
            return names[index] if index < len(names) else f"Camera {index}"
        except:
            return f"Camera {index}"

    def start_camera(self, index):
        if self.capture:
            self.capture.release()

        actual_index = self.cam_indices[index] if index < len(self.cam_indices) else 0
        self.capture = cv2.VideoCapture(actual_index, cv2.CAP_DSHOW)

        # Allow camera to initialize
        for _ in range(10):
            self.capture.read()

        # Get actual resolution
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width > 0 and height > 0:
            self.frame_width = width
            self.frame_height = height

        self.running = True
        Thread(target=self.update_frame, daemon=True).start()

    def update_frame(self):
        while self.running:
            ret, frame = self.capture.read()
            if ret:
                self.last_frame = frame.copy()
                self.root.after_idle(self.display_frame, frame)

                if self.recording and self.out:
                    self.out.write(frame)

    def display_frame(self, frame):
        aspect_ratio = self.frame_width / self.frame_height
        canvas_width = self.display_width
        canvas_height = self.display_height
        canvas_ratio = canvas_width / canvas_height

        if canvas_ratio > aspect_ratio:
            new_height = canvas_height
            new_width = int(aspect_ratio * new_height)
        else:
            new_width = canvas_width
            new_height = int(new_width / aspect_ratio)

        resized = cv2.resize(frame, (new_width, new_height))
        rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(rgb_frame)
        img_tk = ImageTk.PhotoImage(img_pil)

        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width // 2, canvas_height // 2,
            image=img_tk, anchor=tk.CENTER
        )
        self.canvas.image = img_tk

    def on_resize(self, event):
        self.display_width = event.width
        self.display_height = event.height

    def change_camera(self, event):
        index = self.cam_selector.current()
        self.current_cam_index = index
        self.start_camera(index)

    def take_snapshot(self):
        if hasattr(self, 'last_frame'):
            filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[["PNG Files", "*.png"]])
            if filename:
                cv2.imwrite(filename, self.last_frame)

    def toggle_recording(self):
        if not self.recording:
            filename = filedialog.asksaveasfilename(defaultextension=".avi", filetypes=[["AVI Files", "*.avi"]])
            if filename:
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                fps = 20.0
                width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
                self.recording = True
                self.record_btn.config(text="Stop Recording")
        else:
            self.recording = False
            if self.out:
                self.out.release()
                self.out = None
            self.record_btn.config(text="Start Recording")

    def on_closing(self):
        self.running = False
        if self.capture:
            self.capture.release()
        if self.recording and self.out:
            self.out.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartTerminal(root)
    root.mainloop()