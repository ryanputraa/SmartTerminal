import sys
import cv2
import subprocess
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QFileDialog, QCheckBox
)
from PyQt5.QtGui import QImage, QPixmap, QIcon, QPainter, QColor, QFont
from PyQt5.QtCore import QTimer, Qt

class SmartTerminalApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIRES SmartTerminal")
        self.setWindowIcon(QIcon("Logo.ico"))
        self.camera_index = 0
        self.recording = False
        self.cap = None
        self.video_writer = None
        self.last_frame_time = time.time()
        self.frame_times = []
        self.fps = 0

        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.populate_resolutions()  # <-- FIX: Populate resolution options at launch
        self.start_camera()

    def init_ui(self):
        layout = QVBoxLayout()

        top_bar = QHBoxLayout()
        self.back_btn = QPushButton("Back to Home")
        self.back_btn.clicked.connect(self.back_to_home)
        top_bar.addWidget(self.back_btn)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_label, stretch=1)

        control_layout = QHBoxLayout()

        self.camera_selector = QComboBox()
        self.detect_cameras()
        self.camera_selector.currentIndexChanged.connect(self.restart_camera)
        control_layout.addWidget(self.camera_selector)

        self.resolution_selector = QComboBox()
        self.resolution_selector.currentIndexChanged.connect(self.restart_camera)
        control_layout.addWidget(self.resolution_selector)

        self.enable_4k_checkbox = QCheckBox("Enable 4K")
        self.enable_4k_checkbox.stateChanged.connect(lambda: self.update_resolution_list())
        control_layout.addWidget(self.enable_4k_checkbox)

        self.record_btn = QPushButton("Start Recording")
        self.record_btn.clicked.connect(self.toggle_recording)
        control_layout.addWidget(self.record_btn)

        self.snapshot_btn = QPushButton("Take Snapshot")
        self.snapshot_btn.clicked.connect(self.take_snapshot)
        control_layout.addWidget(self.snapshot_btn)

        layout.addLayout(control_layout)
        self.setLayout(layout)

    def detect_cameras(self):
        self.camera_selector.clear()
        index = 0
        try:
            output = subprocess.check_output(
                "ffmpeg -list_devices true -f dshow -i dummy",
                stderr=subprocess.STDOUT, shell=True).decode()
            for line in output.splitlines():
                if "dshow" in line and "video" in line:
                    name = line.split('"')[1]
                    self.camera_selector.addItem(name, index)
                    index += 1
        except Exception as e:
            print("Error detecting cameras:", e)

    def update_resolution_list(self):
        current = self.resolution_selector.currentText()
        self.populate_resolutions()
        for i in range(self.resolution_selector.count()):
            if self.resolution_selector.itemText(i) == current:
                self.resolution_selector.setCurrentIndex(i)
                break

    def populate_resolutions(self):
        self.resolution_selector.clear()
        resolutions = [
            (1920, 1080), (1280, 720), (800, 600), (640, 480), (320, 240)
        ]
        if self.enable_4k_checkbox.isChecked():
            resolutions = [
                (3840, 2160), (2560, 1440)
            ] + resolutions

        for w, h in resolutions:
            self.resolution_selector.addItem(f"{w}x{h}", (w, h))

    def start_camera(self):
        self.camera_index = self.camera_selector.currentData()
        if self.camera_index is None:
            self.camera_index = 0

        resolution_data = self.resolution_selector.currentData()
        if resolution_data:
            w, h = resolution_data
        else:
            w, h = 1920, 1080

        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        self.timer.start(30)

    def restart_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
        self.start_camera()

    def update_frame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                now = time.time()
                self.frame_times.append(now)

                while self.frame_times and now - self.frame_times[0] > 5:
                    self.frame_times.pop(0)

                if len(self.frame_times) > 1:
                    self.fps = len(self.frame_times) / (self.frame_times[-1] - self.frame_times[0])

                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

                pixmap = QPixmap.fromImage(qt_image)
                painter = QPainter(pixmap)
                painter.setPen(QColor("white"))
                painter.setFont(QFont("Arial", 14))
                painter.drawText(10, 30, f"FPS: {self.fps:.1f}")
                painter.end()

                scaled_pixmap = pixmap.scaled(
                    self.video_label.width(),
                    self.video_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.video_label.setPixmap(scaled_pixmap)

                if self.recording and self.video_writer is not None:
                    self.video_writer.write(frame)

    def take_snapshot(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                path, _ = QFileDialog.getSaveFileName(self, "Save Snapshot", "snapshot.jpg", "Images (*.jpg *.png)")
                if path:
                    cv2.imwrite(path, frame)

    def toggle_recording(self):
        if not self.recording:
            current_data = self.resolution_selector.currentData()
            if current_data:
                w, h = current_data
            else:
                w, h = 1920, 1080
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            path, _ = QFileDialog.getSaveFileName(self, "Save Recording", "recording.avi", "Videos (*.avi)")
            if not path:
                return
            self.video_writer = cv2.VideoWriter(path, fourcc, 30.0, (w, h))
            self.recording = True
            self.record_btn.setText("Stop Recording")
        else:
            self.recording = False
            if self.video_writer:
                self.video_writer.release()
            self.video_writer = None
            self.record_btn.setText("Start Recording")

    def back_to_home(self):
        from main_launcher import Launcher
        self.home = Launcher()
        self.home.show()
        self.close()

    def resizeEvent(self, event):
        self.update_frame()
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.timer.stop()
        if self.cap:
            self.cap.release()
        if self.video_writer:
            self.video_writer.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SmartTerminalApp()
    window.show()
    sys.exit(app.exec_())
