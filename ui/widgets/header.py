from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import QDateTime, QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QFocusEvent
from ui.styles import HEADER_STYLE, LOGO_STYLE
from config import LAYOUT_PARAMS, get_is_small_screen
from simple_startup import autostart_is_enabled, autostart_enable, autostart_disable

class HeaderWidget(QFrame):
    search_text_changed = pyqtSignal(str)
    search_focus_gained = pyqtSignal()
    search_focus_lost = pyqtSignal()
    search_position_requested = pyqtSignal(int, int)
    exit_requested = pyqtSignal()
    check_updates_requested = pyqtSignal()
    autostart_toggled = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.is_small_screen = get_is_small_screen()
        self.init_ui()
        
    def init_ui(self):
        # Адаптивная высота заголовка
        header_height = LAYOUT_PARAMS['header_height']
        self.setFixedHeight(header_height)
        self.setStyleSheet(HEADER_STYLE)
        
        layout = QHBoxLayout(self)
        # Адаптивные отступы
        margin = 15 if not self.is_small_screen else 10
        layout.setContentsMargins(margin, 0, margin, 0)
        
        # Логотип с адаптивным размером
        logo_label = QLabel("bobrik")
        logo_style = LOGO_STYLE
        if self.is_small_screen:
            logo_style = logo_style.replace("24px", "20px")
        logo_label.setStyleSheet(logo_style)
        
        # Версия
        version_label = QLabel("v1.1.4")
        version_size = 12 if self.is_small_screen else 14
        version_label.setStyleSheet(f"""
            QLabel {{
                color: #606060;
                font-size: {version_size}px;
                margin-left: {8 if self.is_small_screen else 10}px;
            }}
        """)
        
        # Строка поиска с адаптивным размером
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск... (Ctrl+K)" if self.is_small_screen else "🔍 Поиск функций... (Ctrl+K)")
        
        # Адаптивные размеры поиска
        search_width = 220 if self.is_small_screen else 280
        search_height = 30 if self.is_small_screen else 35
        search_font_size = 11 if self.is_small_screen else 12
        
        self.search_input.setFixedSize(search_width, search_height)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.on_search_return)
        self.search_input.focus_gained.connect(self.search_focus_gained.emit)
        self.search_input.focus_lost.connect(self.search_focus_lost.emit)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: {6 if self.is_small_screen else 8}px {10 if self.is_small_screen else 12}px;
                color: #e0e0e0;
                font-size: {search_font_size}px;
                font-weight: 400;
            }}
            QLineEdit:focus {{
                border-color: #3b82f6;
                background-color: #262626;
            }}
            QLineEdit:hover {{
                border-color: #4a4a4a;
            }}
        """)
        
        # Время с адаптивным размером
        self.time_label = QLabel()
        time_font_size = 12 if self.is_small_screen else 14
        self.time_label.setStyleSheet(f"""
            QLabel {{
                color: #808080;
                font-size: {time_font_size}px;
            }}
        """)
        
        # Кнопки с адаптивными размерами
        button_size = 30 if self.is_small_screen else 35
        button_font_size = 12 if self.is_small_screen else 14
        
        # Кнопка проверки обновлений
        self.update_button = QPushButton("🔄")
        self.update_button.setFixedSize(button_size, button_size)
        self.update_button.setToolTip("Проверить обновления")
        self.update_button.clicked.connect(self.check_updates_requested.emit)
        self.update_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                color: #808080;
                font-size: {button_font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #10b981;
                border-color: #10b981;
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: #059669;
            }}
        """)

        # Autostart toggle
        self.autostart_button = QPushButton("A")
        self.autostart_button.setFixedSize(button_size, button_size)
        self.autostart_button.setToolTip("Автозапуск: вкл/выкл")
        self.autostart_button.clicked.connect(self.toggle_autostart)
        try:
            self.set_autostart_style(autostart_is_enabled())
        except Exception:
            self.set_autostart_style(False)
        
        # Кнопка выхода
        self.exit_button = QPushButton("✕")
        self.exit_button.setFixedSize(button_size, button_size)
        self.exit_button.clicked.connect(self.exit_requested.emit)
        exit_font_size = button_font_size + 2 if not self.is_small_screen else button_font_size
        self.exit_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                color: #808080;
                font-size: {exit_font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #ef4444;
                border-color: #ef4444;
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: #dc2626;
            }}
        """)
        
        self.update_time()
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        
        # Компоновка элементов
        layout.addWidget(logo_label)
        layout.addWidget(version_label)
        
        # Для маленьких экранов убираем некоторые растяжки
        if not self.is_small_screen:
            layout.addStretch()
        else:
            layout.addSpacing(10)
            
        layout.addWidget(self.search_input)
        
        if not self.is_small_screen:
            layout.addStretch()
        else:
            layout.addSpacing(10)
            
        layout.addWidget(self.time_label)
        layout.addWidget(self.update_button)
        layout.addWidget(self.autostart_button)
        layout.addWidget(self.exit_button)
        
    def on_search_text_changed(self, text):
        self.search_text_changed.emit(text)
        
        if text.strip():
            self.emit_search_position()
        
    def on_search_return(self):
        pass
        
    def emit_search_position(self):
        parent_widget = self.parent()
        if parent_widget:
            search_pos = self.search_input.mapTo(parent_widget, self.search_input.rect().bottomLeft())
            self.search_position_requested.emit(search_pos.x(), search_pos.y() + 5)
        
    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()
        
    def clear_search(self):
        self.search_input.clear()
        
    def get_search_text(self):
        return self.search_input.text()
        
    def update_time(self):
        # Для маленьких экранов сокращенный формат времени
        if self.is_small_screen:
            current_time = QDateTime.currentDateTime().toString("dd.MM HH:mm")
        else:
            current_time = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm:ss")
        self.time_label.setText(current_time)

    # === Автозапуск ===
    def set_autostart_style(self, enabled: bool):
        button_font_size = 12 if self.is_small_screen else 14
        if enabled:
            style = f"""
                QPushButton {{
                    background-color: #065f46;
                    border: 1px solid #10b981;
                    border-radius: 6px;
                    color: #10b981;
                    font-size: {button_font_size}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #047857;
                    border-color: #34d399;
                    color: #ffffff;
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
                    border-radius: 6px;
                    color: #ef4444;
                    font-size: {button_font_size}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #991b1b;
                    border-color: #f87171;
                    color: #ffffff;
                }}
                QPushButton:pressed {{
                    background-color: #7f1d1d;
                }}
            """
        self.autostart_button.setStyleSheet(style)

    def toggle_autostart(self):
        try:
            current = autostart_is_enabled()
            if current:
                ok = autostart_disable()
                if ok:
                    self.set_autostart_style(False)
                    self.autostart_toggled.emit(False)
            else:
                ok = autostart_enable()
                if ok:
                    self.set_autostart_style(True)
                    self.autostart_toggled.emit(True)
        except Exception:
            pass

class SearchLineEdit(QLineEdit):
    focus_gained = pyqtSignal()
    focus_lost = pyqtSignal()
    
    def focusInEvent(self, event: QFocusEvent):
        super().focusInEvent(event)
        self.focus_gained.emit()
        
    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        self.focus_lost.emit()

    # === Автозапуск ===
    def set_autostart_style(self, enabled: bool):
        button_font_size = 12 if self.is_small_screen else 14
        if enabled:
            style = f"""
                QPushButton {{
                    background-color: #065f46;
                    border: 1px solid #10b981;
                    border-radius: 6px;
                    color: #10b981;
                    font-size: {button_font_size}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #047857;
                    border-color: #34d399;
                    color: #ffffff;
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
                    border-radius: 6px;
                    color: #ef4444;
                    font-size: {button_font_size}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #991b1b;
                    border-color: #f87171;
                    color: #ffffff;
                }}
                QPushButton:pressed {{
                    background-color: #7f1d1d;
                }}
            """
        self.autostart_button.setStyleSheet(style)

    def toggle_autostart(self):
        try:
            current = autostart_is_enabled()
            if current:
                ok = autostart_disable()
                if ok:
                    self.set_autostart_style(False)
                    self.autostart_toggled.emit(False)
            else:
                ok = autostart_enable()
                if ok:
                    self.set_autostart_style(True)
                    self.autostart_toggled.emit(True)
        except Exception:
            pass
