import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal

class NetworkManager(QThread):
    log_signal = pyqtSignal(str, str)  # message, log_type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
    def run(self):
        pass
        
    def run_ipconfig(self):
        """Выполняет ipconfig и выводит результат в консоль"""
        try:
            if sys.platform == "win32":
                # Windows - ipconfig /all
                self.log_signal.emit("Выполняем ipconfig /all...", "info")
                result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, encoding='cp866')
                
                if result.returncode == 0:
                    # Разбиваем вывод на строки и отправляем по одной
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip():  # Пропускаем пустые строки
                            self.log_signal.emit(line.strip(), "info")
                    self.log_signal.emit("ipconfig выполнен успешно", "success")
                else:
                    self.log_signal.emit(f"Ошибка выполнения ipconfig: {result.stderr}", "error")
                    
            elif sys.platform == "linux":
                # Linux - ifconfig или ip addr
                self.log_signal.emit("Выполняем ifconfig...", "info")
                try:
                    result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if line.strip():
                                self.log_signal.emit(line.strip(), "info")
                        self.log_signal.emit("ifconfig выполнен успешно", "success")
                    else:
                        raise subprocess.CalledProcessError(result.returncode, 'ifconfig')
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Если ifconfig не найден, пробуем ip addr
                    self.log_signal.emit("ifconfig не найден, пробуем ip addr...", "warning")
                    try:
                        result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
                        if result.returncode == 0:
                            lines = result.stdout.strip().split('\n')
                            for line in lines:
                                if line.strip():
                                    self.log_signal.emit(line.strip(), "info")
                            self.log_signal.emit("ip addr выполнен успешно", "success")
                        else:
                            self.log_signal.emit("Ошибка выполнения ip addr", "error")
                    except FileNotFoundError:
                        self.log_signal.emit("Команды ifconfig и ip не найдены", "error")
                        
            elif sys.platform == "darwin":
                # macOS - ifconfig
                self.log_signal.emit("Выполняем ifconfig...", "info")
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            self.log_signal.emit(line.strip(), "info")
                    self.log_signal.emit("ifconfig выполнен успешно", "success")
                else:
                    self.log_signal.emit(f"Ошибка выполнения ifconfig: {result.stderr}", "error")
                    
            else:
                self.log_signal.emit("Получение сетевой информации не поддерживается для данной ОС", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Неожиданная ошибка при выполнении сетевой команды: {str(e)}", "error")
            
    def run_ping(self, host="8.8.8.8", count=4):
        """Выполняет ping указанного хоста"""
        try:
            if sys.platform == "win32":
                # Windows ping
                self.log_signal.emit(f"Выполняем ping {host}...", "info")
                result = subprocess.run(['ping', '-n', str(count), host], capture_output=True, text=True, encoding='cp866')
            else:
                # Linux/macOS ping
                self.log_signal.emit(f"Выполняем ping {host}...", "info")
                result = subprocess.run(['ping', '-c', str(count), host], capture_output=True, text=True)
                
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        self.log_signal.emit(line.strip(), "info")
                self.log_signal.emit(f"ping {host} выполнен успешно", "success")
            else:
                self.log_signal.emit(f"Ошибка ping {host}: {result.stderr}", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при выполнении ping: {str(e)}", "error")
            
    def run_netstat(self):
        """Выполняет netstat для показа сетевых соединений"""
        try:
            if sys.platform == "win32":
                # Windows netstat
                self.log_signal.emit("Выполняем netstat -an...", "info")
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, encoding='cp866')
            else:
                # Linux/macOS netstat
                self.log_signal.emit("Выполняем netstat -an...", "info")
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
                
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Показываем первые 20 строк, чтобы не перегружать консоль
                for i, line in enumerate(lines):
                    if i >= 20:
                        self.log_signal.emit(f"... (показано первых 20 строк из {len(lines)})", "info")
                        break
                    if line.strip():
                        self.log_signal.emit(line.strip(), "info")
                self.log_signal.emit("netstat выполнен успешно", "success")
            else:
                self.log_signal.emit(f"Ошибка выполнения netstat: {result.stderr}", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при выполнении netstat: {str(e)}", "error")
            
    def run_nslookup(self, domain="google.com"):
        """Выполняет nslookup для указанного домена"""
        try:
            self.log_signal.emit(f"Выполняем nslookup {domain}...", "info")
            
            if sys.platform == "win32":
                result = subprocess.run(['nslookup', domain], capture_output=True, text=True, encoding='cp866')
            else:
                result = subprocess.run(['nslookup', domain], capture_output=True, text=True)
                
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        self.log_signal.emit(line.strip(), "info")
                self.log_signal.emit(f"nslookup {domain} выполнен успешно", "success")
            else:
                self.log_signal.emit(f"Ошибка nslookup {domain}: {result.stderr}", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при выполнении nslookup: {str(e)}", "error")