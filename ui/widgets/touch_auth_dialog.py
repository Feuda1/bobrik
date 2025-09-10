from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGridLayout, QWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from config import get_is_small_screen

class TouchAuthDialog(QDialog):
    auth_accepted = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.correct_pin = "2289"
        self.current_pin = ""
        self.is_small_screen = get_is_small_screen()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("bobrik - Авторизация")
        
        # Адаптивные размеры диалога
        if self.is_small_screen:
            dialog_width, dialog_height = 320, 450
            title_size = 22
            desc_size = 13
            pin_size = 35
            button_size = 55
            keypad_height = 240
        else:
            dialog_width, dialog_height = 380, 520
            title_size = 26
            desc_size = 15
            pin_size = 40
            button_size = 65
            keypad_height = 280
        
        self.setFixedSize(dialog_width, dialog_height)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        
        self.center_window()
        
        main_layout = QVBoxLayout(self)
        margin = 20 if self.is_small_screen else 25
        spacing = 10 if self.is_small_screen else 12
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Заголовок
        title_label = QLabel("bobrik")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: #ffffff;
                font-size: {title_size}px;
                font-weight: 600;
                padding: 8px;
            }}
        """)
        main_layout.addWidget(title_label)
        
        desc_label = QLabel("Введите PIN-код")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: #808080;
                font-size: {desc_size}px;
                margin-bottom: 3px;
            }}
        """)
        main_layout.addWidget(desc_label)
        
        # PIN индикаторы
        pin_container = QWidget()
        pin_container_height = 50 if self.is_small_screen else 55
        pin_container.setFixedHeight(pin_container_height)
        pin_layout = QHBoxLayout(pin_container)
        pin_spacing = 10 if self.is_small_screen else 12
        pin_layout.setSpacing(pin_spacing)
        pin_layout.setContentsMargins(0, 5, 0, 5)
        
        self.pin_indicators = []
        for i in range(4):
            indicator = QLabel("●")
            indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            indicator.setFixedSize(pin_size, pin_size)
            indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: #141414;
                    border: 1px solid #1f1f1f;
                    border-radius: 6px;
                    color: #404040;
                    font-size: {12 if self.is_small_screen else 14}px;
                    font-weight: 500;
                }}
            """)
            self.pin_indicators.append(indicator)
            pin_layout.addWidget(indicator)
            
        pin_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(pin_container)
        
        # Статус
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(18)
        status_size = 12 if self.is_small_screen else 13
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: #808080;
                font-size: {status_size}px;
                font-weight: 500;
            }}
        """)
        main_layout.addWidget(self.status_label)
        
        # Клавиатура
        keypad_frame = QFrame()
        keypad_frame.setFixedHeight(keypad_height)
        keypad_frame.setStyleSheet("""
            QFrame {
                background-color: #141414;
                border: 1px solid #1f1f1f;
                border-radius: 8px;
            }
        """)
        
        keypad_layout = QGridLayout(keypad_frame)
        keypad_spacing = 8 if self.is_small_screen else 10
        keypad_margin = 15 if self.is_small_screen else 18
        keypad_layout.setSpacing(keypad_spacing)
        keypad_layout.setContentsMargins(keypad_margin, keypad_margin, keypad_margin, keypad_margin)
        
        # Создаем квадратные кнопки цифр
        self.number_buttons = []
        for i in range(1, 10):
            button = self.create_number_button(str(i), button_size)
            row = (i - 1) // 3
            col = (i - 1) % 3
            keypad_layout.addWidget(button, row, col)
            self.number_buttons.append(button)
            
        # Кнопка 0
        zero_button = self.create_number_button("0", button_size)
        keypad_layout.addWidget(zero_button, 3, 1)
        self.number_buttons.append(zero_button)
        
        # Кнопка очистки
        clear_button = QPushButton("⌫")
        clear_button.setFixedSize(button_size, button_size)
        clear_button.clicked.connect(self.clear_pin)
        clear_font_size = 16 if self.is_small_screen else 18
        clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                color: #808080;
                font-size: {clear_font_size}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #262626;
                border-color: #3a3a3a;
                color: #e0e0e0;
            }}
            QPushButton:pressed {{
                background-color: #1a1a1a;
            }}
        """)
        keypad_layout.addWidget(clear_button, 3, 2)
        
        main_layout.addWidget(keypad_frame)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #0a0a0a;
                border: 1px solid #1f1f1f;
                border-radius: 8px;
            }
        """)
        
    def create_number_button(self, number, size):
        """Создает квадратную кнопку цифры"""
        button = QPushButton(number)
        button.setFixedSize(size, size)
        button.clicked.connect(lambda: self.add_digit(number))
        
        button_font_size = 18 if self.is_small_screen else 20
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                color: #e0e0e0;
                font-size: {button_font_size}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #262626;
                border-color: #3a3a3a;
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: #333333;
                border-color: #4a4a4a;
            }}
        """)
        return button
        
    def center_window(self):
        """Центрирует окно на экране"""
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
        else:
            screen = self.screen().geometry()
            size = self.geometry()
            self.move(
                (screen.width() - size.width()) // 2,
                (screen.height() - size.height()) // 2
            )
        
    def add_digit(self, digit):
        """Добавляет цифру к PIN"""
        if len(self.current_pin) < 4:
            self.current_pin += digit
            self.update_indicators()
            
            if len(self.current_pin) == 4:
                QTimer.singleShot(100, self.check_pin)
                
    def clear_pin(self):
        """Очищает PIN"""
        self.current_pin = ""
        self.update_indicators()
        self.status_label.setText("")
        
    def update_indicators(self):
        """Обновляет индикаторы PIN"""
        pin_size = 35 if self.is_small_screen else 40
        font_size = 12 if self.is_small_screen else 14
        
        for i, indicator in enumerate(self.pin_indicators):
            if i < len(self.current_pin):
                indicator.setStyleSheet(f"""
                    QLabel {{
                        background-color: #2a2a2a;
                        border: 1px solid #4a4a4a;
                        border-radius: 6px;
                        color: #ffffff;
                        font-size: {font_size}px;
                        font-weight: 500;
                    }}
                """)
            else:
                indicator.setStyleSheet(f"""
                    QLabel {{
                        background-color: #141414;
                        border: 1px solid #1f1f1f;
                        border-radius: 6px;
                        color: #404040;
                        font-size: {font_size}px;
                        font-weight: 500;
                    }}
                """)
                
    def check_pin(self):
        """Проверяет PIN"""
        if self.current_pin == self.correct_pin:
            self.show_success()
            QTimer.singleShot(300, self.accept_auth)
        else:
            self.show_error()
            QTimer.singleShot(800, self.clear_pin)
            
    def show_success(self):
        """Показывает успешную авторизацию"""
        self.status_label.setText("✅ Доступ разрешен")
        status_size = 12 if self.is_small_screen else 13
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: #10b981;
                font-size: {status_size}px;
                font-weight: 600;
            }}
        """)
        
        pin_size = 35 if self.is_small_screen else 40
        font_size = 12 if self.is_small_screen else 14
        
        for indicator in self.pin_indicators:
            indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: #065f46;
                    border: 1px solid #10b981;
                    border-radius: 6px;
                    color: #10b981;
                    font-size: {font_size}px;
                    font-weight: 500;
                }}
            """)
            
    def show_error(self):
        """Показывает ошибку"""
        self.status_label.setText("❌ Неверный PIN-код")
        status_size = 12 if self.is_small_screen else 13
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: #ef4444;
                font-size: {status_size}px;
                font-weight: 600;
            }}
        """)
        
        pin_size = 35 if self.is_small_screen else 40
        font_size = 12 if self.is_small_screen else 14
        
        for indicator in self.pin_indicators:
            indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: #7f1d1d;
                    border: 1px solid #ef4444;
                    border-radius: 6px;
                    color: #ef4444;
                    font-size: {font_size}px;
                    font-weight: 500;
                }}
            """)
            
    def accept_auth(self):
        """Принимает авторизацию"""
        self.auth_accepted.emit()
        self.accept()
        
    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        key = event.key()
        
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            digit = str(key - Qt.Key.Key_0)
            self.add_digit(digit)
        elif key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self.clear_pin()
        elif key == Qt.Key.Key_Return:
            if len(self.current_pin) == 4:
                self.check_pin()
            elif len(self.current_pin) == 0:
                self.current_pin = self.correct_pin
                self.update_indicators()
                QTimer.singleShot(50, self.check_pin)
        elif key == Qt.Key.Key_Escape:
            self.reject()
            
        super().keyPressEvent(event)