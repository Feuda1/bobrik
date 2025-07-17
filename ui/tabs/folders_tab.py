from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from managers.logs_manager import LogsManager

class FoldersTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.logs_manager = LogsManager(self)
        self.logs_manager.log_signal.connect(self.log_signal.emit)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        title = QLabel("Открытие папок")
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
        
        entities_button = self.create_button("EntitiesStorage", False)
        entities_button.clicked.connect(lambda: self.open_folder("entities_storage"))
        grid.addWidget(entities_button, 0, 0)
        
        plugin_button = self.create_button("PluginConfig", False)
        plugin_button.clicked.connect(lambda: self.open_folder("plugin_configs"))
        grid.addWidget(plugin_button, 0, 1)
        
        logs_button = self.create_button("Logs", False)
        logs_button.clicked.connect(lambda: self.open_folder("logs"))
        grid.addWidget(logs_button, 0, 2)
        
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
        
    def open_folder(self, folder_type):
        self.logs_manager.open_folder(folder_type)