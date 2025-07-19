from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import QDateTime, QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QFocusEvent
from ui.styles import HEADER_STYLE, LOGO_STYLE

class HeaderWidget(QFrame):
    search_text_changed = pyqtSignal(str)
    search_focus_gained = pyqtSignal()
    search_focus_lost = pyqtSignal()
    search_position_requested = pyqtSignal(int, int)  # x, y координаты
    exit_requested = pyqtSignal()  # Сигнал для выхода
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setFixedHeight(70)
        self.setStyleSheet(HEADER_STYLE)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # Логотип
        logo_label = QLabel("bobrik")
        logo_label.setStyleSheet(LOGO_STYLE)
        
        # Версия
        version_label = QLabel("v1.0")
        version_label.setStyleSheet("""
            QLabel {
                color: #606060;
                font-size: 14px;
                margin-left: 10px;
            }
        """)
        
        # Строка поиска
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск функций... (Ctrl+K)")
        self.search_input.setFixedSize(280, 35)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.on_search_return)
        self.search_input.focus_gained.connect(self.search_focus_gained.emit)
        self.search_input.focus_lost.connect(self.search_focus_lost.emit)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e0e0e0;
                font-size: 12px;
                font-weight: 400;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background-color: #262626;
            }
            QLineEdit:hover {
                border-color: #4a4a4a;
            }
        """)
        
        # Время
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 14px;
            }
        """)
        
        # Кнопка выхода
        self.exit_button = QPushButton("✕")
        self.exit_button.setFixedSize(35, 35)
        self.exit_button.clicked.connect(self.exit_requested.emit)
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                color: #808080;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ef4444;
                border-color: #ef4444;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #dc2626;
            }
        """)
        
        self.update_time()
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        
        layout.addWidget(logo_label)
        layout.addWidget(version_label)
        layout.addStretch()
        layout.addWidget(self.search_input)
        layout.addStretch()
        layout.addWidget(self.time_label)
        layout.addWidget(self.exit_button)
        
    def on_search_text_changed(self, text):
        """Обработка изменения текста в поиске"""
        self.search_text_changed.emit(text)
        
        # Если есть текст, показываем выпадающий поиск
        if text.strip():
            self.emit_search_position()
        
    def on_search_return(self):
        """Обработка Enter в поиске"""
        # Сигнал для выполнения первого результата будет обработан в main_window
        pass
        
    def emit_search_position(self):
        """Отправить координаты для позиционирования выпадающего поиска"""
        # Получаем координаты относительно родительского виджета (главного окна)
        parent_widget = self.parent()
        if parent_widget:
            # Позиция строки поиска относительно главного окна
            search_pos = self.search_input.mapTo(parent_widget, self.search_input.rect().bottomLeft())
            self.search_position_requested.emit(search_pos.x(), search_pos.y() + 5)
        
    def focus_search(self):
        """Установить фокус на поиск"""
        self.search_input.setFocus()
        self.search_input.selectAll()
        
    def clear_search(self):
        """Очистить поиск"""
        self.search_input.clear()
        
    def get_search_text(self):
        """Получить текст поиска"""
        return self.search_input.text()
        
    def update_time(self):
        current_time = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm:ss")
        self.time_label.setText(current_time)

class SearchLineEdit(QLineEdit):
    """Кастомный QLineEdit с сигналами фокуса"""
    focus_gained = pyqtSignal()
    focus_lost = pyqtSignal()
    
    def focusInEvent(self, event: QFocusEvent):
        super().focusInEvent(event)
        self.focus_gained.emit()
        
    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        self.focus_lost.emit()