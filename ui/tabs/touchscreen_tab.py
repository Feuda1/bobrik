from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from managers.touchscreen_manager import TouchscreenManager
from ui.styles import get_button_style

class TouchscreenTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.touchscreen_manager = TouchscreenManager()
        self.touchscreen_manager.log_signal.connect(self.log_signal.emit)
        self.touchscreen_manager.status_signal.connect(self.update_button_state)
        self.touchscreen_manager.start()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Описание функции
        description = QLabel("Управление сенсорным экраном позволяет быстро отключать и включать тачскрин на терминалах.")
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 14px;
                padding: 10px;
                background-color: #1a1a1a;
                border-radius: 6px;
                border: 1px solid #2a2a2a;
            }
        """)
        layout.addWidget(description)
        
        # Информационная панель (создаём до кнопки!)
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 6px;
                border: 1px solid #2a2a2a;
                padding: 15px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        self.status_label = QLabel("Статус: Готов к работе")
        self.status_label.setStyleSheet("color: #e0e0e0; font-size: 14px;")
        info_layout.addWidget(self.status_label)
        
        # Кнопка управления
        button_container = QHBoxLayout()
        button_container.addStretch()
        
        self.touchscreen_button = QPushButton()
        self.touchscreen_button.setFixedSize(200, 80)
        self.touchscreen_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.touchscreen_button.clicked.connect(self.toggle_touchscreen)
        self.update_button_state(False)
        
        button_container.addWidget(self.touchscreen_button)
        button_container.addStretch()
        
        layout.addLayout(button_container)
        layout.addWidget(info_frame)
        layout.addStretch()
        
    def update_button_state(self, is_disabled):
        self.touchscreen_button.setStyleSheet(get_button_style(is_disabled))
        
        if is_disabled:
            text = "Включить\nсенсорный экран"
            self.status_label.setText("Статус: Сенсорный экран отключен")
        else:
            text = "Отключить\nсенсорный экран"
            self.status_label.setText("Статус: Сенсорный экран включен")
            
        self.touchscreen_button.setText(text)
        
    def toggle_touchscreen(self):
        self.touchscreen_manager.toggle_touchscreen()
        
    def cleanup(self):
        if self.touchscreen_manager.is_disabled:
            self.touchscreen_manager.enable_touchscreen()