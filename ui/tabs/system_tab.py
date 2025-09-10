from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from managers.touchscreen_manager import TouchscreenManager
from managers.reboot_manager import RebootManager
from managers.device_manager import DeviceManager
from managers.network_manager import NetworkManager
from managers.cleanup_manager import CleanupManager
from managers.iiko_manager import IikoManager
from managers.rndis_manager import RndisManager
from config import LAYOUT_PARAMS, get_is_small_screen
from simple_startup import autostart_is_enabled, autostart_enable, autostart_disable

class SystemTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.is_small_screen = get_is_small_screen()
        
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

        # RNDIS/Internet sharing manager
        self.rndis_manager = RndisManager(self)
        self.rndis_manager.log_signal.connect(self.log_signal.emit)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        margins = LAYOUT_PARAMS['content_margins']
        spacing = LAYOUT_PARAMS['content_spacing']
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(spacing)
        
        title = QLabel("Системные функции")
        title_size = 16 if self.is_small_screen else 18
        title.setStyleSheet(f"""
            QLabel {{
                color: #ffffff;
                font-size: {title_size}px;
                font-weight: 500;
                padding-bottom: 5px;
            }}
        """)
        layout.addWidget(title)
        
        # Адаптивные размеры контейнера кнопок
        buttons_per_row = LAYOUT_PARAMS['buttons_per_row']
        button_width = LAYOUT_PARAMS['button_width']
        button_height = LAYOUT_PARAMS['button_height']
        
        # Рассчитываем размер контейнера на основе количества кнопок
        container_width = buttons_per_row * button_width + (buttons_per_row - 1) * 5  # 5px spacing
        container_height = 200 if not self.is_small_screen else 160
        
        buttons_container = QWidget()
        buttons_container.setFixedSize(container_width, container_height)
        buttons_container.setStyleSheet("QWidget { background-color: transparent; }")
        
        grid = QGridLayout(buttons_container)
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)
        
        # Создаем кнопки с адаптивным расположением
        buttons_data = [
            ("Сенсорный\nэкран", self.toggle_touchscreen, True),  # is_toggle = True
            ("Ребут\nсенсорного", self.reboot_touchscreen, False),
            ("Перезагрузка\nсистемы", self.request_reboot, False),
            ("Очистка\nTemp файлов", self.clean_temp_files, False),
            ("Перезапуск\nCOM портов", self.restart_com_ports, False),
            ("Управление\nслужбами", self.open_services, False),
            ("Отключить\nзащиту", self.disable_security, True),
            ("Папка\nавтозагрузки", self.open_startup, False),
            ("Панель\nуправления", self.open_control_panel, False),
            ("Перезапуск\nдисп. печати", self.restart_print_spooler, False),
            ("Очистка\nочереди печати", self.clear_print_queue, False),
            ("Настройка\nTLS 1.2", self.configure_tls, False),
            # RNDIS удалён
]
        # Кнопка автозапуска перенесена в хедер
        
        self.button_widgets = {}
        
        for i, (text, handler, is_toggle) in enumerate(buttons_data):
            row = i // buttons_per_row
            col = i % buttons_per_row
            
            is_active = False
            # Initialize state for Autostart toggle by handler identity
            if is_toggle and handler == self.toggle_autostart:
                try:
                    is_active = autostart_is_enabled()
                except Exception:
                    is_active = False
            if is_toggle and ("Автозапуск" in text):
                try:
                    is_active = autostart_is_enabled()
                except Exception:
                    is_active = False
            try:
                from managers.cleanup_manager import CleanupManager  # type: ignore
                if is_toggle and handler == self.disable_security:
                    is_active = self.cleanup_manager.is_security_enabled()
            except Exception:
                pass
            button = self.create_button(text, is_active, is_toggle=is_toggle)
            button.clicked.connect(handler)
            
            # Специальные стили для некоторых кнопок
            if "Ребут\nсенсорного" in text or "Перезапуск\n" in text:
                button.setStyleSheet(self.get_special_button_style())
            
            grid.addWidget(button, row, col)
            
            # Сохраняем ссылку на кнопку сенсорного экрана для обновления
            if "Сенсорный\nэкран" in text:
                self.touchscreen_button = button
            
            self.button_widgets[text] = button
        
        layout.addWidget(buttons_container)
        layout.addStretch()
        
    def create_button(self, text, is_active, enabled=True, is_toggle=False):
        button = QPushButton(text)
        button_width = LAYOUT_PARAMS['button_width']
        button_height = LAYOUT_PARAMS['button_height']
        button.setFixedSize(button_width, button_height)
        button.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)
        button.setEnabled(enabled)
        self.update_button_style(button, is_active, enabled, is_toggle)
        return button
        
    def update_button_style(self, button, is_active, enabled=True, is_toggle=False):
        font_size = 10 if self.is_small_screen else 11
        
        if not enabled:
            style = f"""
                QPushButton {{
                    background-color: #0f0f0f;
                    border: 1px solid #1a1a1a;
                    border-radius: 4px;
                    color: #404040;
                    font-size: {font_size}px;
                    font-weight: 500;
                    padding: 4px 2px;
                }}
            """
        elif is_toggle:
            if is_active:
                style = f"""
                    QPushButton {{
                        background-color: #065f46;
                        border: 1px solid #10b981;
                        border-radius: 4px;
                        color: #10b981;
                        font-size: {font_size}px;
                        font-weight: 500;
                        padding: 4px 2px;
                    }}
                    QPushButton:hover {{
                        background-color: #047857;
                        border-color: #34d399;
                    }}
                    QPushButton:pressed {{
                        background-color: #064e3b;
                    }}
                """
            else:
                style = f"""
                    QPushButton {{
                        background-color: #7f1d1d;
                        border: 1px solid #ef4444;
                        border-radius: 4px;
                        color: #ef4444;
                        font-size: {font_size}px;
                        font-weight: 500;
                        padding: 4px 2px;
                    }}
                    QPushButton:hover {{
                        background-color: #991b1b;
                        border-color: #f87171;
                    }}
                    QPushButton:pressed {{
                        background-color: #7f1d1d;
                    }}
                """
        else:
            style = f"""
                QPushButton {{
                    background-color: #2a2a2a;
                    border: 1px solid #3a3a3a;
                    border-radius: 4px;
                    color: #e0e0e0;
                    font-size: {font_size}px;
                    font-weight: 500;
                    padding: 4px 2px;
                }}
                QPushButton:hover {{
                    background-color: #3a3a3a;
                    border-color: #4a4a4a;
                }}
                QPushButton:pressed {{
                    background-color: #1a1a1a;
                }}
            """
        button.setStyleSheet(style)
        
    def get_special_button_style(self):
        """Стиль для специальных кнопок (синие)"""
        font_size = 10 if self.is_small_screen else 11
        return f"""
            QPushButton {{
                background-color: #1e40af;
                border: 1px solid #3b82f6;
                border-radius: 4px;
                color: #3b82f6;
                font-size: {font_size}px;
                font-weight: 500;
                padding: 4px 2px;
            }}
            QPushButton:hover {{
                background-color: #1d4ed8;
                border-color: #60a5fa;
            }}
            QPushButton:pressed {{
                background-color: #1e3a8a;
            }}
        """
        
    def update_touchscreen_button(self, is_disabled):
        if hasattr(self, 'touchscreen_button'):
            self.update_button_style(self.touchscreen_button, not is_disabled, True, is_toggle=True)
        
    def toggle_touchscreen(self):
        self.touchscreen_manager.toggle_touchscreen()
        
    def reboot_touchscreen(self):
        self.touchscreen_manager.reboot_touchscreen()
        
    def request_reboot(self):
        self.reboot_manager.request_reboot()
        
    def open_services(self):
        self.device_manager.open_services()
        
    def clean_temp_files(self):
        self.cleanup_manager.clean_temp_files()
        
    def restart_com_ports(self):
        self.iiko_manager.restart_com_ports()
        
    def disable_security(self):
        # Тумблер защиты (Defender+Firewall)
        try:
            btn = None
            try:
                btn = self.sender()
            except Exception:
                btn = None
            self.cleanup_manager.toggle_security()
            active = False
            try:
                active = self.cleanup_manager.is_security_enabled()
            except Exception:
                active = False
            if btn is not None:
                self.update_button_style(btn, active, True, is_toggle=True)
        except Exception:
            pass
        self.cleanup_manager.configure_tls()
        
    def open_startup(self):
        # Открыть папку автозагрузки пользователя
        try:
            self.cleanup_manager.open_startup_folder()
        except Exception:
            pass

    def toggle_internet_sharing(self):
        # Use RNDIS manager to toggle internet sharing
        self.rndis_manager.toggle_internet_sharing()

    def open_control_panel(self):
        # Delegate to cleanup manager implementation
        try:
            self.cleanup_manager.open_control_panel()
        except Exception:
            pass

    def restart_print_spooler(self):
        # Delegate to cleanup manager implementation
        try:
            self.cleanup_manager.restart_print_spooler()
        except Exception:
            pass

    def clear_print_queue(self):
        # Delegate to cleanup manager implementation
        try:
            self.cleanup_manager.clear_print_queue()
        except Exception:
            pass

    def configure_tls(self):
        # Delegate to cleanup manager implementation
        try:
            self.cleanup_manager.configure_tls()
        except Exception:
            pass
        
    def toggle_autostart(self):
        try:
            btn = None
            try:
                btn = self.sender()
            except Exception:
                btn = None
            current = autostart_is_enabled()
            if current:
                ok = autostart_disable()
                if ok:
                    if btn is not None:
                        self.update_button_style(btn, False, True, is_toggle=True)
                    self.log_signal.emit("Автозапуск: выключен", "info")
                else:
                    self.log_signal.emit("Автозапуск: не удалось выключить", "error")
            else:
                ok = autostart_enable()
                if ok:
                    if btn is not None:
                        self.update_button_style(btn, True, True, is_toggle=True)
                    self.log_signal.emit("Автозапуск: включен", "success")
                else:
                    self.log_signal.emit("Автозапуск: не удалось включить", "error")
        except Exception as e:
            self.log_signal.emit(f"Ошибка автозапуска: {e}", "error")

    def cleanup(self):
        if self.touchscreen_manager.is_disabled:
            self.touchscreen_manager.enable_touchscreen()

