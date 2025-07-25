import subprocess
import sys
import os
import json
import tempfile
import threading
import shutil
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMessageBox

try:
    import requests
except ImportError:
    requests = None

class SimpleUpdateManager(QThread):
    log_signal = pyqtSignal(str, str)
    update_available_signal = pyqtSignal(str, str, str)  # version, notes, download_url
    show_confirmation_signal = pyqtSignal(str, str)  # script_path, new_exe_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_version = "1.1.4"  # Текущая версия приложения
        self.github_repo = "Feuda1/bobrik"
        self.version_url = f"https://raw.githubusercontent.com/{self.github_repo}/main/version.json"
        self.exe_url = f"https://github.com/{self.github_repo}/releases/latest/download/bobrik.exe"
        
        # Подключаем сигналы к слотам в главном потоке
        self.update_available_signal.connect(self._show_update_dialog_in_main_thread)
        self.show_confirmation_signal.connect(self._show_confirmation_dialog)
        
    def run(self):
        pass
        
    def check_for_updates(self):
        """Проверяет наличие обновлений"""
        try:
            if not requests:
                self.log_signal.emit("Для проверки обновлений требуется библиотека requests", "error")
                return
                
            self.log_signal.emit("🔍 Проверка обновлений...", "info")
            threading.Thread(target=self._check_updates_async, daemon=True).start()
            
        except Exception as e:
            self.log_signal.emit(f"❌ Ошибка при проверке обновлений: {str(e)}", "error")
                
    def _check_updates_async(self):
        """Проверяет обновления в отдельном потоке"""
        try:
            headers = {
                'User-Agent': 'bobrik-updater/1.0',
                'Cache-Control': 'no-cache'
            }
            
            # Загружаем информацию о версии
            response = requests.get(self.version_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            version_data = response.json()
            latest_version = version_data.get('version', '')
            release_notes = version_data.get('notes', '')
            download_url = version_data.get('download_url', self.exe_url)
            
            if self._is_newer_version(latest_version, self.current_version):
                self.log_signal.emit(f"🎉 Доступна новая версия: {latest_version}", "success")
                # Отправляем сигнал в главный поток
                self.update_available_signal.emit(latest_version, release_notes, download_url)
            else:
                self.log_signal.emit("✅ У вас установлена последняя версия", "success")
                    
        except requests.RequestException as e:
            self.log_signal.emit(f"🌐 Не удалось проверить обновления: проверьте подключение к интернету", "error")
        except json.JSONDecodeError:
            self.log_signal.emit("📄 Ошибка формата файла версии", "error")
        except Exception as e:
            self.log_signal.emit(f"❌ Ошибка при проверке обновлений: {str(e)}", "error")
                
    def _is_newer_version(self, latest, current):
        """Сравнивает версии (например: 1.0.1 > 1.0.0)"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Дополняем до одинаковой длины
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return False
            
    def _show_update_dialog_in_main_thread(self, version, notes, download_url):
        """Показывает диалог обновления в главном потоке"""
        try:
            if not self.parent:
                return
                
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Доступно обновление bobrik')
            
            text = f'🎉 Новая версия {version} доступна!\n\n'
            
            if notes:
                # Ограничиваем длину описания
                short_notes = notes[:300] + '...' if len(notes) > 300 else notes
                text += f'Что нового:\n{short_notes}\n\n'
                
            text += '💾 Обновить сейчас?'
            
            msg.setText(text)
            msg.setIcon(QMessageBox.Icon.Information)
            
            update_button = msg.addButton('🔄 Обновить', QMessageBox.ButtonRole.YesRole)
            later_button = msg.addButton('⏰ Позже', QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(update_button)
            
            # Показываем диалог синхронно в главном потоке
            result = msg.exec()
            
            if msg.clickedButton() == update_button:
                self.log_signal.emit("📥 Начинаем загрузку обновления...", "info")
                threading.Thread(target=self._download_and_install_update, 
                               args=(download_url, version), daemon=True).start()
            else:
                self.log_signal.emit("⏰ Обновление отложено", "info")
                
        except Exception as e:
            self.log_signal.emit(f"❌ Ошибка диалога обновления: {str(e)}", "error")
            
    def _download_and_install_update(self, download_url, version):
        """Скачивает и устанавливает обновление"""
        try:
            # Создаем временный файл
            temp_dir = tempfile.gettempdir()
            new_exe_path = os.path.join(temp_dir, f"bobrik_{version}.exe")
            
            # Скачиваем новую версию
            headers = {
                'User-Agent': 'bobrik-updater/1.0'
            }
            
            response = requests.get(download_url, stream=True, headers=headers, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_progress = 0
            
            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            if progress >= last_progress + 20:  # Логируем каждые 20%
                                self.log_signal.emit(f"📥 Загружено: {progress}%", "info")
                                last_progress = progress
            
            self.log_signal.emit("✅ Загрузка завершена", "success")
            
            # Проверяем размер файла
            file_size_mb = os.path.getsize(new_exe_path) / (1024 * 1024)
            if file_size_mb < 5:  # Если файл меньше 5 МБ, что-то не так
                self.log_signal.emit("❌ Загруженный файл слишком мал", "error")
                return
                
            self.log_signal.emit(f"📦 Размер файла: {file_size_mb:.1f} МБ", "info")
            
            # Создаем скрипт обновления
            self._create_update_script(new_exe_path)
            
        except Exception as e:
            self.log_signal.emit(f"❌ Ошибка загрузки обновления: {str(e)}", "error")
            
    def _create_update_script(self, new_exe_path):
        """Создает скрипт для замены файла и перезапуска"""
        try:
            current_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
            temp_dir = tempfile.gettempdir()
            script_path = os.path.join(temp_dir, "bobrik_update.bat")
            
            self.log_signal.emit(f"Создание скрипта обновления: {script_path}", "info")
            
            # Создаем batch скрипт для Windows (без эмодзи)
            script_content = f'''@echo off
echo Obnovlenie bobrik...
timeout /t 3 /nobreak > nul

echo Sozdanie rezervnoy kopii...
if exist "{current_exe}.backup" del /q "{current_exe}.backup" 2>nul
ren "{current_exe}" "{os.path.basename(current_exe)}.backup" 2>nul

echo Ustanovka novoy versii...
copy /y "{new_exe_path}" "{current_exe}" 2>nul

if exist "{current_exe}" (
    echo Zapusk obnovlennoy versii...
    start "" "{current_exe}"
    
    echo Ochistka vremennyh faylov...
    timeout /t 2 /nobreak > nul
    del /q "{new_exe_path}" 2>nul
    
    echo Obnovlenie zaversheno uspeshno
) else (
    echo Oshibka obnovleniya, vosstanovlenie rezervnoy kopii...
    ren "{os.path.basename(current_exe)}.backup" "{os.path.basename(current_exe)}" 2>nul
)

del /q "%~f0" 2>nul
'''
            
            with open(script_path, 'w', encoding='ascii', errors='ignore') as f:
                f.write(script_content)
                
            self.log_signal.emit("Скрипт создан, отправляем сигнал для показа диалога", "info")
            
            # Используем сигнал для показа диалога в главном потоке
            self.show_confirmation_signal.emit(script_path, new_exe_path)
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка создания скрипта обновления: {str(e)}", "error")
            
    def _show_confirmation_dialog(self, script_path, new_exe_path):
        """Показ диалога подтверждения через сигнал (выполняется в главном потоке)"""
        try:
            self.log_signal.emit("Показываем диалог подтверждения в главном потоке", "info")
            
            if not self.parent:
                self.log_signal.emit("Родительский виджет не найден", "error")
                return
                
            # Создаем диалог в главном потоке
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Готово к установке')
            msg.setText('Обновление загружено!\n\nСейчас bobrik закроется и обновится.\n\nПродолжить?')
            msg.setIcon(QMessageBox.Icon.Question)
            
            install_button = msg.addButton('Обновить', QMessageBox.ButtonRole.YesRole)
            cancel_button = msg.addButton('Отмена', QMessageBox.ButtonRole.NoRole)
            
            self.log_signal.emit("Диалог создан, показываем пользователю", "info")
            
            # Показываем диалог
            result = msg.exec()
            
            self.log_signal.emit("Диалог закрыт пользователем", "info")
            
            if msg.clickedButton() == install_button:
                self.log_signal.emit("Пользователь выбрал 'Обновить'", "info")
                self._start_update_process(script_path, new_exe_path)
            else:
                self.log_signal.emit("Пользователь выбрал 'Отмена'", "info")
                self._cleanup_update_files(script_path, new_exe_path)
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка диалога подтверждения: {str(e)}", "error")
            
    def _start_update_process(self, script_path, new_exe_path):
        """Запускает процесс обновления"""
        try:
            self.log_signal.emit("Запускаем процесс обновления", "info")
            
            # Запускаем скрипт обновления
            self.log_signal.emit(f"Запуск скрипта: {script_path}", "info")
            process = subprocess.Popen([script_path], shell=True, cwd=os.path.dirname(script_path))
            self.log_signal.emit(f"Скрипт запущен с PID: {process.pid}", "info")
            
            # Планируем закрытие приложения
            self.log_signal.emit("Закрытие приложения через 3 секунды", "info")
            QTimer.singleShot(3000, self._close_application)
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка запуска обновления: {str(e)}", "error")
            
    def _cleanup_update_files(self, script_path, new_exe_path):
        """Очищает файлы обновления при отмене"""
        try:
            if os.path.exists(new_exe_path):
                os.remove(new_exe_path)
                self.log_signal.emit("Временный exe удален", "info")
            if os.path.exists(script_path):
                os.remove(script_path)
                self.log_signal.emit("Скрипт удален", "info")
            self.log_signal.emit("Обновление отменено", "info")
        except Exception as e:
            self.log_signal.emit(f"Ошибка удаления файлов: {str(e)}", "warning")
            
    def _close_application(self):
        """Закрывает приложение"""
        try:
            self.log_signal.emit("Закрываем приложение для обновления", "info")
            if hasattr(self.parent, 'quit_application'):
                self.parent.quit_application()
            else:
                sys.exit(0)
        except Exception as e:
            self.log_signal.emit(f"Ошибка закрытия: {str(e)}", "error")
            sys.exit(0)
            
    def set_github_repo(self, repo_path):
        """Устанавливает путь к репозиторию GitHub"""
        self.github_repo = repo_path
        self.version_url = f"https://raw.githubusercontent.com/{repo_path}/main/version.json"
        self.exe_url = f"https://github.com/{repo_path}/releases/latest/download/bobrik.exe"