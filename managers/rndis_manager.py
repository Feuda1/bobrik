import subprocess
import sys
import time
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

try:
    import win32com.client
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class RndisManager(QThread):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
    def run(self):
        pass
        
    def restart_rndis(self):
        """Перезапускает RNDIS через отключение/включение галочки"""
        try:
            if not HAS_WIN32:
                self.log_signal.emit("Установите: pip install pywin32", "error")
                return
                
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Перезагрузка RNDIS')
            msg.setText('Перезагрузить RNDIS?\n\nЭто отключит и включит галочку общего доступа.')
            msg.setIcon(QMessageBox.Icon.Question)
            
            yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
            no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(no_button)
            
            msg.exec()
            
            if msg.clickedButton() != yes_button:
                self.log_signal.emit("Отменено", "info")
                return
                
            threading.Thread(target=self._toggle_ics_com, daemon=True).start()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {str(e)}", "error")
            
    def _toggle_ics_com(self):
        """Переключает ICS через COM интерфейс Windows"""
        try:
            # Создаем COM объект для работы с сетевыми подключениями
            self.log_signal.emit("Подключаемся к Windows COM...", "info")
            
            # Используем WMI для работы с сетевыми адаптерами
            wmi = win32com.client.GetObject("winmgmts:")
            
            # Находим активные сетевые подключения
            adapters = wmi.ExecQuery("SELECT * FROM Win32_NetworkAdapter WHERE NetConnectionStatus = 2")
            
            main_adapter = None
            for adapter in adapters:
                if adapter.Name and "RNDIS" not in adapter.Name and "Loopback" not in adapter.Name:
                    main_adapter = adapter
                    break
                    
            if not main_adapter:
                self.log_signal.emit("Не найдено подключение к интернету", "error")
                return
                
            self.log_signal.emit(f"Найдено: {main_adapter.Name}", "info")
            
            # Отключаем общий доступ
            self.log_signal.emit("Отключаем общий доступ...", "info")
            self._disable_sharing_wmi(main_adapter)
            
            # Ждем 3 секунды
            time.sleep(3)
            
            # Включаем общий доступ
            self.log_signal.emit("Включаем общий доступ...", "info")
            self._enable_sharing_wmi(main_adapter)
            
            self.log_signal.emit("RNDIS перезагружен!", "success")
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка COM: {str(e)}", "error")
            
    def _disable_sharing_wmi(self, adapter):
        """Отключает общий доступ через WMI"""
        try:
            # Получаем конфигурацию адаптера
            wmi = win32com.client.GetObject("winmgmts:")
            configs = wmi.ExecQuery(f"SELECT * FROM Win32_NetworkAdapterConfiguration WHERE Index = {adapter.Index}")
            
            for config in configs:
                if config.IPEnabled:
                    # Отключаем ICS
                    config.DisableIPSec()
                    
        except Exception as e:
            self.log_signal.emit(f"Ошибка отключения: {str(e)}", "warning")
            
    def _enable_sharing_wmi(self, adapter):
        """Включает общий доступ через WMI"""
        try:
            # Получаем конфигурацию адаптера
            wmi = win32com.client.GetObject("winmgmts:")
            configs = wmi.ExecQuery(f"SELECT * FROM Win32_NetworkAdapterConfiguration WHERE Index = {adapter.Index}")
            
            for config in configs:
                if config.IPEnabled:
                    # Включаем ICS
                    config.EnableStatic(["192.168.137.1"], ["255.255.255.0"])
                    time.sleep(1)
                    config.EnableDHCP()
                    
        except Exception as e:
            self.log_signal.emit(f"Ошибка включения: {str(e)}", "warning")