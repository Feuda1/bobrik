import datetime
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QTextEdit
from PyQt6.QtGui import QTextCursor
from ui.styles import PANEL_STYLE, CONSOLE_STYLE
from config import COLORS

class ConsolePanel(QFrame):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)  # Уменьшили отступы
        layout.setSpacing(0)  # Убрали промежуток
        
        # Убрали заголовок "Консоль"
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(CONSOLE_STYLE)
        layout.addWidget(self.console)
        
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