from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QInputDialog
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from managers.network_manager import NetworkManager
import subprocess
import sys
import os
import tempfile

class DiagnosticWorker(QThread):
    output_signal = pyqtSignal(str, str)  # message, type
    
    def __init__(self, server_address):
        super().__init__()
        self.server_address = server_address
        
    def run(self):
        try:
            # Создаем файл лога на рабочем столе
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            log_file = os.path.join(desktop_path, "532_full_diagnostic.log")
            
            # Список команд для выполнения
            commands = [
                {
                    "name": "1. netsh interface ipv4 show subinterfaces",
                    "cmd": ["netsh", "interface", "ipv4", "show", "subinterfaces"]
                },
                {
                    "name": "2. route print",
                    "cmd": ["route", "print"]
                },
                {
                    "name": "3. ipconfig /all",
                    "cmd": ["ipconfig", "/all"]
                },
                {
                    "name": f"4. ping {self.server_address} -n 10",
                    "cmd": ["ping", self.server_address, "-n", "10"]
                },
                {
                    "name": f"5. ping {self.server_address} -f -l 1472",
                    "cmd": ["ping", self.server_address, "-f", "-l", "1472"]
                },
                {
                    "name": f"6. ping {self.server_address} -f -l 1462",
                    "cmd": ["ping", self.server_address, "-f", "-l", "1462"]
                },
                {
                    "name": f"7. ping {self.server_address} -f -l 1452",
                    "cmd": ["ping", self.server_address, "-f", "-l", "1452"]
                },
                {
                    "name": f"8. ping {self.server_address} -f -l 1372",
                    "cmd": ["ping", self.server_address, "-f", "-l", "1372"]
                },
                {
                    "name": f"9. ping {self.server_address} -l 65500",
                    "cmd": ["ping", self.server_address, "-l", "65500"]
                },
                {
                    "name": f"10. tracert {self.server_address}",
                    "cmd": ["tracert", self.server_address]
                },
                {
                    "name": f"11. pathping {self.server_address}",
                    "cmd": ["pathping", self.server_address]
                }
            ]
            
            self.output_signal.emit("Начинаем полную диагностику сети...", "info")
            self.output_signal.emit(f"Сервер: {self.server_address}", "info")
            self.output_signal.emit(f"Лог сохраняется в: {log_file}", "info")
            
            # Очищаем файл лога
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("")
            
            for i, command in enumerate(commands, 1):
                try:
                    self.output_signal.emit(f"[{i}/11] {command['name']}", "info")
                    
                    # Записываем заголовок в лог
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write("*" * 80 + "\n")
                        f.write(f"* {command['name']}\n")
                        f.write("*" * 80 + "\n")
                    
                    # Выполняем команду
                    process = subprocess.run(
                        command['cmd'],
                        capture_output=True,
                        text=True,
                        encoding='cp866',
                        errors='ignore',
                        timeout=120  # 2 минуты на команду
                    )
                    
                    # Записываем результат в лог
                    with open(log_file, 'a', encoding='utf-8') as f:
                        if process.stdout:
                            f.write(process.stdout)
                        if process.stderr:
                            f.write(f"ОШИБКИ:\n{process.stderr}")
                        f.write("\n")
                    
                    if process.returncode == 0:
                        self.output_signal.emit(f"✓ {command['name']} - выполнено", "success")
                    else:
                        self.output_signal.emit(f"⚠ {command['name']} - завершено с предупреждениями", "warning")
                        
                except subprocess.TimeoutExpired:
                    self.output_signal.emit(f"⏱ {command['name']} - превышено время ожидания", "warning")
                except Exception as e:
                    self.output_signal.emit(f"✗ {command['name']} - ошибка: {str(e)}", "error")
            
            self.output_signal.emit("Диагностика завершена", "success")
            self.output_signal.emit(f"Лог сохранен в: {log_file}", "info")
            
            # Открываем папку с логом
            try:
                subprocess.Popen(['explorer', '/select,', log_file])
            except:
                pass
                
        except Exception as e:
            self.output_signal.emit(f"Критическая ошибка диагностики: {str(e)}", "error")

