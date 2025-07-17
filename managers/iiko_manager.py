import subprocess
import sys
import os
import time
import threading
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from config import IIKO_PATHS, IIKO_CARD_URL

try:
    import psutil
except ImportError:
    psutil = None

try:
    import requests
except ImportError:
    requests = None

class IikoManager(QThread):
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
    def run(self):
        pass
        
    def close_iiko_front(self):
        """Закрывает процесс iikoFront.Net"""
        try:
            if not psutil:
                self.log_signal.emit("Библиотека psutil не установлена, используем taskkill", "warning")
                self._close_iiko_with_taskkill()
                return
                
            self.log_signal.emit("Поиск процесса iikoFront.Net...", "info")
            
            found_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                if 'iikofront' in proc.info['name'].lower():
                    found_processes.append(proc)
            
            if not found_processes:
                self.log_signal.emit("Процесс iikoFront.Net не найден", "warning")
                return
                
            for proc in found_processes:
                try:
                    proc.terminate()
                    proc.wait(timeout=10)
                    self.log_signal.emit(f"Процесс {proc.info['name']} (PID: {proc.info['pid']}) закрыт", "success")
                except psutil.TimeoutExpired:
                    proc.kill()
                    self.log_signal.emit(f"Процесс {proc.info['name']} принудительно завершен", "warning")
                except Exception as e:
                    self.log_signal.emit(f"Ошибка при закрытии процесса: {str(e)}", "error")
                    
        except Exception as e:
            self.log_signal.emit(f"Ошибка при поиске процессов: {str(e)}", "error")
            
    def _close_iiko_with_taskkill(self):
        """Закрывает iiko через taskkill если psutil недоступен"""
        try:
            result = subprocess.run(['taskkill', '/f', '/im', 'iikoFront.Net.exe'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log_signal.emit("Процесс iikoFront.Net закрыт", "success")
            else:
                self.log_signal.emit("Процесс iikoFront.Net не найден", "warning")
        except Exception as e:
            self.log_signal.emit(f"Ошибка при закрытии через taskkill: {str(e)}", "error")
            
    def restart_iiko_front(self):
        """Перезапускает iikoFront.Net"""
        try:
            self.log_signal.emit("Начинаем перезапуск iikoFront.Net...", "info")
            threading.Thread(target=self._restart_iiko_async, daemon=True).start()
        except Exception as e:
            self.log_signal.emit(f"Ошибка при перезапуске iikoFront.Net: {str(e)}", "error")
            
    def _restart_iiko_async(self):
        """Перезапускает iikoFront в отдельном потоке"""
        try:
            self.close_iiko_front()
            time.sleep(2)
            
            if not os.path.exists(IIKO_PATHS['executable']):
                self.log_signal.emit("Исполняемый файл iikoFront.Net не найден", "error")
                return
                
            self.log_signal.emit("Запуск iikoFront.Net...", "info")
            subprocess.Popen([IIKO_PATHS['executable']], 
                           cwd=os.path.dirname(IIKO_PATHS['executable']))
            self.log_signal.emit("iikoFront.Net запущен", "success")
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при перезапуске iikoFront.Net: {str(e)}", "error")
            
    def restart_com_ports(self):
        """Перезапускает все COM порты"""
        try:
            if sys.platform != "win32":
                self.log_signal.emit("Функция доступна только в Windows", "error")
                return
                
            self.log_signal.emit("Поиск COM портов...", "info")
            
            result = subprocess.run([
                'wmic', 'path', 'Win32_PnPEntity', 'where', 
                '"Name LIKE \'%COM%\' OR Name LIKE \'%Serial%\'"',
                'get', 'Name,DeviceID'
            ], capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
            
            if result.returncode != 0:
                self.log_signal.emit("Не удалось получить список COM портов", "error")
                return
                
            lines = result.stdout.strip().split('\n')
            device_ids = []
            
            for line in lines[1:]:
                if line.strip() and 'DeviceID' not in line:
                    parts = line.strip().split()
                    if parts:
                        device_id = parts[-1]
                        if device_id.startswith('USB') or 'COM' in device_id:
                            device_ids.append(device_id)
                            self.log_signal.emit(f"Найден COM порт: {line.strip()}", "info")
                            
            if not device_ids:
                self.log_signal.emit("COM порты не найдены", "warning")
                return
                
            disabled_count = 0
            enabled_count = 0
            
            for device_id in device_ids:
                try:
                    subprocess.run(f'pnputil /disable-device "{device_id}"', 
                                 capture_output=True, shell=True, check=True)
                    disabled_count += 1
                except:
                    pass
                    
            time.sleep(2)
            
            for device_id in device_ids:
                try:
                    subprocess.run(f'pnputil /enable-device "{device_id}"', 
                                 capture_output=True, shell=True, check=True)
                    enabled_count += 1
                except:
                    pass
                    
            if enabled_count > 0:
                self.log_signal.emit(f"Перезапущено {enabled_count} COM портов", "success")
            else:
                self.log_signal.emit("Не удалось перезапустить COM порты (требуются права администратора)", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при перезапуске COM портов: {str(e)}", "error")
            
    def update_iiko_card(self):
        """Обновляет iikoCard"""
        try:
            if not requests:
                self.log_signal.emit("Библиотека requests не установлена", "error")
                return
                
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Обновление iikoCard')
            msg.setText('Начать загрузку и установку iikoCard?')
            msg.setIcon(QMessageBox.Icon.Question)
            
            yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
            no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(no_button)
            
            msg.exec()
            
            if msg.clickedButton() != yes_button:
                self.log_signal.emit("Обновление iikoCard отменено", "info")
                return
                
            self.log_signal.emit("Начинаем загрузку iikoCard...", "info")
            
            threading.Thread(target=self._download_and_install_iiko_card, daemon=True).start()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при запуске обновления iikoCard: {str(e)}", "error")
            
    def _download_and_install_iiko_card(self):
        """Скачивает и устанавливает iikoCard в отдельном потоке"""
        try:
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, "iikoCard_installer.exe")
            
            response = requests.get(IIKO_CARD_URL, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                self.log_signal.emit("Не удалось определить размер файла", "warning")
                total_size = 10 * 1024 * 1024
                
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
                            
            self.log_signal.emit("Загрузка завершена, начинаем установку...", "info")
            
            process = subprocess.Popen([installer_path], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
            
            self.log_signal.emit("100%", "info")
            self.log_signal.emit("iikoCard установка запущена", "success")
            
            try:
                os.remove(installer_path)
            except:
                pass
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при загрузке/установке iikoCard: {str(e)}", "error")