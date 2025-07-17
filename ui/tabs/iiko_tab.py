from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from managers.iiko_manager import IikoManager

class IikoTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.iiko_manager = IikoManager(self)
        self.iiko_manager.log_signal.connect(self.log_signal.emit)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        title = QLabel("Управление iiko")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 500;
                padding-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        buttons_container = QWidget()
        buttons_container.setFixedSize(435, 150)
        buttons_container.setStyleSheet("QWidget { background-color: transparent; }")
        
        grid = QGridLayout(buttons_container)
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        close_button = self.create_button("Закрыть\niikoFront", False)
        close_button.clicked.connect(self.close_iiko_front)
        grid.addWidget(close_button, 0, 0)
        
        restart_button = self.create_button("Перезапустить\niikoFront", False)
        restart_button.clicked.connect(self.restart_iiko_front)
        grid.addWidget(restart_button, 0, 1)
        
        update_button = self.create_button("Обновить\niikoCard", False)
        update_button.clicked.connect(self.update_iiko_card)
        grid.addWidget(update_button, 0, 2)
        
        layout.addWidget(buttons_container)
        layout.addStretch()
        
    def create_button(self, text, is_active, enabled=True, is_toggle=False):
        button = QPushButton(text)
        button.setFixedSize(105, 45)
        button.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)
        button.setEnabled(enabled)
        self.update_button_style(button, is_active, enabled, is_toggle)
        return button
        
    def update_button_style(self, button, is_active, enabled=True, is_toggle=False):
        if not enabled:
            style = """
                QPushButton {
                    background-color: #0f0f0f;
                    border: 1px solid #1a1a1a;
                    border-radius: 4px;
                    color: #404040;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 4px 2px;
                }
            """
        else:
            style = """
                QPushButton {
                    background-color: #2a2a2a;
                    border: 1px solid #3a3a3a;
                    border-radius: 4px;
                    color: #e0e0e0;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 4px 2px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    border-color: #4a4a4a;
                }
                QPushButton:pressed {
                    background-color: #1a1a1a;
                }
            """
        button.setStyleSheet(style)
        
    def close_iiko_front(self):
        self.iiko_manager.close_iiko_front()
        
    def restart_iiko_front(self):
        self.iiko_manager.restart_iiko_front()
        
    def update_iiko_card(self):
        self.iiko_manager.update_iiko_card()