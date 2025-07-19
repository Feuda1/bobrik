import subprocess
import sys
import os
import json
import tempfile
import threading
import shutil
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

try:
    import requests
except ImportError:
    requests = None

class SimpleUpdateManager(QThread):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_version = "1.0.0"  # Текущая версия приложения
        self.github_repo = "Feuda1/bobrik"
        self.version_url = f"https://raw.githubusercontent.com/{self.github_repo}/main/version.json"
        self.exe_url = f"https://github.com/{self.github_repo}/releases/latest/download/bobrik.exe"
        
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
                self._show_update_dialog(latest_version, release_notes, download_url)
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
            
    def _show_update_dialog(self, version, notes, download_url):
        """Показывает диалог обновления"""
        try:
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
            
            msg.exec()
            
            if msg.clickedButton() == update_button:
                self._download_and_install_update(download_url, version)
            else:
                self.log_signal.emit("⏰ Обновление отложено", "info")
                
        except Exception as e:
            self.log_signal.emit(f"❌ Ошибка диалога обновления: {str(e)}", "error")
            
    def _download_and_install_update(self, download_url, version):
        """Скачивает и устанавливает обновление"""
        try:
            self.log_signal.emit(f"📥 Загрузка bobrik {version}...", "info")
            
            # Создаем временный файл
            temp_dir = tempfile.gettempdir()
            new_exe_path = os.path.join(temp_dir, f"bobrik_{version}.exe")
            
            # Скачиваем новую версию
            response = requests.get(download_url, stream=True)
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
            
            # Создаем batch скрипт для Windows
            script_content = f'''@echo off
echo 🔄 Обновление bobrik...
timeout /t 2 /nobreak > nul

echo 📝 Создание резервной копии...
if exist "{current_exe}.backup" del "{current_exe}.backup"
ren "{current_exe}" "{os.path.basename(current_exe)}.backup"

echo 📦 Установка новой версии...
copy "{new_exe_path}" "{current_exe}"

echo 🚀 Запуск обновленной версии...
start "" "{current_exe}"

echo 🧹 Очистка временных файлов...
timeout /t 2 /nobreak > nul
del "{new_exe_path}"
del "%~f0"
'''
            
            with open(script_path, 'w', encoding='cp1251') as f:
                f.write(script_content)
                
            # Показываем финальное подтверждение
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Готово к установке')
            msg.setText('✅ Обновление загружено!\n\n🔄 Сейчас bobrik закроется и обновится.\n\n⚡ Продолжить?')
            msg.setIcon(QMessageBox.Icon.Question)
            
            install_button = msg.addButton('🚀 Обновить', QMessageBox.ButtonRole.YesRole)
            cancel_button = msg.addButton('❌ Отмена', QMessageBox.ButtonRole.NoRole)
            
            msg.exec()
            
            if msg.clickedButton() == install_button:
                self.log_signal.emit("🔄 Запуск установки обновления...", "info")
                
                # Запускаем скрипт обновления
                subprocess.Popen([script_path], shell=True)
                
                # Закрываем приложение
                if hasattr(self.parent, 'quit_application'):
                    self.parent.quit_application()
                else:
                    sys.exit(0)
            else:
                # Удаляем временные файлы
                try:
                    os.remove(new_exe_path)
                    os.remove(script_path)
                except:
                    pass
                self.log_signal.emit("❌ Установка отменена", "info")
                
        except Exception as e:
            self.log_signal.emit(f"❌ Ошибка создания скрипта обновления: {str(e)}", "error")
            
    def set_github_repo(self, repo_path):
        """Устанавливает путь к репозиторию GitHub"""
        self.github_repo = repo_path
        self.version_url = f"https://raw.githubusercontent.com/{repo_path}/main/version.json"
        self.exe_url = f"https://github.com/{repo_path}/releases/latest/download/bobrik.exe"