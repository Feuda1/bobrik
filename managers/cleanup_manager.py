import subprocess
import sys
import os
import shutil
import tempfile
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from config import SYSTEM_PATHS

class CleanupManager(QThread):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
    def run(self):
        pass
        
    def clean_temp_files(self):
        """Очищает временные файлы"""
        try:
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Очистка временных файлов')
            msg.setText('Начать очистку временных файлов?\n\nБудут очищены:\n- Папка %TEMP%\n- Корзина\n- Кэш браузеров\n- Временные файлы Windows')
            msg.setIcon(QMessageBox.Icon.Question)
            
            yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
            no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(no_button)
            
            msg.exec()
            
            if msg.clickedButton() != yes_button:
                self.log_signal.emit("Очистка отменена пользователем", "info")
                return
                
            self.log_signal.emit("Начинаем очистку временных файлов...", "info")
            threading.Thread(target=self._perform_cleanup, daemon=True).start()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при очистке: {str(e)}", "error")
            
    def _perform_cleanup(self):
        """Выполняет очистку в отдельном потоке"""
        try:
            cleaned_folders = 0
            total_size = 0
            
            for temp_folder in SYSTEM_PATHS['temp_folders']:
                if temp_folder and os.path.exists(temp_folder):
                    size_cleaned = self._clean_folder(temp_folder)
                    if size_cleaned > 0:
                        cleaned_folders += 1
                        total_size += size_cleaned
                        
            self._clean_recycle_bin()
            self._clean_browser_cache()
            self._run_disk_cleanup()
            
            size_mb = total_size / (1024 * 1024)
            self.log_signal.emit(f"Очистка завершена. Освобождено: {size_mb:.1f} МБ", "success")
        except Exception as e:
            self.log_signal.emit(f"Ошибка при очистке: {str(e)}", "error")
            
    def _clean_folder(self, folder_path):
        """Очищает указанную папку"""
        try:
            if not os.path.exists(folder_path):
                return 0
                
            total_size = 0
            files_deleted = 0
            
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        total_size += file_size
                        files_deleted += 1
                    except (OSError, PermissionError):
                        continue
                        
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        shutil.rmtree(dir_path, ignore_errors=True)
                    except (OSError, PermissionError):
                        continue
                        
            if files_deleted > 0:
                self.log_signal.emit(f"Очищена папка {folder_path}: {files_deleted} файлов", "info")
                
            return total_size
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при очистке папки {folder_path}: {str(e)}", "warning")
            return 0
            
    def _clean_recycle_bin(self):
        """Очищает корзину"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(['rd', '/s', '/q', r'C:\$Recycle.Bin'], 
                                      shell=True, capture_output=True)
                if result.returncode == 0:
                    self.log_signal.emit("Корзина очищена", "info")
                else:
                    self.log_signal.emit("Не удалось очистить корзину", "warning")
        except Exception:
            pass
            
    def _clean_browser_cache(self):
        """Очищает кэш браузеров"""
        try:
            username = os.getenv('USERNAME')
            browser_paths = [
                f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache",
                f"C:\\Users\\{username}\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache",
                f"C:\\Users\\{username}\\AppData\\Local\\Mozilla\\Firefox\\Profiles",
                f"C:\\Users\\{username}\\AppData\\Roaming\\Opera Software\\Opera Stable\\Cache"
            ]
            
            for path in browser_paths:
                if os.path.exists(path):
                    size_cleaned = self._clean_folder(path)
                    if size_cleaned > 0:
                        browser_name = path.split('\\')[-3] if '\\' in path else "браузер"
                        self.log_signal.emit(f"Очищен кэш {browser_name}", "info")
                        
        except Exception:
            pass
            
    def _run_disk_cleanup(self):
        """Запускает встроенную очистку диска Windows"""
        try:
            if sys.platform == "win32":
                subprocess.Popen(['cleanmgr', '/sagerun:1'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                self.log_signal.emit("Запущена системная очистка диска", "info")
        except Exception:
            pass
            
    def disable_windows_defender(self):
        """Отключает защитник Windows и брандмауэр"""
        try:
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Отключение защитных функций')
            msg.setText('ВНИМАНИЕ! Это отключит:\n- Защитник Windows\n- Брандмауэр Windows\n- Контроль учетных записей (UAC)\n\nВы уверены?')
            msg.setIcon(QMessageBox.Icon.Warning)
            
            yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
            no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(no_button)
            
            msg.exec()
            
            if msg.clickedButton() != yes_button:
                self.log_signal.emit("Отключение защитных функций отменено", "info")
                return
                
            if sys.platform != "win32":
                self.log_signal.emit("Функция доступна только в Windows", "error")
                return
                
            self.log_signal.emit("Отключаем защитные функции Windows...", "warning")
            
            commands = [
                ['powershell', '-Command', 'Set-MpPreference -DisableRealtimeMonitoring $true'],
                ['powershell', '-Command', 'Set-MpPreference -DisableBehaviorMonitoring $true'],
                ['powershell', '-Command', 'Set-MpPreference -DisableIOAVProtection $true'],
                ['powershell', '-Command', 'Set-MpPreference -DisablePrivacyMode $true'],
                ['powershell', '-Command', 'Set-MpPreference -SignatureDisableUpdateOnStartupWithoutEngine $true'],
                ['netsh', 'advfirewall', 'set', 'allprofiles', 'state', 'off'],
                ['reg', 'add', 'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System', '/v', 'EnableLUA', '/t', 'REG_DWORD', '/d', '0', '/f']
            ]
            
            success_count = 0
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        success_count += 1
                except Exception:
                    continue
                    
            if success_count >= 5:
                self.log_signal.emit("Защитные функции отключены (требуется перезагрузка)", "warning")
            else:
                self.log_signal.emit("Частично отключены защитные функции (требуются права администратора)", "warning")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при отключении защитных функций: {str(e)}", "error")
            
    def restart_print_spooler(self):
        """Перезапускает диспетчер печати"""
        try:
            if sys.platform != "win32":
                self.log_signal.emit("Функция доступна только в Windows", "error")
                return
                
            self.log_signal.emit("Перезапуск диспетчера печати...", "info")
            
            subprocess.run(['net', 'stop', 'spooler'], capture_output=True, check=True)
            self.log_signal.emit("Служба диспетчера печати остановлена", "info")
            
            subprocess.run(['net', 'start', 'spooler'], capture_output=True, check=True)
            self.log_signal.emit("Служба диспетчера печати запущена", "success")
            
        except subprocess.CalledProcessError as e:
            self.log_signal.emit("Не удалось перезапустить диспетчер печати (требуются права администратора)", "error")
        except Exception as e:
            self.log_signal.emit(f"Ошибка при перезапуске диспетчера печати: {str(e)}", "error")
            
    def clear_print_queue(self):
        """Очищает очередь печати"""
        try:
            if sys.platform != "win32":
                self.log_signal.emit("Функция доступна только в Windows", "error")
                return
                
            self.log_signal.emit("Очистка очереди печати...", "info")
            threading.Thread(target=self._clear_print_queue_async, daemon=True).start()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при очистке очереди печати: {str(e)}", "error")
            
    def _clear_print_queue_async(self):
        """Очищает очередь печати в отдельном потоке"""
        try:
            subprocess.run(['net', 'stop', 'spooler'], capture_output=True)
            
            spool_path = r"C:\Windows\System32\spool\PRINTERS"
            if os.path.exists(spool_path):
                files_deleted = 0
                for file in os.listdir(spool_path):
                    try:
                        os.remove(os.path.join(spool_path, file))
                        files_deleted += 1
                    except:
                        continue
                        
                self.log_signal.emit(f"Удалено {files_deleted} файлов из очереди печати", "info")
            
            subprocess.run(['net', 'start', 'spooler'], capture_output=True)
            self.log_signal.emit("Очередь печати очищена", "success")
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при очистке очереди печати: {str(e)}", "error")
            
    def open_startup_folder(self):
        """Открывает папку автозагрузки"""
        try:
            startup_path = SYSTEM_PATHS['startup_folder']
            
            if not os.path.exists(startup_path):
                os.makedirs(startup_path, exist_ok=True)
                
            subprocess.Popen(['explorer', startup_path])
            self.log_signal.emit("Открыта папка автозагрузки", "success")
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при открытии папки автозагрузки: {str(e)}", "error")
            
    def configure_tls(self):
        """Настраивает TLS 1.2 в реестре"""
        try:
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Настройка TLS 1.2')
            msg.setText('Настроить TLS 1.2 в реестре?\n\nЭто включит поддержку TLS 1.2 для клиента и сервера.')
            msg.setIcon(QMessageBox.Icon.Question)
            
            yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
            no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(no_button)
            
            msg.exec()
            
            if msg.clickedButton() != yes_button:
                self.log_signal.emit("Настройка TLS отменена", "info")
                return
                
            if sys.platform != "win32":
                self.log_signal.emit("Функция доступна только в Windows", "error")
                return
                
            self.log_signal.emit("Настраиваем TLS 1.2...", "info")
            threading.Thread(target=self._configure_tls_async, daemon=True).start()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при настройке TLS: {str(e)}", "error")
            
    def open_devices_and_printers(self):
        """Открывает устройства и принтеры"""
        try:
            if sys.platform == "win32":
                subprocess.Popen(['control', 'printers'])
                self.log_signal.emit("Открыты устройства и принтеры", "success")
            else:
                self.log_signal.emit("Функция доступна только в Windows", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при открытии устройств и принтеров: {str(e)}", "error")
            
    def open_control_panel(self):
        """Открывает панель управления"""
        try:
            if sys.platform == "win32":
                subprocess.Popen(['control'])
                self.log_signal.emit("Открыта панель управления", "success")
            else:
                self.log_signal.emit("Функция доступна только в Windows", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при открытии панели управления: {str(e)}", "error")
            
    def _configure_tls_async(self):
        """Настраивает TLS в отдельном потоке"""
        try:
            registry_commands = [
                ['reg', 'add', 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\TLS 1.2', '/f'],
                ['reg', 'add', 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\TLS 1.2\\Client', '/f'],
                ['reg', 'add', 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\TLS 1.2\\Server', '/f'],
                ['reg', 'add', 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\TLS 1.2\\Client', '/v', 'Enabled', '/t', 'REG_DWORD', '/d', '1', '/f'],
                ['reg', 'add', 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\TLS 1.2\\Client', '/v', 'DisabledByDefault', '/t', 'REG_DWORD', '/d', '0', '/f'],
                ['reg', 'add', 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\TLS 1.2\\Server', '/v', 'Enabled', '/t', 'REG_DWORD', '/d', '1', '/f'],
                ['reg', 'add', 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\TLS 1.2\\Server', '/v', 'DisabledByDefault', '/t', 'REG_DWORD', '/d', '0', '/f']
            ]
            
            success_count = 0
            
            for cmd in registry_commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        success_count += 1
                except Exception:
                    continue
                    
            if success_count >= 6:
                self.log_signal.emit("TLS 1.2 успешно настроен в реестре", "success")
                self.log_signal.emit("Для применения изменений рекомендуется перезагрузка", "info")
            elif success_count > 0:
                self.log_signal.emit(f"TLS частично настроен ({success_count}/7 команд выполнено)", "warning")
                self.log_signal.emit("Возможно требуются права администратора", "warning")
            else:
                self.log_signal.emit("Не удалось настроить TLS (требуются права администратора)", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при настройке TLS: {str(e)}", "error")