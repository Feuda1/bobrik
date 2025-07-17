import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

class RebootManager(QThread):
    log_signal = pyqtSignal(str, str)  # message, log_type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
    def run(self):
        pass
        
    def request_reboot(self):
        """Запрашивает подтверждение и перезагружает систему"""
        msg = QMessageBox(self.parent)
        msg.setWindowTitle('Подтверждение перезагрузки')
        msg.setText('Точно хотите перезагрузить систему?')
        msg.setIcon(QMessageBox.Icon.Question)
        
        # Создаем кнопки на русском языке
        yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
        no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
        
        msg.setDefaultButton(no_button)
        
        msg.exec()
        
        if msg.clickedButton() == yes_button:
            self.log_signal.emit("Инициирована перезагрузка системы", "warning")
            self.perform_reboot()
        else:
            self.log_signal.emit("Перезагрузка отменена пользователем", "info")
            
    def perform_reboot(self):
        """Выполняет перезагрузку системы"""
        try:
            if sys.platform == "win32":
                # Windows
                self.log_signal.emit("Выполняется перезагрузка Windows...", "warning")
                subprocess.run(['shutdown', '/r', '/t', '0'], check=True)
            elif sys.platform == "linux":
                # Linux
                self.log_signal.emit("Выполняется перезагрузка Linux...", "warning")
                subprocess.run(['sudo', 'reboot'], check=True)
            else:
                self.log_signal.emit("Перезагрузка не поддерживается для данной ОС", "error")
                
        except subprocess.CalledProcessError as e:
            self.log_signal.emit(f"Ошибка при перезагрузке: {str(e)}", "error")
        except Exception as e:
            self.log_signal.emit(f"Неожиданная ошибка: {str(e)}", "error")
            
    def schedule_reboot(self, minutes=1):
        """Планирует перезагрузку через указанное количество минут"""
        msg = QMessageBox(self.parent)
        msg.setWindowTitle('Запланированная перезагрузка')
        msg.setText(f'Запланировать перезагрузку через {minutes} минут?\n\nВы сможете отменить её до истечения времени.')
        msg.setIcon(QMessageBox.Icon.Question)
        
        # Создаем кнопки на русском языке
        yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
        no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
        
        msg.setDefaultButton(no_button)
        
        msg.exec()
        
        if msg.clickedButton() == yes_button:
            try:
                if sys.platform == "win32":
                    seconds = minutes * 60
                    subprocess.run(['shutdown', '/r', '/t', str(seconds)], check=True)
                    self.log_signal.emit(f"Перезагрузка запланирована через {minutes} минут", "warning")
                else:
                    self.log_signal.emit("Планировка перезагрузки поддерживается только на Windows", "error")
                    
            except subprocess.CalledProcessError as e:
                self.log_signal.emit(f"Ошибка при планировании перезагрузки: {str(e)}", "error")
        else:
            self.log_signal.emit("Планирование перезагрузки отменено", "info")
            
    def cancel_scheduled_reboot(self):
        """Отменяет запланированную перезагрузку"""
        try:
            if sys.platform == "win32":
                subprocess.run(['shutdown', '/a'], check=True)
                self.log_signal.emit("Запланированная перезагрузка отменена", "success")
            else:
                self.log_signal.emit("Отмена перезагрузки поддерживается только на Windows", "error")
                
        except subprocess.CalledProcessError as e:
            self.log_signal.emit(f"Ошибка при отмене перезагрузки: {str(e)}", "error")