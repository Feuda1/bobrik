from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import subprocess
import sys

class PingWorker(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self, ip_address):
        super().__init__()
        self.ip_address = ip_address
        
    def run(self):
        try:
            if sys.platform == "win32":
                cmd = ['ping', '-n', '4', self.ip_address]  # 4 пакета в Windows
            else:
                cmd = ['ping', '-c', '4', self.ip_address]  # 4 пакета в Linux/Mac
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp866',  # Кодировка для Windows консоли
                errors='ignore'
            )
            
            # Выводим весь результат
            if process.stdout:
                for line in process.stdout.split('\n'):
                    if line.strip():
                        self.output_signal.emit(line.strip())
                        
            if process.stderr:
                for line in process.stderr.split('\n'):
                    if line.strip():
                        self.output_signal.emit(f"Ошибка: {line.strip()}")
                    
        except Exception as e:
            self.output_signal.emit(f"Ошибка выполнения ping: {str(e)}")
        finally:
            self.finished_signal.emit()

class PingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ping_worker = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Ping")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f0f0f;
                color: #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title = QLabel("Ping IP адреса")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 600;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Поле ввода IP
        input_layout = QHBoxLayout()
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Введите IP адрес (например: 8.8.8.8)")
        self.ip_input.setFixedHeight(35)
        self.ip_input.returnPressed.connect(self.start_ping)
        self.ip_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        input_layout.addWidget(self.ip_input)
        
        # Кнопка запуска
        self.start_button = QPushButton("Ping")
        self.start_button.setFixedSize(80, 35)
        self.start_button.clicked.connect(self.start_ping)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                border: 1px solid #10b981;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #047857;
                border-color: #34d399;
            }
            QPushButton:pressed {
                background-color: #065f46;
            }
            QPushButton:disabled {
                background-color: #0f0f0f;
                border-color: #1a1a1a;
                color: #404040;
            }
        """)
        input_layout.addWidget(self.start_button)
        
        layout.addLayout(input_layout)
        
        # Область вывода
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 10px;
                color: #e0e0e0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.output_text)
        
        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        clear_button = QPushButton("Очистить")
        clear_button.setFixedSize(100, 35)
        clear_button.clicked.connect(self.clear_output)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #1e40af;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                color: #3b82f6;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
                border-color: #60a5fa;
                color: #60a5fa;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
            }
        """)
        buttons_layout.addWidget(clear_button)
        
        close_button = QPushButton("Закрыть")
        close_button.setFixedSize(100, 35)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
        
        # Фокус на поле ввода
        self.ip_input.setFocus()
        
    def start_ping(self):
        ip_address = self.ip_input.text().strip()
        if not ip_address:
            self.output_text.append("⚠️ Введите IP адрес")
            return
            
        # Простая валидация IP
        parts = ip_address.split('.')
        if len(parts) == 4:
            try:
                for part in parts:
                    num = int(part)
                    if not 0 <= num <= 255:
                        raise ValueError()
            except ValueError:
                self.output_text.append("⚠️ Неверный формат IP адреса")
                return
        elif not any(char.isalpha() for char in ip_address):
            self.output_text.append("⚠️ Неверный формат IP адреса")
            return
            
        self.output_text.clear()
        self.output_text.append(f"Выполняется ping {ip_address}...")
        self.output_text.append("")
        
        self.start_button.setEnabled(False)
        self.start_button.setText("...")
        self.ip_input.setEnabled(False)
        
        self.ping_worker = PingWorker(ip_address)
        self.ping_worker.output_signal.connect(self.on_output_received)
        self.ping_worker.finished_signal.connect(self.on_ping_finished)
        self.ping_worker.start()
        
    def on_output_received(self, output):
        self.output_text.append(output)
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def on_ping_finished(self):
        self.start_button.setEnabled(True)
        self.start_button.setText("Ping")
        self.ip_input.setEnabled(True)
        self.output_text.append("")
        self.output_text.append("Ping завершен")
        
    def clear_output(self):
        self.output_text.clear()
        
    def closeEvent(self, event):
        if self.ping_worker and self.ping_worker.isRunning():
            self.ping_worker.wait(1000)
        event.accept()