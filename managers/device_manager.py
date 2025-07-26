import subprocess
import sys
import os
from PyQt6.QtCore import QThread, pyqtSignal

class DeviceManager(QThread):
    log_signal = pyqtSignal(str, str)  # message, log_type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
    def run(self):
        pass
        
    def open_device_manager(self):
        """Открывает диспетчер устройств"""
        try:
            if sys.platform == "win32":
                # Windows - открываем через devmgmt.msc
                self.log_signal.emit("Открываем диспетчер устройств...", "info")
                subprocess.Popen(['devmgmt.msc'], shell=True)
                self.log_signal.emit("Диспетчер устройств запущен", "success")
                
            elif sys.platform == "linux":
                # Linux - пробуем различные менеджеры устройств
                managers = [
                    ['lshw-gtk'],  # GUI версия lshw
                    ['hardinfo'],  # HardInfo
                    ['gnome-device-manager'],  # GNOME Device Manager
                    ['lsusb'],  # Простой список USB устройств в терминале
                ]
                
                success = False
                for manager in managers:
                    try:
                        subprocess.Popen(manager)
                        self.log_signal.emit(f"Запущен {manager[0]}", "success")
                        success = True
                        break
                    except FileNotFoundError:
                        continue
                
                if not success:
                    # Если GUI менеджеры не найдены, показываем список в терминале
                    self.log_signal.emit("GUI менеджеры устройств не найдены, показываем список в терминале", "warning")
                    subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 'lsusb && lspci && read -p "Нажмите Enter для закрытия..."'])
                    
            elif sys.platform == "darwin":
                # macOS - открываем информацию о системе
                self.log_signal.emit("Открываем информацию о системе macOS...", "info")
                subprocess.Popen(['open', '/Applications/Utilities/System Information.app'])
                self.log_signal.emit("Информация о системе запущена", "success")
                
            else:
                self.log_signal.emit("Диспетчер устройств не поддерживается для данной ОС", "error")
                
        except subprocess.SubprocessError as e:
            self.log_signal.emit(f"Ошибка при запуске диспетчера устройств: {str(e)}", "error")
        except Exception as e:
            self.log_signal.emit(f"Неожиданная ошибка: {str(e)}", "error")
            
    def open_system_info(self):
        """Открывает информацию о системе"""
        try:
            if sys.platform == "win32":
                # Windows - открываем msinfo32
                self.log_signal.emit("Открываем информацию о системе...", "info")
                subprocess.Popen(['msinfo32'])
                self.log_signal.emit("Информация о системе запущена", "success")
                
            elif sys.platform == "linux":
                # Linux - показываем системную информацию
                try:
                    subprocess.Popen(['hardinfo'])
                    self.log_signal.emit("Запущен HardInfo", "success")
                except FileNotFoundError:
                    try:
                        subprocess.Popen(['gnome-system-monitor'])
                        self.log_signal.emit("Запущен системный монитор", "success")
                    except FileNotFoundError:
                        # Показываем информацию в терминале
                        self.log_signal.emit("Показываем информацию о системе в терминале", "info")
                        subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 'uname -a && lscpu && free -h && df -h && read -p "Нажмите Enter для закрытия..."'])
                        
            elif sys.platform == "darwin":
                # macOS
                subprocess.Popen(['open', '/Applications/Utilities/System Information.app'])
                self.log_signal.emit("Информация о системе запущена", "success")
                
            else:
                self.log_signal.emit("Информация о системе не поддерживается для данной ОС", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при открытии информации о системе: {str(e)}", "error")
            
    def open_registry_editor(self):
        """Открывает редактор реестра (только Windows)"""
        try:
            if sys.platform == "win32":
                self.log_signal.emit("Открываем редактор реестра...", "info")
                subprocess.Popen(['regedit'])
                self.log_signal.emit("Редактор реестра запущен", "success")
            else:
                self.log_signal.emit("Редактор реестра доступен только в Windows", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при открытии редактора реестра: {str(e)}", "error")
            
    def open_services(self):
        """Открывает управление службами"""
        try:
            if sys.platform == "win32":
                # Windows - открываем services.msc
                self.log_signal.emit("Открываем управление службами...", "info")
                subprocess.Popen(['services.msc'], shell=True)
                self.log_signal.emit("Управление службами запущено", "success")
                
            elif sys.platform == "linux":
                # Linux - пробуем различные менеджеры служб
                try:
                    subprocess.Popen(['systemctl', 'status', '--no-pager'])
                    self.log_signal.emit("Показываем статус служб в терминале", "info")
                    subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 'systemctl list-units --type=service && read -p "Нажмите Enter для закрытия..."'])
                except FileNotFoundError:
                    self.log_signal.emit("systemctl не найден", "error")
                    
            else:
                self.log_signal.emit("Управление службами не поддерживается для данной ОС", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при открытии управления службами: {str(e)}", "error")