import subprocess
import win32com.client
import wmi
import pythoncom
import ctypes
import sys
import logging
import json
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Dict, Optional, Union

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Кастомные исключения
class IcsError(Exception):
    """Базовое исключение для ICS операций"""
    pass

class InsufficientPrivilegesError(IcsError):
    """Недостаточно прав для выполнения операции"""
    pass

class NetworkAdapterError(IcsError):
    """Ошибка сетевого адаптера"""
    pass

class ServiceError(IcsError):
    """Ошибка службы ICS"""
    pass

@dataclass
class NetworkConnection:
    """Информация о сетевом подключении"""
    name: str
    guid: str
    device_name: str
    status: int
    media_type: int
    sharing_enabled: bool = False
    sharing_type: Optional[int] = None

class RndisManager:
    """
    Комплексный менеджер для управления Internet Connection Sharing (ICS)
    Поддерживает различные методы: COM, PowerShell, WMI
    """
    
    def __init__(self, prefer_powershell: bool = True):
        """
        Инициализация RndisManager
        
        Args:
            prefer_powershell: Предпочитать PowerShell методы вместо COM
        """
        self.prefer_powershell = prefer_powershell
        self._wmi_connection = None
        self._net_share = None
        self._ps_module_available = False
        
        # Проверка системных требований
        if not self._check_admin_rights():
            raise InsufficientPrivilegesError("Administrator rights required")
        
        self._initialize_connections()
    
    def _check_admin_rights(self) -> bool:
        """Проверка прав администратора"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _initialize_connections(self):
        """Инициализация подключений к системным сервисам"""
        try:
            # Инициализация COM
            pythoncom.CoInitialize()
            
            # Регистрация библиотеки hnetcfg.dll
            subprocess.run(['regsvr32', '/s', 'hnetcfg.dll'], 
                         shell=True, check=False)
            
            # Создание COM объекта
            self._net_share = win32com.client.Dispatch("HNetCfg.HNetShare")
            
            # Инициализация WMI
            self._wmi_connection = wmi.WMI()
            
            # Проверка доступности PowerShell модуля
            self._ps_module_available = self._check_powershell_module()
            
            logger.info("RndisManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RndisManager: {e}")
            raise IcsError(f"Initialization failed: {e}")
    
    def _check_powershell_module(self) -> bool:
        """Проверка наличия модуля PSInternetConnectionSharing"""
        try:
            result = subprocess.run([
                "powershell.exe", "-Command",
                "Get-Module -ListAvailable -Name PSInternetConnectionSharing"
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0 and result.stdout.strip()
        except:
            return False
    
    @contextmanager
    def _safe_com_context(self):
        """Контекстный менеджер для безопасной работы с COM"""
        try:
            yield self._net_share
        except Exception as e:
            logger.error(f"COM operation failed: {e}")
            raise IcsError(f"COM error: {e}")
    
    def _run_powershell_command(self, command: str, timeout: int = 30) -> Dict:
        """
        Выполнение PowerShell команды с обработкой ошибок
        
        Args:
            command: PowerShell команда
            timeout: Таймаут выполнения
            
        Returns:
            Словарь с результатами выполнения
        """
        try:
            result = subprocess.run([
                "powershell.exe", "-Command", command
            ], capture_output=True, text=True, timeout=timeout, check=True)
            
            return {
                "success": True,
                "output": result.stdout.strip(),
                "error": None
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": None,
                "error": "Command timed out"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": e.stdout,
                "error": e.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "output": None,
                "error": str(e)
            }
    
    def get_network_connections(self) -> List[NetworkConnection]:
        """
        Получение списка всех сетевых подключений
        
        Returns:
            Список объектов NetworkConnection
        """
        connections = []
        
        try:
            with self._safe_com_context() as net_share:
                for connection in net_share.EnumEveryConnection:
                    try:
                        props = net_share.NetConnectionProps(connection)
                        config = net_share.INetSharingConfigurationForINetConnection(connection)
                        
                        conn_obj = NetworkConnection(
                            name=props.Name,
                            guid=props.Guid,
                            device_name=props.DeviceName,
                            status=props.Status,
                            media_type=props.MediaType,
                            sharing_enabled=config.SharingEnabled,
                            sharing_type=config.SharingType if config.SharingEnabled else None
                        )
                        
                        connections.append(conn_obj)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get connection info: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to enumerate connections: {e}")
            raise NetworkAdapterError(f"Cannot enumerate connections: {e}")
        
        return connections
    
    def find_connection_by_name(self, name: str) -> Optional[NetworkConnection]:
        """
        Поиск подключения по имени
        
        Args:
            name: Имя подключения
            
        Returns:
            Объект NetworkConnection или None
        """
        connections = self.get_network_connections()
        for conn in connections:
            if conn.name == name:
                return conn
        return None
    
    def is_sharing_installed(self) -> bool:
        """
        Проверка, поддерживает ли система ICS
        
        Returns:
            True если ICS поддерживается
        """
        try:
            with self._safe_com_context() as net_share:
                return net_share.SharingInstalled
        except Exception as e:
            logger.error(f"Failed to check ICS support: {e}")
            return False
    
    def enable_ics_com(self, public_connection_name: str, 
                      private_connection_name: str = None) -> bool:
        """
        Включение ICS через COM интерфейс
        
        Args:
            public_connection_name: Имя публичного подключения
            private_connection_name: Имя приватного подключения (опционально)
            
        Returns:
            True если операция успешна
        """
        try:
            with self._safe_com_context() as net_share:
                # Сначала отключаем все существующие подключения
                self._disable_all_sharing_com()
                
                # Настройка публичного подключения
                for connection in net_share.EnumEveryConnection:
                    props = net_share.NetConnectionProps(connection)
                    config = net_share.INetSharingConfigurationForINetConnection(connection)
                    
                    if props.Name == public_connection_name:
                        config.EnableSharing(0)  # 0 = публичное подключение
                        logger.info(f"Enabled public sharing for: {public_connection_name}")
                        
                    elif private_connection_name and props.Name == private_connection_name:
                        config.EnableSharing(1)  # 1 = приватное подключение
                        logger.info(f"Enabled private sharing for: {private_connection_name}")
                
                # Запуск службы SharedAccess
                self._ensure_shared_access_service()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to enable ICS via COM: {e}")
            raise ServiceError(f"ICS enable failed: {e}")
    
    def enable_ics_powershell(self, public_connection_name: str,
                             private_connection_name: str = None) -> bool:
        """
        Включение ICS через PowerShell
        
        Args:
            public_connection_name: Имя публичного подключения
            private_connection_name: Имя приватного подключения (опционально)
            
        Returns:
            True если операция успешна
        """
        try:
            if self._ps_module_available:
                # Использование модуля PSInternetConnectionSharing
                if private_connection_name:
                    command = f"Set-Ics -PublicConnectionName '{public_connection_name}' -PrivateConnectionName '{private_connection_name}'"
                else:
                    command = f"Set-Ics -PublicConnectionName '{public_connection_name}'"
            else:
                # Fallback к COM через PowerShell
                command = f"""
                $netShare = New-Object -ComObject HNetCfg.HNetShare
                $connections = $netShare.EnumEveryConnection
                
                foreach ($conn in $connections) {{
                    $props = $netShare.NetConnectionProps.Invoke($conn)
                    $config = $netShare.INetSharingConfigurationForINetConnection.Invoke($conn)
                    
                    if ($props.Name -eq '{public_connection_name}') {{
                        $config.EnableSharing(0)
                        Write-Host "Enabled public sharing for: $($props.Name)"
                    }}
                    {f'''
                    elseif ($props.Name -eq '{private_connection_name}') {{
                        $config.EnableSharing(1)
                        Write-Host "Enabled private sharing for: $($props.Name)"
                    }}
                    ''' if private_connection_name else ''}
                }}
                
                Start-Service SharedAccess -ErrorAction SilentlyContinue
                """
            
            result = self._run_powershell_command(command)
            
            if result["success"]:
                logger.info("ICS enabled successfully via PowerShell")
                return True
            else:
                logger.error(f"PowerShell ICS enable failed: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to enable ICS via PowerShell: {e}")
            raise ServiceError(f"PowerShell ICS enable failed: {e}")
    
    def disable_ics_com(self) -> bool:
        """
        Отключение ICS через COM интерфейс
        
        Returns:
            True если операция успешна
        """
        try:
            return self._disable_all_sharing_com()
        except Exception as e:
            logger.error(f"Failed to disable ICS via COM: {e}")
            raise ServiceError(f"ICS disable failed: {e}")
    
    def disable_ics_powershell(self) -> bool:
        """
        Отключение ICS через PowerShell
        
        Returns:
            True если операция успешна
        """
        try:
            if self._ps_module_available:
                command = "Disable-Ics"
            else:
                command = """
                $netShare = New-Object -ComObject HNetCfg.HNetShare
                $connections = $netShare.EnumEveryConnection
                
                foreach ($conn in $connections) {
                    $config = $netShare.INetSharingConfigurationForINetConnection.Invoke($conn)
                    if ($config.SharingEnabled) {
                        $config.DisableSharing()
                        Write-Host "Disabled sharing for connection"
                    }
                }
                """
            
            result = self._run_powershell_command(command)
            
            if result["success"]:
                logger.info("ICS disabled successfully via PowerShell")
                return True
            else:
                logger.error(f"PowerShell ICS disable failed: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to disable ICS via PowerShell: {e}")
            raise ServiceError(f"PowerShell ICS disable failed: {e}")
    
    def _disable_all_sharing_com(self) -> bool:
        """Отключение всех ICS подключений через COM"""
        try:
            with self._safe_com_context() as net_share:
                for connection in net_share.EnumEveryConnection:
                    try:
                        config = net_share.INetSharingConfigurationForINetConnection(connection)
                        if config.SharingEnabled:
                            config.DisableSharing()
                    except Exception as e:
                        logger.warning(f"Failed to disable sharing for connection: {e}")
                        continue
                
                logger.info("All ICS connections disabled")
                return True
                
        except Exception as e:
            logger.error(f"Failed to disable all ICS connections: {e}")
            return False
    
    def _ensure_shared_access_service(self):
        """Обеспечение запуска службы SharedAccess"""
        try:
            # Проверка статуса службы
            service_status = self.get_shared_access_service_status()
            
            if service_status and service_status.get('state') != 'Running':
                # Запуск службы
                subprocess.run(['net', 'start', 'SharedAccess'], 
                             check=True, capture_output=True)
                logger.info("SharedAccess service started")
                
                # Настройка автозапуска
                subprocess.run(['sc', 'config', 'SharedAccess', 'start=', 'auto'], 
                             check=True, capture_output=True)
                
        except Exception as e:
            logger.warning(f"Failed to manage SharedAccess service: {e}")
    
    def get_shared_access_service_status(self) -> Optional[Dict]:
        """
        Получение статуса службы SharedAccess
        
        Returns:
            Словарь с информацией о службе
        """
        try:
            services = self._wmi_connection.Win32_Service(Name="SharedAccess")
            for service in services:
                return {
                    'name': service.Name,
                    'state': service.State,
                    'start_mode': service.StartMode,
                    'status': service.Status
                }
        except Exception as e:
            logger.error(f"Failed to get SharedAccess service status: {e}")
            return None
    
    def get_ics_status(self) -> Dict:
        """
        Получение полного статуса ICS
        
        Returns:
            Словарь с информацией о статусе ICS
        """
        status = {
            'sharing_installed': self.is_sharing_installed(),
            'service_status': self.get_shared_access_service_status(),
            'active_connections': [],
            'method_availability': {
                'com': self._net_share is not None,
                'powershell_module': self._ps_module_available,
                'wmi': self._wmi_connection is not None
            }
        }
        
        # Получение активных подключений с ICS
        connections = self.get_network_connections()
        for conn in connections:
            if conn.sharing_enabled:
                status['active_connections'].append({
                    'name': conn.name,
                    'type': 'Public' if conn.sharing_type == 0 else 'Private',
                    'guid': conn.guid
                })
        
        return status
    
    def create_virtual_adapter(self, adapter_name: str = "RndisAdapter") -> bool:
        """
        Создание виртуального сетевого адаптера
        
        Args:
            adapter_name: Имя адаптера
            
        Returns:
            True если адаптер создан успешно
        """
        try:
            # Попытка создания Microsoft KM-TEST Loopback Adapter
            command = f"""
            $devcon = Get-Command devcon -ErrorAction SilentlyContinue
            if ($devcon) {{
                devcon install $env:windir\\inf\\netloop.inf *MSLOOP
            }} else {{
                pnputil /add-driver $env:windir\\inf\\netloop.inf /install
            }}
            """
            
            result = self._run_powershell_command(command)
            
            if result["success"]:
                logger.info(f"Virtual adapter '{adapter_name}' created successfully")
                return True
            else:
                logger.error(f"Failed to create virtual adapter: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create virtual adapter: {e}")
            return False
    
    def configure_virtual_adapter(self, adapter_name: str, 
                                 ip_address: str = "192.168.137.1",
                                 subnet_mask: str = "255.255.255.0") -> bool:
        """
        Конфигурация виртуального адаптера
        
        Args:
            adapter_name: Имя адаптера
            ip_address: IP адрес
            subnet_mask: Маска подсети
            
        Returns:
            True если конфигурация успешна
        """
        try:
            command = f"""
            netsh interface ip set address name="{adapter_name}" static {ip_address} {subnet_mask}
            netsh interface ip set dns name="{adapter_name}" static 8.8.8.8
            """
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Virtual adapter '{adapter_name}' configured with IP {ip_address}")
                return True
            else:
                logger.error(f"Failed to configure adapter: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to configure virtual adapter: {e}")
            return False
    
    def enable_ics(self, public_connection_name: str,
                   private_connection_name: str = None) -> bool:
        """
        Универсальный метод включения ICS
        
        Args:
            public_connection_name: Имя публичного подключения
            private_connection_name: Имя приватного подключения (опционально)
            
        Returns:
            True если операция успешна
        """
        if self.prefer_powershell:
            try:
                return self.enable_ics_powershell(public_connection_name, private_connection_name)
            except Exception as e:
                logger.warning(f"PowerShell method failed, trying COM: {e}")
                return self.enable_ics_com(public_connection_name, private_connection_name)
        else:
            try:
                return self.enable_ics_com(public_connection_name, private_connection_name)
            except Exception as e:
                logger.warning(f"COM method failed, trying PowerShell: {e}")
                return self.enable_ics_powershell(public_connection_name, private_connection_name)
    
    def disable_ics(self) -> bool:
        """
        Универсальный метод отключения ICS
        
        Returns:
            True если операция успешна
        """
        if self.prefer_powershell:
            try:
                return self.disable_ics_powershell()
            except Exception as e:
                logger.warning(f"PowerShell method failed, trying COM: {e}")
                return self.disable_ics_com()
        else:
            try:
                return self.disable_ics_com()
            except Exception as e:
                logger.warning(f"COM method failed, trying PowerShell: {e}")
                return self.disable_ics_powershell()
    
    def __del__(self):
        """Деструктор для очистки ресурсов"""
        try:
            pythoncom.CoUninitialize()
        except:
            pass

# Функция для проверки и получения прав администратора
def ensure_admin_rights():
    """Проверка и получение прав администратора"""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        # Перезапуск с правами администратора
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return False
    return True

# Пример использования
if __name__ == "__main__":
    # Проверка прав администратора
    if not ensure_admin_rights():
        print("Перезапуск с правами администратора...")
        sys.exit(0)
    
    try:
        # Создание менеджера ICS
        ics_manager = RndisManager(prefer_powershell=True)
        
        # Получение списка сетевых подключений
        connections = ics_manager.get_network_connections()
        print("Доступные сетевые подключения:")
        for conn in connections:
            print(f"  - {conn.name} (ICS: {conn.sharing_enabled})")
        
        # Проверка статуса ICS
        status = ics_manager.get_ics_status()
        print(f"\nСтатус ICS: {status}")
        
        # Включение ICS (пример)
        public_conn = "Wi-Fi"  # Замените на ваше подключение
        private_conn = "Ethernet"  # Замените на ваше подключение
        
        if ics_manager.enable_ics(public_conn, private_conn):
            print(f"ICS включен: {public_conn} -> {private_conn}")
        else:
            print("Не удалось включить ICS")
        
        # Ожидание
        time.sleep(2)
        
        # Отключение ICS
        if ics_manager.disable_ics():
            print("ICS отключен")
        else:
            print("Не удалось отключить ICS")
            
    except InsufficientPrivilegesError:
        print("Ошибка: Требуются права администратора")
    except NetworkAdapterError as e:
        print(f"Ошибка сетевого адаптера: {e}")
    except ServiceError as e:
        print(f"Ошибка службы: {e}")
    except IcsError as e:
        print(f"Ошибка ICS: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")