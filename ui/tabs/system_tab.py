from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from managers.touchscreen_manager import TouchscreenManager
from managers.reboot_manager import RebootManager
from managers.device_manager import DeviceManager
from managers.network_manager import NetworkManager
from managers.cleanup_manager import CleanupManager
from managers.iiko_manager import IikoManager
from managers.rndis_manager import RndisManager

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
        
        self.cleanup_manager = CleanupManager(self)
        self.cleanup_manager.log_signal.connect(self.log_signal.emit)
        
        self.iiko_manager = IikoManager(self)
        self.iiko_manager.log_signal.connect(self.log_signal.emit)
        
        self.rndis_manager = RndisManager(self)
        self.rndis_manager.log_signal.connect(self.log_signal.emit)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
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
        
        buttons_container = QWidget()
        buttons_container.setFixedSize(645, 200)
        buttons_container.setStyleSheet("QWidget { background-color: transparent; }")
        
        grid = QGridLayout(buttons_container)
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)
        
        self.touchscreen_button = self.create_button("Сенсорный\nэкран", False, is_toggle=True)
        self.touchscreen_button.clicked.connect(self.toggle_touchscreen)
        grid.addWidget(self.touchscreen_button, 0, 0)
        
        self.restart_button = self.create_button("Перезагрузка\nсистемы", False)
        self.restart_button.clicked.connect(self.request_reboot)
        grid.addWidget(self.restart_button, 0, 1)
        
        cleanup_button = self.create_button("Очистка\nTemp файлов", False)
        cleanup_button.clicked.connect(self.clean_temp_files)
        grid.addWidget(cleanup_button, 0, 2)
        
        com_button = self.create_button("Перезапуск\nCOM портов", False)
        com_button.clicked.connect(self.restart_com_ports)
        grid.addWidget(com_button, 0, 3)
        
        services_button = self.create_button("Управление\nслужбами", False)
        services_button.clicked.connect(self.open_services)
        grid.addWidget(services_button, 1, 0)
        
        security_button = self.create_button("Отключить\nзащиту", False)
        security_button.clicked.connect(self.disable_security)
        grid.addWidget(security_button, 1, 1)
        
        startup_button = self.create_button("Папка\nавтозагрузки", False)
        startup_button.clicked.connect(self.open_startup)
        grid.addWidget(startup_button, 1, 2)
        
        control_button = self.create_button("Панель\nуправления", False)
        control_button.clicked.connect(self.open_control_panel)
        grid.addWidget(control_button, 1, 3)
        
        print_restart_button = self.create_button("Перезапуск\nдисп. печати", False)
        print_restart_button.clicked.connect(self.restart_print_spooler)
        grid.addWidget(print_restart_button, 2, 0)
        
        print_clear_button = self.create_button("Очистка\nочереди печати", False)
        print_clear_button.clicked.connect(self.clear_print_queue)
        grid.addWidget(print_clear_button, 2, 1)
        
        tls_button = self.create_button("Настройка\nTLS 1.2", False)
        tls_button.clicked.connect(self.configure_tls)
        grid.addWidget(tls_button, 2, 2)
        
        rndis_button = self.create_button("Перезапуск\nRNDIS", False)
        rndis_button.clicked.connect(self.toggle_internet_sharing)
        rndis_button.setStyleSheet("""
            QPushButton {
                background-color: #1e40af;
                border: 1px solid #3b82f6;
                border-radius: 4px;
                color: #3b82f6;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 2px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
                border-color: #60a5fa;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
            }
        """)
        grid.addWidget(rndis_button, 2, 3)
        
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
        elif is_toggle:
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
        self.update_button_style(self.touchscreen_button, not is_disabled, True, is_toggle=True)
        
    def toggle_touchscreen(self):
        self.touchscreen_manager.toggle_touchscreen()
        
    def request_reboot(self):
        self.reboot_manager.request_reboot()
        
    def open_services(self):
        self.device_manager.open_services()
        
    def clean_temp_files(self):
        self.cleanup_manager.clean_temp_files()
        
    def restart_com_ports(self):
        self.iiko_manager.restart_com_ports()
        
    def disable_security(self):
        self.cleanup_manager.disable_windows_defender()
        
    def open_startup(self):
        self.cleanup_manager.open_startup_folder()
        
    def open_control_panel(self):
        self.cleanup_manager.open_control_panel()
        
    def restart_print_spooler(self):
        self.cleanup_manager.restart_print_spooler()
        
    def clear_print_queue(self):
        self.cleanup_manager.clear_print_queue()
        
    def configure_tls(self):
        self.cleanup_manager.configure_tls()
        
    def toggle_internet_sharing(self):
        self.rndis_manager.toggle_internet_sharing()
        
    def cleanup(self):
        if self.touchscreen_manager.is_disabled:
            self.touchscreen_manager.enable_touchscreen()