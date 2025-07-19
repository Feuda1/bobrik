from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QDateTime, QTimer, pyqtSignal
from ui.styles import HEADER_STYLE, LOGO_STYLE

class HeaderWidget(QFrame):
    search_requested = pyqtSignal()
    
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
        
        # Кнопка глобального поиска
        self.search_button = QPushButton("🔍 Поиск")
        self.search_button.setFixedSize(100, 35)
        self.search_button.clicked.connect(self.search_requested.emit)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #1e40af;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                color: #3b82f6;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
                border-color: #60a5fa;
                color: #60a5fa;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
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
        layout.addWidget(self.search_button)
        layout.addWidget(self.time_label)
        
    def update_time(self):
        current_time = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm:ss")
        self.time_label.setText(current_time)