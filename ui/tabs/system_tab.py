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

class SystemTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.is_small_screen = get_is_small_screen()
        
        # Ленивая инициализация менеджеров
        self._managers = {}
        
        # Только touchscreen_manager нужен сразу для отображения статуса
        self.touchscreen_manager = TouchscreenManager()
        self.touchscreen_manager.log_signal.connect(self.log_signal.emit)
        self.touchscreen_manager.status_signal.connect(self.update_touchscreen_button)
        self.touchscreen_manager.start()
        
        self.init_ui()
        
    def get_manager(self, manager_name):
        """Ленивая загрузка менеджеров"""
        if manager_name not in self._managers:
            if manager_name == 'reboot':
                self._managers[manager_name] = RebootManager(self)
            elif manager_name == 'device':
                self._managers[manager_name] = DeviceManager(self)
            elif manager_name == 'network':
                self._managers[manager_name] = NetworkManager(self)
            elif manager_name == 'cleanup':
                self._managers[manager_name] = CleanupManager(self)
            elif manager_name == 'iiko':
                self._managers[manager_name] = IikoManager(self)
            elif manager_name == 'rndis':
                self._managers[manager_name] = RndisManager(self)
                
            if manager_name in self._managers:
                self._managers[manager_name].log_signal.connect(self.log_signal.emit)
                
        return self._managers.get(manager_name)
        
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
            ("Отключить\nзащиту", self.disable_security, False),
            ("Папка\nавтозагрузки", self.open_startup, False),
            ("Панель\nуправления", self.open_control_panel, False),
            ("Перезапуск\nдисп. печати", self.restart_print_spooler, False),
            ("Очистка\nочереди печати", self.clear_print_queue, False),
            ("Настройка\nTLS 1.2", self.configure_tls, False),
            ("Перезапуск\nRNDIS", self.toggle_internet_sharing, False)
        ]
        
        self.button_widgets = {}
        
        for i, (text, handler, is_toggle) in enumerate(buttons_data):
            row = i // buttons_per_row
            col = i % buttons_per_row
            
            button = self.create_button(text, False, is_toggle=is_toggle)
            button.clicked.connect(handler)
            
            # Специальные стили для некоторых кнопок
            if "Ребут\nсенсорного" in text or "Перезапуск\nRNDIS" in text:
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
        manager = self.get_manager('reboot')
        if manager:
            manager.request_reboot()
        
    def open_services(self):
        manager = self.get_manager('device')
        if manager:
            manager.open_services()
        
    def clean_temp_files(self):
        manager = self.get_manager('cleanup')
        if manager:
            manager.clean_temp_files()
        
    def restart_com_ports(self):
        manager = self.get_manager('iiko')
        if manager:
            manager.restart_com_ports()
        
    def disable_security(self):
        manager = self.get_manager('cleanup')
        if manager:
            manager.disable_windows_defender()
        
    def open_startup(self):
        manager = self.get_manager('cleanup')
        if manager:
            manager.open_startup_folder()
        
    def open_control_panel(self):
        manager = self.get_manager('cleanup')
        if manager:
            manager.open_control_panel()
        
    def restart_print_spooler(self):
        manager = self.get_manager('cleanup')
        if manager:
            manager.restart_print_spooler()
        
    def clear_print_queue(self):
        manager = self.get_manager('cleanup')
        if manager:
            manager.clear_print_queue()
        
    def configure_tls(self):
        manager = self.get_manager('cleanup')
        if manager:
            manager.configure_tls()
        
    def toggle_internet_sharing(self):
        manager = self.get_manager('rndis')
        if manager:
            manager.toggle_internet_sharing()
        
    def cleanup(self):
        if self.touchscreen_manager.is_disabled:
            self.touchscreen_manager.enable_touchscreen()