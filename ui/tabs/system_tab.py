from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from managers.touchscreen_manager import TouchscreenManager
from managers.reboot_manager import RebootManager
from managers.device_manager import DeviceManager
from managers.network_manager import NetworkManager

class SystemTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.touchscreen_manager = TouchscreenManager()
        self.touchscreen_manager.log_signal.connect(self.log_signal.emit)
        self.touchscreen_manager.status_signal.connect(self.update_touchscreen_button)
        self.touchscreen_manager.start()
        
        self.reboot_manager = RebootManager(self)
        self.reboot_manager.log_signal.connect(self.log_signal.emit)
        
        self.device_manager = DeviceManager(self)
        self.device_manager.log_signal.connect(self.log_signal.emit)
        
        self.network_manager = NetworkManager(self)
        self.network_manager.log_signal.connect(self.log_signal.emit)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Заголовок
        title = QLabel("Системные функции")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 500;
                padding-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Контейнер для кнопок с фиксированным размером
        buttons_container = QWidget()
        buttons_container.setFixedSize(420, 100)  # Увеличили ширину для 4 кнопок
        buttons_container.setStyleSheet("QWidget { background-color: transparent; }")
        
        # Сетка для кнопок
        grid = QGridLayout(buttons_container)
        grid.setSpacing(1)
        grid.setContentsMargins(0, 0, 0, 0)
        
        # Кнопка сенсорного экрана (переключаемая)
        self.touchscreen_button = self.create_button("Сенсорный\nэкран", False, is_toggle=True)
        self.touchscreen_button.clicked.connect(self.toggle_touchscreen)
        grid.addWidget(self.touchscreen_button, 0, 0)
        
        # Кнопка перезагрузки (обычная)
        self.restart_button = self.create_button("Перезагрузка\nсистемы", False)
        self.restart_button.clicked.connect(self.request_reboot)
        grid.addWidget(self.restart_button, 0, 1)
        
        # Остальные кнопки
        services_button = self.create_button("Управление\nслужбами", False)
        services_button.clicked.connect(self.open_services)
        grid.addWidget(services_button, 0, 2)
        
        # Кнопка ipconfig
        ipconfig_button = self.create_button("IP\nконфигурация", False)
        ipconfig_button.clicked.connect(self.run_ipconfig)
        grid.addWidget(ipconfig_button, 0, 3)
        
        registry_button = self.create_button("Редактор\nреестра", False)
        registry_button.clicked.connect(self.open_registry_editor)
        grid.addWidget(registry_button, 1, 0)
        
        self.devices_button = self.create_button("Диспетчер\nустройств", False)
        self.devices_button.clicked.connect(self.open_device_manager)
        grid.addWidget(self.devices_button, 1, 1)
        
        info_button = self.create_button("Информация\nо системе", False)
        info_button.clicked.connect(self.open_system_info)
        grid.addWidget(info_button, 1, 2)
        
        # Кнопка ping
        ping_button = self.create_button("Ping\nтест", False)
        ping_button.clicked.connect(self.run_ping)
        grid.addWidget(ping_button, 1, 3)
        
        layout.addWidget(buttons_container)
        layout.addStretch()
        
    def create_button(self, text, is_active, enabled=True, is_toggle=False):
        button = QPushButton(text)
        button.setFixedSize(100, 45)
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
        elif is_toggle:
            # Стиль для переключаемых кнопок (красный/зелёный)
            if is_active:
                style = """
                    QPushButton {
                        background-color: #065f46;
                        border: 1px solid #10b981;
                        border-radius: 4px;
                        color: #10b981;
                        font-size: 11px;
                        font-weight: 500;
                        padding: 4px 2px;
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
                        border-radius: 4px;
                        color: #ef4444;
                        font-size: 11px;
                        font-weight: 500;
                        padding: 4px 2px;
                    }
                    QPushButton:hover {
                        background-color: #991b1b;
                        border-color: #f87171;
                    }
                    QPushButton:pressed {
                        background-color: #7f1d1d;
                    }
                """
        else:
            # Стиль для обычных кнопок (нейтральный серый)
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
        
    def update_touchscreen_button(self, is_disabled):
        # is_disabled = True означает, что сенсор выключен, поэтому кнопка красная
        self.update_button_style(self.touchscreen_button, not is_disabled, True, is_toggle=True)
        
    def toggle_touchscreen(self):
        self.touchscreen_manager.toggle_touchscreen()
        
    def request_reboot(self):
        self.reboot_manager.request_reboot()
        
    def open_device_manager(self):
        self.device_manager.open_device_manager()
        
    def open_system_info(self):
        self.device_manager.open_system_info()
        
    def open_registry_editor(self):
        self.device_manager.open_registry_editor()
        
    def open_services(self):
        self.device_manager.open_services()
        
    def run_ipconfig(self):
        self.network_manager.run_ipconfig()
        
    def run_ping(self):
        self.network_manager.run_ping("8.8.8.8", 4)
        
    def cleanup(self):
        if self.touchscreen_manager.is_disabled:
            self.touchscreen_manager.enable_touchscreen()