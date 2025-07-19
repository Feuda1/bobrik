import subprocess
import sys
import time
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from config import TOUCHSCREEN_KEYWORDS

class TouchscreenManager(QThread):
    log_signal = pyqtSignal(str, str)  # message, log_type
    status_signal = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.is_disabled = False
        self.device_ids = []
        
    def run(self):
        pass  # Не ищем устройства автоматически при запуске
        
    def find_touchscreen_devices(self):
        try:
            if sys.platform == "win32":
                result = subprocess.run(['wmic', 'path', 'Win32_PnPEntity', 'where', 
                                       'ConfigManagerErrorCode=0', 'get', 'Name,DeviceID'], 
                                       capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
                
                lines = result.stdout.strip().split('\n')
                self.device_ids = []
                
                for line in lines:
                    lower_line = line.lower()
                    if any(keyword in lower_line for keyword in TOUCHSCREEN_KEYWORDS):
                        parts = line.split()
                        if parts:
                            device_id = parts[-1]
                            if 'HID' in device_id or 'USB' in device_id:
                                self.device_ids.append(device_id)
                                self.log_signal.emit(f"Найдено устройство: {line.strip()}", "info")
                
                if not self.device_ids:
                    self.log_signal.emit("Сенсорные устройства не найдены", "warning")
                else:
                    self.log_signal.emit(f"Найдено {len(self.device_ids)} сенсорных устройств", "success")
                    
            else:
                self.log_signal.emit("Поддерживается только Windows", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при поиске устройств: {str(e)}", "error")
    
    def toggle_touchscreen(self):
        if not self.device_ids:
            self.log_signal.emit("Поиск сенсорных устройств...", "info")
            self.find_touchscreen_devices()
            
        if not self.device_ids:
            self.log_signal.emit("Нет устройств для управления", "error")
            return
            
        if self.is_disabled:
            self.enable_touchscreen()
        else:
            self.disable_touchscreen()
            
    def disable_touchscreen(self):
        try:
            success_count = 0
            for device_id in self.device_ids:
                cmd = f'pnputil /disable-device "{device_id}"'
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
                if result.returncode == 0:
                    success_count += 1
                    
            if success_count > 0:
                self.is_disabled = True
                self.status_signal.emit(True)
                self.log_signal.emit(f"Сенсорный экран отключен ({success_count} устройств)", "success")
                self.show_desktop_notification(True)
            else:
                self.log_signal.emit("Не удалось отключить устройства (требуются права администратора)", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при отключении: {str(e)}", "error")
            
    def enable_touchscreen(self):
        try:
            success_count = 0
            for device_id in self.device_ids:
                cmd = f'pnputil /enable-device "{device_id}"'
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
                if result.returncode == 0:
                    success_count += 1
                    
            if success_count > 0:
                self.is_disabled = False
                self.status_signal.emit(False)
                self.log_signal.emit(f"Сенсорный экран включен ({success_count} устройств)", "success")
                self.show_desktop_notification(False)
            else:
                self.log_signal.emit("Не удалось включить устройства", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при включении: {str(e)}", "error")
            
    def reboot_touchscreen(self):
        """Перезапускает сенсорный экран (отключает и снова включает)"""
        try:
            if not self.device_ids:
                self.log_signal.emit("Поиск сенсорных устройств...", "info")
                self.find_touchscreen_devices()
                
            if not self.device_ids:
                self.log_signal.emit("Сенсорные устройства не найдены для перезапуска", "error")
                return
                
            self.log_signal.emit("Начинаем перезапуск сенсорного экрана...", "info")
            
            # Запускаем перезапуск в отдельном потоке
            threading.Thread(target=self._reboot_touchscreen_async, daemon=True).start()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при перезапуске сенсорного экрана: {str(e)}", "error")
            
    def _reboot_touchscreen_async(self):
        """Выполняет перезапуск сенсорного экрана в отдельном потоке"""
        try:
            # Сохраняем текущий статус
            was_disabled = self.is_disabled
            
            # Этап 1: Отключаем все сенсорные устройства
            self.log_signal.emit("Отключаем сенсорные устройства...", "info")
            disabled_count = 0
            
            for device_id in self.device_ids:
                try:
                    cmd = f'pnputil /disable-device "{device_id}"'
                    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
                    if result.returncode == 0:
                        disabled_count += 1
                except:
                    continue
                    
            if disabled_count > 0:
                self.log_signal.emit(f"Отключено {disabled_count} сенсорных устройств", "info")
            else:
                self.log_signal.emit("Не удалось отключить устройства", "warning")
                return
                
            # Этап 2: Ждем 3 секунды
            self.log_signal.emit("Ожидание 3 секунды...", "info")
            time.sleep(3)
            
            # Этап 3: Включаем все сенсорные устройства обратно
            self.log_signal.emit("Включаем сенсорные устройства...", "info")
            enabled_count = 0
            
            for device_id in self.device_ids:
                try:
                    cmd = f'pnputil /enable-device "{device_id}"'
                    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
                    if result.returncode == 0:
                        enabled_count += 1
                except:
                    continue
                    
            if enabled_count > 0:
                # Восстанавливаем исходный статус
                if was_disabled:
                    self.is_disabled = True
                    self.status_signal.emit(True)
                else:
                    self.is_disabled = False
                    self.status_signal.emit(False)
                    
                self.log_signal.emit(f"Включено {enabled_count} сенсорных устройств", "info")
                self.log_signal.emit("Перезапуск сенсорного экрана завершен", "success")
                
                # Показываем уведомление о завершении
                self.show_desktop_notification_reboot()
            else:
                self.log_signal.emit("Не удалось включить устройства", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при перезапуске: {str(e)}", "error")
            
    def show_desktop_notification(self, is_disabled):
        """Показывает уведомление о включении/отключении"""
        try:
            if is_disabled:
                subprocess.Popen(['msg', '*', '/TIME:3', 'Сенсорный экран ОТКЛЮЧЕН'], 
                               shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(['msg', '*', '/TIME:3', 'Сенсорный экран ВКЛЮЧЕН'], 
                               shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
            
    def show_desktop_notification_reboot(self):
        """Показывает уведомление о перезапуске"""
        try:
            subprocess.Popen(['msg', '*', '/TIME:4', 'Сенсорный экран ПЕРЕЗАПУЩЕН'], 
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass