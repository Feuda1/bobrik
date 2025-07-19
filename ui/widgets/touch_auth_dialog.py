from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGridLayout, QWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

class TouchAuthDialog(QDialog):
    auth_accepted = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.correct_pin = "2289"
        self.current_pin = ""
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("bobrik - Авторизация")
        self.setFixedSize(380, 520)  # Еще компактнее
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        
        self.center_window()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(12)
        
        # Заголовок
        title_label = QLabel("bobrik")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 26px;
                font-weight: 600;
                padding: 8px;
            }
        """)
        main_layout.addWidget(title_label)
        
        desc_label = QLabel("Введите PIN-код")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 15px;
                margin-bottom: 3px;
            }
        """)
        main_layout.addWidget(desc_label)
        
        # PIN индикаторы
        pin_container = QWidget()
        pin_container.setFixedHeight(55)
        pin_layout = QHBoxLayout(pin_container)
        pin_layout.setSpacing(12)
        pin_layout.setContentsMargins(0, 5, 0, 5)
        
        self.pin_indicators = []
        for i in range(4):
            indicator = QLabel("●")
            indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            indicator.setFixedSize(40, 40)
            indicator.setStyleSheet("""
                QLabel {
                    background-color: #141414;
                    border: 1px solid #1f1f1f;
                    border-radius: 6px;
                    color: #404040;
                    font-size: 14px;
                    font-weight: 500;
                }
            """)
            self.pin_indicators.append(indicator)
            pin_layout.addWidget(indicator)
            
        pin_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(pin_container)
        
        # Статус
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(18)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # Клавиатура
        keypad_frame = QFrame()
        keypad_frame.setFixedHeight(280)  # Компактная клавиатура
        keypad_frame.setStyleSheet("""
            QFrame {
                background-color: #141414;
                border: 1px solid #1f1f1f;
                border-radius: 8px;
            }
        """)
        
        keypad_layout = QGridLayout(keypad_frame)
        keypad_layout.setSpacing(10)  # Меньшие отступы
        keypad_layout.setContentsMargins(18, 18, 18, 18)
        
        # Создаем квадратные кнопки цифр
        self.number_buttons = []
        for i in range(1, 10):
            button = self.create_number_button(str(i))
            row = (i - 1) // 3
            col = (i - 1) % 3
            keypad_layout.addWidget(button, row, col)
            self.number_buttons.append(button)
            
        # Кнопка 0
        zero_button = self.create_number_button("0")
        keypad_layout.addWidget(zero_button, 3, 1)
        self.number_buttons.append(zero_button)
        
        # Кнопка очистки
        clear_button = QPushButton("⌫")
        clear_button.setFixedSize(65, 65)
        clear_button.clicked.connect(self.clear_pin)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                color: #808080;
                font-size: 18px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #262626;
                border-color: #3a3a3a;
                color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
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
        
    def create_number_button(self, number):
        """Создает квадратную кнопку цифры"""
        button = QPushButton(number)
        button.setFixedSize(65, 65)  # Компактные кнопки
        button.clicked.connect(lambda: self.add_digit(number))
        button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                color: #e0e0e0;
                font-size: 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #262626;
                border-color: #3a3a3a;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #333333;
                border-color: #4a4a4a;
            }
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
                QTimer.singleShot(200, self.check_pin)
                
    def clear_pin(self):
        """Очищает PIN"""
        self.current_pin = ""
        self.update_indicators()
        self.status_label.setText("")
        
    def update_indicators(self):
        """Обновляет индикаторы PIN"""
        for i, indicator in enumerate(self.pin_indicators):
            if i < len(self.current_pin):
                indicator.setStyleSheet("""
                    QLabel {
                        background-color: #2a2a2a;
                        border: 1px solid #4a4a4a;
                        border-radius: 6px;
                        color: #ffffff;
                        font-size: 14px;
                        font-weight: 500;
                    }
                """)
            else:
                indicator.setStyleSheet("""
                    QLabel {
                        background-color: #141414;
                        border: 1px solid #1f1f1f;
                        border-radius: 6px;
                        color: #404040;
                        font-size: 14px;
                        font-weight: 500;
                    }
                """)
                
    def check_pin(self):
        """Проверяет PIN"""
        if self.current_pin == self.correct_pin:
            self.show_success()
            QTimer.singleShot(1000, self.accept_auth)
        else:
            self.show_error()
            QTimer.singleShot(1500, self.clear_pin)
            
    def show_success(self):
        """Показывает успешную авторизацию"""
        self.status_label.setText("✅ Доступ разрешен")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #10b981;
                font-size: 13px;
                font-weight: 600;
            }
        """)
        
        for indicator in self.pin_indicators:
            indicator.setStyleSheet("""
                QLabel {
                    background-color: #065f46;
                    border: 1px solid #10b981;
                    border-radius: 6px;
                    color: #10b981;
                    font-size: 14px;
                    font-weight: 500;
                }
            """)
            
    def show_error(self):
        """Показывает ошибку"""
        self.status_label.setText("❌ Неверный PIN-код")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ef4444;
                font-size: 13px;
                font-weight: 600;
            }
        """)
        
        for indicator in self.pin_indicators:
            indicator.setStyleSheet("""
                QLabel {
                    background-color: #7f1d1d;
                    border: 1px solid #ef4444;
                    border-radius: 6px;
                    color: #ef4444;
                    font-size: 14px;
                    font-weight: 500;
                }
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
        elif key == Qt.Key.Key_Return and len(self.current_pin) == 4:
            self.check_pin()
        elif key == Qt.Key.Key_Escape:
            self.reject()
            
        super().keyPressEvent(event)