class PingWorker(QThread):
    output_signal = pyqtSignal(str, str)  # message, type
    
    def __init__(self, ip_address):
        super().__init__()
        self.ip_address = ip_address
        
    def run(self):
        try:
            if sys.platform == "win32":
                cmd = ['ping', '-n', '4', self.ip_address]
            else:
                cmd = ['ping', '-c', '4', self.ip_address]
            
            self.output_signal.emit(f"Ping {self.ip_address}...", "info")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='cp866',
                errors='ignore',
                universal_newlines=True
            )
            
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                if line.strip():
                    self.output_signal.emit(line.strip(), "info")
            
            process.wait()
            
        except Exception as e:
            self.output_signal.emit(f"Ошибка ping: {str(e)}", "error")

class NetworkTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.network_manager = NetworkManager(self)
        self.network_manager.log_signal.connect(self.log_signal.emit)
        self.ping_worker = None
        self.diagnostic_worker = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        title = QLabel("Сетевые функции")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 500;
                padding-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Кнопка IPConfig
        ipconfig_button = QPushButton("IPConfig")
        ipconfig_button.setFixedSize(105, 45)
        ipconfig_button.clicked.connect(self.open_ipconfig)
        ipconfig_button.setStyleSheet("""
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
        """)
        
        # Кнопка FullDiagnostic
        diagnostic_button = QPushButton("FullDiagnostic")
        diagnostic_button.setFixedSize(105, 45)
        diagnostic_button.clicked.connect(self.start_diagnostic)
        diagnostic_button.setStyleSheet("""
            QPushButton {
                background-color: #7c2d12;
                border: 1px solid #ea580c;
                border-radius: 4px;
                color: #ea580c;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 2px;
            }
            QPushButton:hover {
                background-color: #9a3412;
                border-color: #fb923c;
                color: #fb923c;
            }
            QPushButton:pressed {
                background-color: #7c2d12;
            }
        """)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(ipconfig_button)
        buttons_layout.addWidget(diagnostic_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Ping секция
        ping_layout = QHBoxLayout()
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Введите IP адрес для ping")
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
        ping_layout.addWidget(self.ip_input)
        
        self.ping_button = QPushButton("Ping")
        self.ping_button.setFixedSize(80, 35)
        self.ping_button.clicked.connect(self.start_ping)
        self.ping_button.setStyleSheet("""
            QPushButton {
                background-color: #1e40af;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
                border-color: #60a5fa;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
            }
            QPushButton:disabled {
                background-color: #0f0f0f;
                border-color: #1a1a1a;
                color: #404040;
            }
        """)
        ping_layout.addWidget(self.ping_button)
        
        layout.addLayout(ping_layout)
        layout.addStretch()
        
    def open_ipconfig(self):
        self.network_manager.open_ipconfig()
        
    def start_ping(self):
        ip_address = self.ip_input.text().strip()
        if not ip_address:
            self.log_signal.emit("Введите IP адрес", "error")
            return
            
        if self.ping_worker and self.ping_worker.isRunning():
            self.log_signal.emit("Ping уже выполняется", "warning")
            return
            
        self.ping_button.setEnabled(False)
        self.ping_button.setText("...")
        
        self.ping_worker = PingWorker(ip_address)
        self.ping_worker.output_signal.connect(self.log_signal.emit)
        self.ping_worker.finished.connect(self.on_ping_finished)
        self.ping_worker.start()
        
    def start_diagnostic(self):
        # Запрашиваем сервер у пользователя
        server, ok = QInputDialog.getText(
            self, 
            'Полная диагностика сети', 
            'Введите адрес сервера:'
        )
        
        if not ok or not server.strip():
            return
            
        server = server.strip()
        
        if self.diagnostic_worker and self.diagnostic_worker.isRunning():
            self.log_signal.emit("Диагностика уже выполняется", "warning")
            return
            
        self.log_signal.emit("Запуск полной диагностики сети...", "info")
        
        self.diagnostic_worker = DiagnosticWorker(server)
        self.diagnostic_worker.output_signal.connect(self.log_signal.emit)
        self.diagnostic_worker.start()
        
    def on_ping_finished(self):
        self.ping_button.setEnabled(True)
        self.ping_button.setText("Ping")