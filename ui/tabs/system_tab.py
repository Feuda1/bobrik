from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from managers.touchscreen_manager import TouchscreenManager

class SystemTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.touchscreen_manager = TouchscreenManager()
        self.touchscreen_manager.log_signal.connect(self.log_signal.emit)
        self.touchscreen_manager.status_signal.connect(self.update_touchscreen_button)
        self.touchscreen_manager.start()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("Системные функции")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 500;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Сетка для кнопок
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Кнопка сенсорного экрана
        self.touchscreen_button = self.create_button("Сенсорный\nэкран", False)
        self.touchscreen_button.clicked.connect(self.toggle_touchscreen)
        grid.addWidget(self.touchscreen_button, 0, 0)
        
        # Заготовки других кнопок
        restart_button = self.create_button("Перезагрузка\nсистемы", False, enabled=False)
        grid.addWidget(restart_button, 0, 1)
        
        services_button = self.create_button("Управление\nслужбами", False, enabled=False)
        grid.addWidget(services_button, 0, 2)
        
        registry_button = self.create_button("Редактор\nреестра", False, enabled=False)
        grid.addWidget(registry_button, 1, 0)
        
        devices_button = self.create_button("Диспетчер\nустройств", False, enabled=False)
        grid.addWidget(devices_button, 1, 1)
        
        info_button = self.create_button("Информация\nо системе", False, enabled=False)
        grid.addWidget(info_button, 1, 2)
        
        layout.addLayout(grid)
        layout.addStretch()
        
    def create_button(self, text, is_active, enabled=True):
        button = QPushButton(text)
        button.setFixedSize(120, 60)
        button.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)
        button.setEnabled(enabled)
        self.update_button_style(button, is_active, enabled)
        return button
        
    def update_button_style(self, button, is_active, enabled=True):
        if not enabled:
            style = """
                QPushButton {
                    background-color: #0f0f0f;
                    border: 1px solid #1a1a1a;
                    border-radius: 2px;
                    color: #404040;
                    font-size: 12px;
                    font-weight: 500;
                }
            """
        elif is_active:
            style = """
                QPushButton {
                    background-color: #065f46;
                    border: 1px solid #10b981;
                    border-radius: 2px;
                    color: #10b981;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #047857;
                    border-color: #34d399;
                }
                QPushButton:pressed {
                    background-color: #064e3b;
                }
            """
        else:
            style = """
                QPushButton {
                    background-color: #7f1d1d;
                    border: 1px solid #ef4444;
                    border-radius: 2px;
                    color: #ef4444;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #991b1b;
                    border-color: #f87171;
                }
                QPushButton:pressed {
                    background-color: #7f1d1d;
                }
            """
        button.setStyleSheet(style)
        
    def update_touchscreen_button(self, is_disabled):
        # is_disabled = True означает, что сенсор выключен, поэтому кнопка красная
        self.update_button_style(self.touchscreen_button, not is_disabled, True)
        
    def toggle_touchscreen(self):
        self.touchscreen_manager.toggle_touchscreen()
        
    def cleanup(self):
        if self.touchscreen_manager.is_disabled:
            self.touchscreen_manager.enable_touchscreen()