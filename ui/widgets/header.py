from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import QDateTime, QTimer
from ui.styles import HEADER_STYLE, LOGO_STYLE

class HeaderWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setFixedHeight(70)
        self.setStyleSheet(HEADER_STYLE)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        logo_label = QLabel("bobrik")
        logo_label.setStyleSheet(LOGO_STYLE)
        
        version_label = QLabel("v1.0")
        version_label.setStyleSheet("""
            QLabel {
                color: #606060;
                font-size: 14px;
                margin-left: 10px;
            }
        """)
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 14px;
            }
        """)
        
        self.update_time()
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        
        layout.addWidget(logo_label)
        layout.addWidget(version_label)
        layout.addStretch()
        layout.addWidget(self.time_label)
        
    def update_time(self):
        current_time = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm:ss")
        self.time_label.setText(current_time)