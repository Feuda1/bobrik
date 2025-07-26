import subprocess
import sys
import os
import tempfile
import threading
import shutil
import json
import zipfile
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QFileDialog

try:
    import requests
except ImportError:
    requests = None

class InstallerManager(QThread):
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        self.programs = {
            "7zip": {
                "name": "7-Zip",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/7z2500-x64.exe",
                "filename": "7z2500-x64.exe",
                "silent_args": ["/S"],
                "check_names": ["7-Zip", "7zip"],
                "category": "utilities"
            },
            "advanced_ip_scanner": {
                "name": "Advanced IP Scanner",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/Advanced_IP_Scanner_2.5.4594.1.exe",
                "filename": "Advanced_IP_Scanner_2.5.4594.1.exe",
                "silent_args": ["/VERYSILENT", "/NORESTART"],
                "check_names": ["Advanced IP Scanner", "Advanced_IP_Scanner"],
                "category": "network"
            },
            "anydesk": {
                "name": "AnyDesk",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/AnyDesk.exe",
                "filename": "AnyDesk.exe",
                "silent_args": ["--install", "--silent"],
                "check_names": ["AnyDesk"],
                "category": "remote"
            },
            "assistant": {
                "name": "Ассистент",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/assistant_install_6.exe",
                "filename": "assistant_install_6.exe",
                "silent_args": ["/S"],
                "check_names": ["Ассистент", "Assistant"],
                "category": "utilities"
            },
            "com_port_checker": {
                "name": "Com Port Checker",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/ComPortChecker.1.1.zip",
                "filename": "ComPortChecker.1.1.zip",
                "silent_args": [],
                "check_names": ["Com Port Checker", "ComPortChecker"],
                "category": "utilities",
                "is_zip": True,
                "extract_and_run": "ComPortChecker.exe"
            },
            "database_net": {
                "name": "Database Net",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/DatabaseNet5Pro.zip",
                "filename": "DatabaseNet5Pro.zip",
                "silent_args": [],
                "check_names": ["Database Net", "DatabaseNet"],
                "category": "development",
                "is_zip": True,
                "extract_and_run": "setup.exe"
            },
            "notepad_plus": {
                "name": "Notepad++",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/npp.8.8.2.Installer.x64.exe",
                "filename": "npp.8.8.2.Installer.x64.exe",
                "silent_args": ["/S"],
                "check_names": ["Notepad++", "notepad"],
                "category": "utilities"
            },
            "printer_test": {
                "name": "Printer TEST V3.1C",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/Printer-TEST-V3.1C.zip",
                "filename": "Printer-TEST-V3.1C.zip",
                "silent_args": [],
                "check_names": ["Printer TEST", "PrinterTEST"],
                "category": "utilities",
                "is_zip": True,
                "extract_and_run": "PrinterTEST.exe"
            },
            "rhelper": {
                "name": "Rhelper (Remote Access)",
                "url": "https://github.com/Feuda1/Programs-for-Bobrik/releases/download/v1.0.0/remote-access-setup.exe",
                "filename": "remote-access-setup.exe",
                "silent_args": ["/S"],
                "check_names": ["Rhelper", "Remote Access"],
                "category": "remote"
            }
        }
        
    def run(self):
        pass
        
    def install_program(self, program_key, silent=True):
        """Устанавливает программу по ключу"""
        if not requests:
            self.log_signal.emit("Библиотека requests не установлена", "error")
            return
            
        if program_key not in self.programs:
            self.log_signal.emit(f"Программа {program_key} не найдена", "error")
            return
            
        program = self.programs[program_key]
        
        if self.check_program_installed(program_key):
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Программа уже установлена')
            msg.setText(f'{program["name"]} уже установлена в системе.\n\nПереустановить?')
            msg.setIcon(QMessageBox.Icon.Question)
            
            yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
            no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(no_button)
            
            msg.exec()
            
            if msg.clickedButton() != yes_button:
                self.log_signal.emit(f"Переустановка {program['name']} отменена", "info")
                return
        
        if not silent:
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Установка программы')
            msg.setText(f'Начать загрузку и установку {program["name"]}?')
            msg.setIcon(QMessageBox.Icon.Question)
            
            yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
            no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(no_button)
            
            msg.exec()
            
            if msg.clickedButton() != yes_button:
                self.log_signal.emit(f"Установка {program['name']} отменена", "info")
                return
                
        self.log_signal.emit(f"Начинаем загрузку {program['name']}...", "info")
        threading.Thread(target=self._download_and_install, args=(program,), daemon=True).start()
        
    def _download_and_install(self, program):
        """Загружает и устанавливает программу"""
        try:
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, program["filename"])
            
            self.log_signal.emit(f"Загрузка {program['name']}...", "info")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(program["url"], stream=True, headers=headers, timeout=60, allow_redirects=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                self.log_signal.emit("Размер файла неизвестен, начинаем загрузку...", "warning")
                total_size = 50 * 1024 * 1024
                
            downloaded = 0
            last_logged_progress = 0
            
            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = min(90, int((downloaded / total_size) * 90))
                        
                        if progress >= last_logged_progress + 10 and progress > 0:
                            self.log_signal.emit(f"Загружено: {progress}%", "info")
                            last_logged_progress = progress
                            
            file_size_mb = os.path.getsize(installer_path) / (1024 * 1024)
            self.log_signal.emit(f"Загрузка завершена ({file_size_mb:.1f} МБ)", "success")
            
            if not os.path.exists(installer_path) or os.path.getsize(installer_path) < 1024:
                self.log_signal.emit("Файл установщика поврежден или не найден", "error")
                return
                
            if program.get("is_zip", False):
                self._handle_zip_installation(program, installer_path)
            else:
                self._handle_regular_installation(program, installer_path)
                
        except requests.RequestException as e:
            self.log_signal.emit(f"Ошибка загрузки {program['name']}: {str(e)}", "error")
        except Exception as e:
            self.log_signal.emit(f"Ошибка установки {program['name']}: {str(e)}", "error")
    
    def _handle_zip_installation(self, program, zip_path):
        """Обрабатывает установку из ZIP архива"""
        try:
            temp_dir = tempfile.gettempdir()
            extract_dir = os.path.join(temp_dir, f"{program['name']}_extracted")
            
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            
            os.makedirs(extract_dir)
            
            self.log_signal.emit(f"Извлечение {program['name']}...", "info")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            self.log_signal.emit(f"Архив извлечен в {extract_dir}", "info")
            
            extract_and_run = program.get("extract_and_run")
            if extract_and_run:
                exe_path = None
                for root, dirs, files in os.walk(extract_dir):
                    if extract_and_run in files:
                        exe_path = os.path.join(root, extract_and_run)
                        break
                
                if exe_path and os.path.exists(exe_path):
                    self.log_signal.emit(f"Запуск установщика: {extract_and_run}", "info")
                    subprocess.Popen([exe_path])
                    self.log_signal.emit(f"{program['name']} - установщик запущен", "success")
                else:
                    self.log_signal.emit(f"Файл {extract_and_run} не найден в архиве", "error")
                    subprocess.Popen(['explorer', extract_dir])
                    self.log_signal.emit(f"Открыта папка с файлами {program['name']}", "info")
            else:
                subprocess.Popen(['explorer', extract_dir])
                self.log_signal.emit(f"Открыта папка с файлами {program['name']}", "info")
            
            try:
                os.remove(zip_path)
                self.log_signal.emit("Временный архив удален", "info")
            except:
                pass
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при работе с архивом: {str(e)}", "error")
    
    def _handle_regular_installation(self, program, installer_path):
        """Обрабатывает обычную установку .exe/.msi"""
        try:
            self.log_signal.emit(f"Начинаем установку {program['name']}...", "info")
            
            is_msi = program.get("is_msi", False) or installer_path.lower().endswith('.msi')
            
            if is_msi:
                install_cmd = ['msiexec', '/i', installer_path] + program.get("silent_args", ['/quiet'])
            else:
                install_cmd = [installer_path] + program.get("silent_args", [])
            
            self.log_signal.emit(f"Команда установки: {' '.join(install_cmd[:2])}", "info")
            
            process = subprocess.Popen(
                install_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            self.log_signal.emit("95%", "info")
            self.log_signal.emit(f"{program['name']} - установка запущена", "success")
            
            def cleanup_and_check():
                try:
                    process.wait(timeout=300)
                    
                    try:
                        os.remove(installer_path)
                        self.log_signal.emit("Временный файл удален", "info")
                    except:
                        pass
                    
                    self.log_signal.emit("100%", "success")
                    
                    if process.returncode == 0:
                        self.log_signal.emit(f"{program['name']} успешно установлена", "success")
                    else:
                        self.log_signal.emit(f"{program['name']} - установка завершена с кодом {process.returncode}", "warning")
                        
                except subprocess.TimeoutExpired:
                    self.log_signal.emit(f"Установка {program['name']} занимает больше времени чем ожидалось", "info")
                except Exception as e:
                    self.log_signal.emit(f"Ошибка в процессе установки: {str(e)}", "error")
            
            threading.Thread(target=cleanup_and_check, daemon=True).start()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка установки {program['name']}: {str(e)}", "error")
            
    def install_from_local_file(self):
        """Устанавливает программу из локального файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            'Выбрать установщик',
            '',
            'Исполняемые файлы (*.exe *.msi *.zip);;Все файлы (*.*)'
        )
        
        if not file_path:
            self.log_signal.emit("Выбор файла отменен", "info")
            return
            
        self.log_signal.emit(f"Запуск установщика: {os.path.basename(file_path)}", "info")
        threading.Thread(target=self._run_local_installer, args=(file_path,), daemon=True).start()
        
    def _run_local_installer(self, file_path):
        """Запускает локальный установщик"""
        try:
            if file_path.lower().endswith('.zip'):
                temp_dir = tempfile.gettempdir()
                extract_dir = os.path.join(temp_dir, "local_installer_extracted")
                
                if os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir)
                
                os.makedirs(extract_dir)
                
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                subprocess.Popen(['explorer', extract_dir])
                self.log_signal.emit("ZIP архив извлечен и папка открыта", "success")
                
            elif file_path.lower().endswith('.msi'):
                subprocess.Popen(['msiexec', '/i', file_path])
                self.log_signal.emit("MSI установщик запущен", "success")
            else:
                subprocess.Popen([file_path])
                self.log_signal.emit("Установщик запущен", "success")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка запуска установщика: {str(e)}", "error")
            
    def check_program_installed(self, program_key):
        """Проверяет, установлена ли программа"""
        try:
            if program_key not in self.programs:
                return False
                
            program = self.programs[program_key]
            check_names = program.get("check_names", [program["name"]])
            
            if sys.platform == "win32":
                for name in check_names:
                    if self._check_in_registry(name) or self._check_in_programs(name):
                        return True
                        
            return False
            
        except Exception:
            return False
    
    def _check_in_registry(self, program_name):
        """Проверяет программу в реестре"""
        try:
            registry_paths = [
                r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
                r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
            ]
            
            for reg_path in registry_paths:
                try:
                    result = subprocess.run([
                        'reg', 'query', reg_path, '/s', '/f', program_name
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0 and program_name.lower() in result.stdout.lower():
                        return True
                except:
                    continue
                    
            return False
            
        except Exception:
            return False
    
    def _check_in_programs(self, program_name):
        """Проверяет программу через wmic"""
        try:
            result = subprocess.run([
                'wmic', 'product', 'where', f'name like "%{program_name}%"',
                'get', 'name'
            ], capture_output=True, text=True, timeout=15)
            
            return result.returncode == 0 and program_name.lower() in result.stdout.lower()
            
        except Exception:
            return False
            
    def get_installed_programs_list(self):
        """Возвращает список установленных программ"""
        try:
            installed = []
            
            for key, program in self.programs.items():
                if self.check_program_installed(key):
                    installed.append((key, program["name"]))
                    
            return installed
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка проверки установленных программ: {str(e)}", "error")
            return []
            
    def uninstall_program(self, program_key):
        """Удаляет программу"""
        try:
            if program_key not in self.programs:
                self.log_signal.emit("Программа не найдена", "error")
                return
                
            program = self.programs[program_key]
            
            if sys.platform != "win32":
                self.log_signal.emit("Автоматическое удаление доступно только в Windows", "error")
                return
                
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Удаление программы')
            msg.setText(f'Удалить {program["name"]}?\n\nОткроется стандартное окно удаления.')
            msg.setIcon(QMessageBox.Icon.Question)
            
            yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
            no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(no_button)
            
            msg.exec()
            
            if msg.clickedButton() != yes_button:
                return
                
            self.log_signal.emit(f"Открытие программ и компонентов для удаления {program['name']}...", "info")
            
            subprocess.Popen(['appwiz.cpl'])
            
            self.log_signal.emit("Найдите программу в списке и удалите вручную", "info")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка удаления {program['name']}: {str(e)}", "error")
            
    def get_programs_by_category(self, category):
        """Возвращает программы по категории"""
        return [(key, prog["name"]) for key, prog in self.programs.items() 
                if prog.get("category") == category]
    
    def add_custom_program(self, name, url, silent_args=None):
        """Добавляет пользовательскую программу"""
        try:
            key = name.lower().replace(' ', '_').replace('-', '_')
            filename = f"{key}_installer.exe"
            
            if url.lower().endswith('.msi'):
                filename = f"{key}_installer.msi"
            elif url.lower().endswith('.zip'):
                filename = f"{key}_installer.zip"
                
            self.programs[key] = {
                "name": name,
                "url": url,
                "filename": filename,
                "silent_args": silent_args or ["/S"],
                "check_names": [name],
                "category": "custom",
                "is_custom": True
            }
            
            self.log_signal.emit(f"Добавлена программа: {name}", "success")
            return key
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка добавления программы: {str(e)}", "error")
            return None