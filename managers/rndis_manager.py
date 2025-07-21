import subprocess
import sys
import time
import threading
from PyQt6.QtCore import QThread, pyqtSignal

class RndisManager(QThread):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.sharing_enabled = False
        self.saved_public_connection = None   # Сеть с интернетом (публичная)
        self.saved_private_connection = None  # Приватная сеть для расшаривания
        
    def run(self):
        pass
    
    def toggle_internet_sharing(self):
        """Автоматическое переключение общего доступа"""
        try:
            if sys.platform != "win32":
                self.log_signal.emit("Функция доступна только в Windows", "error")
                return
            
            self.log_signal.emit("Запуск автоматического переключения общего доступа...", "info")
            
            # Запускаем в отдельном потоке
            threading.Thread(target=self._auto_sharing_cycle, daemon=True).start()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {str(e)}", "error")
    
    def _auto_sharing_cycle(self):
        """Автоматический цикл включения/выключения"""
        try:
            # Сначала определяем активное интернет-подключение
            self.log_signal.emit("Определяем активное интернет-подключение...", "info")
            active_connection = self._get_active_internet_connection()
            
            if not active_connection:
                self.log_signal.emit("Не удалось определить активное интернет-подключение", "error")
                return
            
            self.log_signal.emit(f"Найдено активное подключение: {active_connection}", "success")
            
            # Сохраняем текущие настройки
            self.log_signal.emit("Сохраняем текущие настройки общего доступа...", "info")
            self._save_current_sharing_settings()
            
            # Выключаем общий доступ только для активного подключения
            self.log_signal.emit("Выключаем общий доступ к интернету...", "warning")
            self._disable_sharing_for_connection(active_connection)
            
            # Ждем 3 секунды
            time.sleep(3)
            
            # Снова включаем с восстановлением настроек
            self.log_signal.emit("Снова включаем общий доступ к интернету...", "info")
            self._enable_sharing_for_connection(active_connection)
            
            self.log_signal.emit("Переключение общего доступа завершено", "success")
            self.log_signal.emit("RNDIS перезагружен", "success")
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {str(e)}", "error")
    
    def _get_active_internet_connection(self):
        """Определяет активное интернет-подключение"""
        try:
            # Метод 1: Через маршрут по умолчанию
            result = subprocess.run([
                'powershell', '-Command', 
                '''
                $route = Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Sort-Object RouteMetric | Select-Object -First 1
                if ($route) {
                    $adapter = Get-NetAdapter -InterfaceIndex $route.InterfaceIndex
                    Write-Output $adapter.Name
                }
                '''
            ], capture_output=True, text=True, timeout=15, 
               creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0 and result.stdout.strip():
                connection_name = result.stdout.strip()
                if connection_name and len(connection_name) > 1:
                    return connection_name
            
            # Метод 2: Через route print (резервный)
            result = subprocess.run(['route', 'print', '0.0.0.0'], 
                                  capture_output=True, text=True, timeout=10,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if '0.0.0.0' in line and 'On-link' not in line:
                        # Ищем интерфейс в строке маршрута
                        parts = line.split()
                        if len(parts) >= 4:
                            # Получаем имя интерфейса по индексу
                            interface_index = parts[-1] if parts[-1].isdigit() else None
                            if interface_index:
                                return self._get_interface_name_by_index(interface_index)
            
            # Метод 3: Через netsh (последний резерв)
            result = subprocess.run(['netsh', 'interface', 'show', 'interface'], 
                                  capture_output=True, text=True, encoding='cp866', 
                                  timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Connected' in line or 'Подключено' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            # Берем последний элемент как имя интерфейса
                            interface_name = ' '.join(parts[3:])
                            if interface_name and 'Ethernet' in interface_name:
                                return interface_name.strip()
                                
            return None
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка определения активного подключения: {str(e)}", "error")
            return None
    
    def _get_interface_name_by_index(self, interface_index):
        """Получает имя интерфейса по индексу"""
        try:
            result = subprocess.run([
                'powershell', '-Command', 
                f'(Get-NetAdapter -InterfaceIndex {interface_index}).Name'
            ], capture_output=True, text=True, timeout=10,
               creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
                
        except Exception:
            pass
        return None
    
    def _disable_sharing_for_connection(self, connection_name):
        """Отключает общий доступ только для указанного подключения"""
        try:
            success_count = 0
            
            # Метод 1: Через COM (самый точный)
            try:
                import win32com.client
                import pythoncom
                
                pythoncom.CoInitialize()
                net_share = win32com.client.Dispatch("HNetCfg.HNetShare")
                
                for connection in net_share.EnumEveryConnection:
                    try:
                        props = net_share.NetConnectionProps(connection)
                        config = net_share.INetSharingConfigurationForINetConnection(connection)
                        
                        # Отключаем только для нужного подключения
                        if props.Name == connection_name and config.SharingEnabled:
                            config.DisableSharing()
                            success_count += 1
                            self.log_signal.emit(f"Отключен общий доступ для {props.Name}", "info")
                            break
                    except Exception:
                        continue
                        
                pythoncom.CoUninitialize()
                
            except Exception:
                # Метод 2: Через netsh (резервный)
                try:
                    result = subprocess.run([
                        'netsh', 'interface', 'set', 'interface', f'name="{connection_name}"', 
                        'admin=disabled'
                    ], capture_output=True, text=True, timeout=10,
                       creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    time.sleep(1)
                    
                    result = subprocess.run([
                        'netsh', 'interface', 'set', 'interface', f'name="{connection_name}"', 
                        'admin=enabled'
                    ], capture_output=True, text=True, timeout=10,
                       creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    if result.returncode == 0:
                        success_count += 1
                        
                except Exception:
                    pass
            
            # Метод 3: Через PowerShell
            try:
                ps_command = f'''
                $adapter = Get-NetAdapter -Name "{connection_name}" -ErrorAction SilentlyContinue
                if ($adapter) {{
                    Disable-NetAdapter -Name "{connection_name}" -Confirm:$false -ErrorAction SilentlyContinue
                    Start-Sleep -Seconds 2
                    Enable-NetAdapter -Name "{connection_name}" -Confirm:$false -ErrorAction SilentlyContinue
                }}
                '''
                
                result = subprocess.run([
                    'powershell', '-Command', ps_command
                ], capture_output=True, text=True, timeout=20,
                   creationflags=subprocess.CREATE_NO_WINDOW)
                
                if result.returncode == 0:
                    success_count += 1
                    
            except Exception:
                pass
            
            if success_count > 0:
                self.log_signal.emit("Общий доступ отключен", "success")
            else:
                self.log_signal.emit("Не удалось отключить общий доступ", "warning")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка отключения: {str(e)}", "error")
    
    def _enable_sharing_for_connection(self, connection_name):
        """Включает общий доступ только для указанного подключения"""
        try:
            success_count = 0
            
            # Метод 1: Через COM (самый точный)
            try:
                import win32com.client
                import pythoncom
                
                pythoncom.CoInitialize()
                net_share = win32com.client.Dispatch("HNetCfg.HNetShare")
                
                for connection in net_share.EnumEveryConnection:
                    try:
                        props = net_share.NetConnectionProps(connection)
                        config = net_share.INetSharingConfigurationForINetConnection(connection)
                        
                        # Включаем только для нужного подключения
                        if props.Name == connection_name:
                            if not config.SharingEnabled:
                                config.EnableSharing(0)  # 0 = публичное подключение (источник интернета)
                                success_count += 1
                                self.log_signal.emit(f"Включен общий доступ для {props.Name}", "info")
                            break
                    except Exception:
                        continue
                        
                pythoncom.CoUninitialize()
                
            except Exception:
                # Метод 2: Через службы
                try:
                    commands = [
                        ['sc', 'config', 'SharedAccess', 'start=auto'],
                        ['net', 'start', 'SharedAccess']
                    ]
                    
                    for cmd in commands:
                        try:
                            result = subprocess.run(cmd, capture_output=True, text=True, 
                                                  timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
                            if result.returncode == 0:
                                success_count += 1
                        except Exception:
                            pass
                            
                except Exception:
                    pass
            
            # Восстанавливаем приватное подключение если было сохранено
            if self.saved_private_connection:
                time.sleep(1)
                self._restore_private_connection()
            
            if success_count > 0:
                self.log_signal.emit("Общий доступ включен", "success")
            else:
                self.log_signal.emit("Частично включен", "warning")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка включения: {str(e)}", "error")
    
    def _save_current_sharing_settings(self):
        """Сохраняет текущие настройки общего доступа"""
        try:
            # Метод 1: Через COM (самый точный)
            try:
                import win32com.client
                import pythoncom
                
                pythoncom.CoInitialize()
                net_share = win32com.client.Dispatch("HNetCfg.HNetShare")
                
                for connection in net_share.EnumEveryConnection:
                    try:
                        props = net_share.NetConnectionProps(connection)
                        config = net_share.INetSharingConfigurationForINetConnection(connection)
                        
                        if config.SharingEnabled:
                            if config.SharingType == 0:  # 0 = публичное подключение
                                self.saved_public_connection = props.Name
                                self.log_signal.emit(f"Сохранена публичная сеть: {props.Name}", "info")
                            elif config.SharingType == 1:  # 1 = приватное подключение
                                self.saved_private_connection = props.Name
                                self.log_signal.emit(f"Сохранена приватная сеть: {props.Name}", "info")
                    except Exception:
                        continue
                        
                pythoncom.CoUninitialize()
                
            except Exception:
                # Метод 2: Через PowerShell как резерв
                try:
                    ps_command = """
                    Get-NetConnectionProfile | Where-Object {$_.NetworkCategory -eq 'Private'} | 
                    Select-Object -First 1 -ExpandProperty InterfaceAlias
                    """
                    
                    result = subprocess.run([
                        'powershell', '-Command', ps_command
                    ], capture_output=True, text=True, timeout=10,
                       creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        self.saved_private_connection = result.stdout.strip()
                        self.log_signal.emit(f"Найдена приватная сеть: {self.saved_private_connection}", "info")
                except Exception:
                    pass
                    
        except Exception as e:
            self.log_signal.emit(f"Ошибка сохранения настроек: {str(e)}", "warning")
    
    def _restore_private_connection(self):
        """Восстанавливает сохраненное приватное подключение"""
        try:
            # Метод 1: Через COM
            try:
                import win32com.client
                import pythoncom
                
                pythoncom.CoInitialize()
                net_share = win32com.client.Dispatch("HNetCfg.HNetShare")
                
                found_and_set = False
                for connection in net_share.EnumEveryConnection:
                    try:
                        props = net_share.NetConnectionProps(connection)
                        config = net_share.INetSharingConfigurationForINetConnection(connection)
                        
                        # Если это нужное нам подключение
                        if props.Name == self.saved_private_connection:
                            # Настраиваем его как приватное
                            if not config.SharingEnabled:
                                config.EnableSharing(1)  # 1 = приватное подключение
                                found_and_set = True
                                self.log_signal.emit(f"Приватная сеть восстановлена: {props.Name}", "success")
                                break
                    except Exception:
                        continue
                        
                if not found_and_set:
                    self.log_signal.emit("Не удалось найти сохраненную сеть через COM", "warning")
                    
                pythoncom.CoUninitialize()
                
            except Exception:
                # Метод 2: Через PowerShell
                try:
                    ps_command = f"""
                    $connectionName = '{self.saved_private_connection}'
                    Set-NetConnectionProfile -InterfaceAlias $connectionName -NetworkCategory Private -ErrorAction SilentlyContinue
                    """
                    
                    result = subprocess.run([
                        'powershell', '-Command', ps_command
                    ], capture_output=True, text=True, timeout=15,
                       creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    if result.returncode == 0:
                        self.log_signal.emit("Приватная сеть восстановлена через PowerShell", "success")
                    else:
                        self.log_signal.emit("Не удалось восстановить через PowerShell", "warning")
                        
                except Exception:
                    self.log_signal.emit("Ошибка восстановления через PowerShell", "warning")
                    
        except Exception as e:
            self.log_signal.emit(f"Ошибка восстановления приватного подключения: {str(e)}", "error")
    
    def restart_rndis(self):
        """Простой перезапуск RNDIS устройств"""
        try:
            self.log_signal.emit("Перезапуск RNDIS устройств...", "info")
            threading.Thread(target=self._restart_rndis_simple, daemon=True).start()
        except Exception as e:
            self.log_signal.emit(f"Ошибка RNDIS: {str(e)}", "error")
    
    def _restart_rndis_simple(self):
        """Простой перезапуск RNDIS"""
        try:
            # Поиск RNDIS устройств
            result = subprocess.run([
                'wmic', 'path', 'Win32_PnPEntity', 'where',
                '"Name LIKE \'%RNDIS%\' OR Name LIKE \'%Android%\'"',
                'get', 'DeviceID'
            ], capture_output=True, text=True, shell=True, encoding='cp866', 
               errors='ignore', timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
            
            device_ids = []
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    if line.strip() and 'DeviceID' not in line:
                        device_id = line.strip()
                        if 'USB' in device_id:
                            device_ids.append(device_id)
            
            if device_ids:
                self.log_signal.emit(f"Найдено {len(device_ids)} RNDIS устройств", "info")
                
                # Отключаем
                for device_id in device_ids:
                    subprocess.run(f'pnputil /disable-device "{device_id}"', 
                                 capture_output=True, shell=True, timeout=10,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                
                time.sleep(2)
                
                # Включаем
                for device_id in device_ids:
                    subprocess.run(f'pnputil /enable-device "{device_id}"', 
                                 capture_output=True, shell=True, timeout=10,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                
                self.log_signal.emit("RNDIS устройства перезапущены", "success")
            else:
                self.log_signal.emit("RNDIS устройства не найдены", "warning")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка перезапуска RNDIS: {str(e)}", "error")