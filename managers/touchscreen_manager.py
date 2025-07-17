import subprocess
import sys
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
            
    def show_desktop_notification(self, is_disabled):
        if is_disabled:
            subprocess.Popen(['msg', '*', '/TIME:3', 'Сенсорный экран ОТКЛЮЧЕН'], 
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)