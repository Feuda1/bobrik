from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGridLayout, QScrollArea, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
import subprocess
import sys
import os
import tempfile
import threading
import shutil
import zipfile

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

class DownloadWorker(QThread):
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str, bool)  # path, success
    
    def __init__(self, url, filename):
        super().__init__()
        self.url = url
        self.filename = filename
        
    def run(self):
        try:
            if not HAS_REQUESTS:
                self.log_signal.emit("Библиотека requests не установлена", "error")
                self.finished_signal.emit("", False)
                return
                
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, self.filename)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.url, stream=True, headers=headers, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_progress = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = min(90, int((downloaded / total_size) * 90))
                            if progress >= last_progress + 10:
                                self.log_signal.emit(f"Загружено: {progress}%", "info")
                                last_progress = progress
            
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.log_signal.emit(f"Загрузка завершена ({file_size_mb:.1f} МБ)", "success")
            self.finished_signal.emit(file_path, True)
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка загрузки: {str(e)}", "error")
            self.finished_signal.emit("", False)

class InstallerTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.all_programs = {
            "7zip": {
                "name": "7-Zip",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/7z2500-x64.exe",
                "filename": "7z2500-x64.exe"
            },
            "advanced_ip_scanner": {
                "name": "Advanced IP Scanner",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/Advanced_IP_Scanner_2.5.4594.1.exe",
                "filename": "Advanced_IP_Scanner_2.5.4594.1.exe"
            },
            "anydesk": {
                "name": "AnyDesk",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/AnyDesk.exe",
                "filename": "AnyDesk.exe"
            },
            "assistant": {
                "name": "Ассистент",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/assistant_install_6.exe",
                "filename": "assistant_install_6.exe"
            },
            "com_port_checker": {
                "name": "Com Port Checker",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/ComPortChecker.1.1.zip",
                "filename": "ComPortChecker.1.1.zip",
                "is_zip": True
            },
            "database_net": {
                "name": "Database Net",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/DatabaseNet5Pro.zip",
                "filename": "DatabaseNet5Pro.zip",
                "is_zip": True
            },
            "notepad_plus": {
                "name": "Notepad++",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/npp.8.8.2.Installer.x64.exe",
                "filename": "npp.8.8.2.Installer.x64.exe"
            },
            "printer_test": {
                "name": "Printer TEST V3.1C",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/Printer-TEST-V3.1C.zip",
                "filename": "Printer-TEST-V3.1C.zip",
                "is_zip": True
            },
            "rhelper": {
                "name": "Rhelper",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/remote-access-setup.exe",
                "filename": "remote-access-setup.exe"
            }
        }
        
        self.download_worker = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Заголовок и поиск
        header_layout = QVBoxLayout()
        
        title = QLabel("Установка программ")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 500;
                padding-bottom: 5px;
            }
        """)
        header_layout.addWidget(title)
        
        # Поиск
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск программ...")
        self.search_edit.setFixedHeight(35)
        self.search_edit.textChanged.connect(self.filter_programs)
        self.search_edit.setStyleSheet("""
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
        header_layout.addWidget(self.search_edit)
        
        layout.addLayout(header_layout)
        
        # Скроллируемая область с программами
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505050;
            }
        """)
        
        self.content_widget = QWidget()
        self.programs_layout = QGridLayout(self.content_widget)
        self.programs_layout.setSpacing(10)
        self.programs_layout.setContentsMargins(10, 10, 10, 10)
        self.programs_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.create_program_buttons()
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
        
    def create_program_buttons(self):
        # Очищаем старые кнопки
        for i in reversed(range(self.programs_layout.count())):
            child = self.programs_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Фильтрация по поиску
        search_text = self.search_edit.text().lower() if hasattr(self, 'search_edit') else ""
        filtered_programs = {}
        
        for key, program in self.all_programs.items():
            if search_text == "" or search_text in program["name"].lower():
                filtered_programs[key] = program
        
        # Создаем кнопки
        row = 0
        col = 0
        max_cols = 4
        
        for program_key, program in filtered_programs.items():
            button = self.create_install_button(program["name"], program_key)
            self.programs_layout.addWidget(button, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Если нет результатов поиска
        if not filtered_programs and search_text:
            no_results = QLabel("🔍 Программы не найдены")
            no_results.setStyleSheet("""
                QLabel {
                    color: #808080;
                    font-size: 14px;
                    padding: 20px;
                    text-align: center;
                }
            """)
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.programs_layout.addWidget(no_results, 0, 0, 1, max_cols)
        
    def filter_programs(self):
        self.create_program_buttons()
        
    def create_install_button(self, program_name, program_key):
        button = QPushButton(program_name)
        button.setFixedSize(140, 50)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda: self.install_program(program_key))
        button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 12px;
                font-weight: 500;
                padding: 6px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #4a4a4a;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        
        return button
        
    def install_program(self, program_key):
        if program_key not in self.all_programs:
            self.log_signal.emit(f"Программа {program_key} не найдена", "error")
            return
            
        program = self.all_programs[program_key]
        
        msg = QMessageBox(self)
        msg.setWindowTitle('Установка программы')
        msg.setText(f'Начать загрузку и установку {program["name"]}?')
        msg.setIcon(QMessageBox.Icon.Question)
        
        yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
        no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(no_button)
        
        msg.exec()
        
        if msg.clickedButton() == yes_button:
            self.download_and_install(program)
        
    def download_and_install(self, program):
        if not HAS_REQUESTS:
            self.log_signal.emit("Для загрузки программ требуется библиотека requests", "error")
            self.log_signal.emit("Установите: pip install requests", "info")
            return
            
        self.log_signal.emit(f"Начинаем загрузку {program['name']}...", "info")
        
        self.download_worker = DownloadWorker(program["url"], program["filename"])
        self.download_worker.log_signal.connect(self.log_signal.emit)
        self.download_worker.finished_signal.connect(lambda path, success: self.on_download_finished(path, success, program))
        self.download_worker.start()
        
    def on_download_finished(self, file_path, success, program):
        if not success:
            return
            
        try:
            if program.get("is_zip", False):
                self.handle_zip_file(file_path, program)
            else:
                self.handle_executable(file_path, program)
        except Exception as e:
            self.log_signal.emit(f"Ошибка обработки файла: {str(e)}", "error")
            
    def get_safe_folder_name(self, program_name):
        """Получает безопасное название папки только на английском"""
        safe_names = {
            "Advanced IP Scanner": "Advanced_IP_Scanner",
            "AnyDesk": "AnyDesk", 
            "Com Port Checker": "ComPortChecker",
            "Database Net": "DatabaseNet",
            "Printer TEST V3.1C": "PrinterTEST",
            "Ассистент": "Assistant",
            "Rhelper": "Rhelper",
            "7-Zip": "7-Zip",
            "Notepad++": "Notepad_Plus"
        }
        return safe_names.get(program_name, program_name.replace(" ", "_"))

    def handle_zip_file(self, zip_path, program):
        try:
            # Получаем безопасное имя папки
            safe_name = self.get_safe_folder_name(program['name'])
            
            # Определяем куда извлекать
            if program.get("filename") in ["Advanced_IP_Scanner_2.5.4594.1.exe", "AnyDesk.exe", 
                                         "ComPortChecker.1.1.zip", "DatabaseNet5Pro.zip", 
                                         "Printer-TEST-V3.1C.zip"]:
                # На рабочий стол
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                extract_dir = os.path.join(desktop_path, safe_name)
                location_msg = "на рабочий стол"
            else:
                # В загрузки
                downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
                extract_dir = os.path.join(downloads_path, safe_name)
                location_msg = "в папку Загрузки"
            
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            
            os.makedirs(extract_dir)
            
            # Извлекаем с правильной кодировкой для русских названий
            try:
                # Пробуем сначала UTF-8
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    for member in zip_ref.infolist():
                        # Исправляем кодировку имени файла
                        try:
                            # Пробуем декодировать как cp866 (DOS кодировка)
                            member.filename = member.filename.encode('cp437').decode('cp866')
                        except:
                            try:
                                # Пробуем декодировать как windows-1251
                                member.filename = member.filename.encode('cp437').decode('windows-1251')
                            except:
                                # Оставляем как есть, если не удалось декодировать
                                pass
                        
                        zip_ref.extract(member, extract_dir)
                        
            except Exception as encoding_error:
                # Если не получилось с кодировкой, извлекаем обычным способом
                self.log_signal.emit(f"Предупреждение: возможны проблемы с кодировкой файлов", "warning")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            
            subprocess.Popen(['explorer', extract_dir])
            self.log_signal.emit(f"{program['name']} извлечен {location_msg} ({safe_name})", "success")
            
            try:
                os.remove(zip_path)
            except:
                pass
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при работе с архивом: {str(e)}", "error")
            
    def handle_executable(self, exe_path, program):
        try:
            # Определяем куда сохранять exe файлы
            if program.get("filename") in ["Advanced_IP_Scanner_2.5.4594.1.exe", "AnyDesk.exe"]:
                # На рабочий стол
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                final_path = os.path.join(desktop_path, program["filename"])
                location_msg = "на рабочий стол"
            else:
                # В загрузки
                downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
                final_path = os.path.join(downloads_path, program["filename"])
                location_msg = "в папку Загрузки"
            
            # Копируем файл в нужное место
            try:
                shutil.copy2(exe_path, final_path)
                self.log_signal.emit(f"{program['name']} сохранен {location_msg}", "info")
            except:
                final_path = exe_path  # Если не удалось скопировать, запускаем оригинал
            
            self.log_signal.emit(f"Запуск установщика {program['name']}...", "info")
            subprocess.Popen([final_path])
            self.log_signal.emit(f"{program['name']} - установщик запущен", "success")
            
            # Специальная обработка для Rhelper - показываем пароль после запуска
            if program.get("filename") == "remote-access-setup.exe":
                self.log_signal.emit("🔑 Пароль для Rhelper: remote-access-setup", "warning")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка запуска установщика: {str(e)}", "error")