import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIRES SmartTerminal")
        self.setFixedSize(500, 400)
        self.setWindowIcon(QIcon("Logo.ico"))

        layout = QVBoxLayout()

        logo = QLabel()
        logo.setPixmap(QPixmap("Logo.png").scaledToWidth(150, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        title = QLabel("AIRES SmartTerminal")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        start_button = QPushButton("Launch Camera")
        start_button.setFixedHeight(40)
        start_button.setFont(QFont("Arial", 12))
        start_button.clicked.connect(self.open_camera)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(start_button)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def open_camera(self):
        from smart_terminal_camera import SmartTerminalApp
        self.cam_window = SmartTerminalApp()
        self.cam_window.showMaximized()
        self.cam_window.setWindowIcon(QIcon("Logo.ico"))
        self.cam_window.show()
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec_())
