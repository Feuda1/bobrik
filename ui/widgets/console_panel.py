import datetime
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt
from ui.styles import PANEL_STYLE, CONSOLE_STYLE
from config import COLORS

class ConsolePanel(QFrame):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Кнопка очистки консоли
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        clear_button = QPushButton("Очистить")
        clear_button.setFixedSize(70, 25)
        clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_button.clicked.connect(self.clear_console)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(clear_button)
        layout.addLayout(button_layout)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(CONSOLE_STYLE)
        layout.addWidget(self.console)
        
    def clear_console(self):
        """Очищает консоль"""
        self.console.clear()
        self.add_log("Консоль очищена", "info")
        
    def add_log(self, message, log_type="info"):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        color = COLORS.get(log_type, COLORS['text_secondary'])
        if log_type == "info":
            color = COLORS['info']
        elif log_type == "success":
            color = COLORS['success']
        elif log_type == "error":
            color = COLORS['error']
        elif log_type == "warning":
            color = COLORS['warning']
            
        formatted_message = f'<span style="color: {COLORS["timestamp"]}">[{timestamp}]</span> <span style="color: {color}">{message}</span>'
        
        self.console.append(formatted_message)
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console.setTextCursor(cursor)