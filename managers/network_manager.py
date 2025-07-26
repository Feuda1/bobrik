import subprocess
import sys
import re
import time
from PyQt6.QtCore import QThread, pyqtSignal

class NetworkManager(QThread):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Кеш для сетевой конфигурации
        self._config_cache = {}
        self._cache_timeout = 30  # 30 секунд
        
    def run(self):
        pass
        
    def run_ipconfig(self):
        """Выполняет ipconfig и показывает только основное подключение"""
        # Проверяем кеш
        current_time = time.time()
        if ('ipconfig' in self._config_cache and 
            current_time - self._config_cache['ipconfig'].get('timestamp', 0) < self._cache_timeout):
            cached_result = self._config_cache['ipconfig']['data']
            self.log_signal.emit("Использован кеш IP конфигурации", "info")
            self.log_signal.emit(cached_result, "success")
            return
            
        try:
            if sys.platform == "win32":
                self.log_signal.emit("Получение IP конфигурации...", "info")
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp866')
                
                if result.returncode == 0:
                    ip_info = self.parse_windows_ipconfig(result.stdout)
                    if ip_info:
                        # Кешируем результат
                        self._config_cache['ipconfig'] = {
                            'data': ip_info,
                            'timestamp': current_time
                        }
                else:
                    self.log_signal.emit(f"Ошибка выполнения ipconfig: {result.stderr}", "error")
                    
            elif sys.platform == "linux":
                self.log_signal.emit("Получение IP конфигурации...", "info")
                try:
                    result = subprocess.run(['ip', 'route', 'get', '8.8.8.8'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self.parse_linux_ip(result.stdout)
                    else:
                        self.parse_linux_fallback()
                except FileNotFoundError:
                    self.parse_linux_fallback()
                    
            elif sys.platform == "darwin":
                self.log_signal.emit("Получение IP конфигурации...", "info")
                result = subprocess.run(['route', 'get', 'default'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.parse_macos_route(result.stdout)
                else:
                    self.log_signal.emit("Ошибка получения маршрута", "error")
                    
            else:
                self.log_signal.emit("Получение IP конфигурации не поддерживается для данной ОС", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при получении IP конфигурации: {str(e)}", "error")
            
    def parse_windows_ipconfig(self, output):
        """Парсит вывод ipconfig для Windows"""
        lines = output.strip().split('\n')
        current_adapter = None
        
        for line in lines:
            line = line.strip()
            
            if 'адаптер' in line.lower() or 'adapter' in line.lower():
                if 'ethernet' in line.lower() or 'wi-fi' in line.lower() or 'wireless' in line.lower():
                    current_adapter = line.replace(':', '').strip()
                    continue
                    
            if current_adapter and ('IPv4' in line or 'IP-адрес' in line):
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    ip = ip_match.group(1)
                    if not ip.startswith('169.254'):
                        adapter_name = self.clean_adapter_name(current_adapter)
                        result = f"{adapter_name}: {ip}"
                        self.log_signal.emit(result, "success")
                        return result
                        
        self.log_signal.emit("Активное подключение не найдено", "warning")
        return None
        
    def parse_linux_ip(self, output):
        """Парсит вывод ip route для Linux"""
        lines = output.strip().split('\n')
        for line in lines:
            if 'src' in line:
                parts = line.split()
                try:
                    src_index = parts.index('src')
                    if src_index + 1 < len(parts):
                        ip = parts[src_index + 1]
                        dev_index = parts.index('dev') if 'dev' in parts else -1
                        if dev_index != -1 and dev_index + 1 < len(parts):
                            interface = parts[dev_index + 1]
                            self.log_signal.emit(f"{interface}: {ip}", "success")
                            return
                except (ValueError, IndexError):
                    continue
                    
        self.log_signal.emit("Активное подключение не найдено", "warning")
        
    def parse_linux_fallback(self):
        """Запасной вариант для Linux"""
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                if ips:
                    self.log_signal.emit(f"Основной IP: {ips[0]}", "success")
                else:
                    self.log_signal.emit("IP адрес не найден", "warning")
            else:
                self.log_signal.emit("Не удалось получить IP адрес", "error")
        except FileNotFoundError:
            self.log_signal.emit("Команды для получения IP не найдены", "error")
            
    def parse_macos_route(self, output):
        """Парсит вывод route для macOS"""
        lines = output.strip().split('\n')
        interface = None
        
        for line in lines:
            if 'interface:' in line:
                interface = line.split(':')[1].strip()
            elif 'src' in line:
                parts = line.split()
                if len(parts) >= 2:
                    ip = parts[1]
                    if interface:
                        self.log_signal.emit(f"{interface}: {ip}", "success")
                    else:
                        self.log_signal.emit(f"Основной IP: {ip}", "success")
                    return
                    
        self.log_signal.emit("Активное подключение не найдено", "warning")
        
    def clean_adapter_name(self, adapter_name):
        """Очищает имя адаптера для более читаемого вывода"""
        adapter_name = adapter_name.lower()
        
        if 'ethernet' in adapter_name:
            return 'Ethernet'
        elif 'wi-fi' in adapter_name or 'wireless' in adapter_name:
            return 'Wi-Fi'
        elif 'bluetooth' in adapter_name:
            return 'Bluetooth'
        else:
            return 'Сетевой адаптер'
            
    def run_netstat(self):
        """Выполняет netstat для показа сетевых соединений"""
        try:
            if sys.platform == "win32":
                self.log_signal.emit("Выполняем netstat -an...", "info")
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, encoding='cp866')
            else:
                self.log_signal.emit("Выполняем netstat -an...", "info")
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
                
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
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