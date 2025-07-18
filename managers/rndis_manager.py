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
        self.saved_private_connection = None  # Запоминаем выбранную приватную сеть
        
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
            # Сначала сохраняем текущие настройки
            self.log_signal.emit("Сохраняем текущие настройки сети...", "info")
            self._save_current_sharing_settings()
            
            # Включаем
            self.log_signal.emit("Включаем общий доступ к интернету...", "info")
            self._enable_sharing_quick()
            
            # Ждем 3 секунды
            time.sleep(3)
            
            # Выключаем
            self.log_signal.emit("Выключаем общий доступ к интернету...", "warning")
            self._disable_sharing_quick()
            
            # Ждем 2 секунды
            time.sleep(2)
            
            # Снова включаем с восстановлением настроек
            self.log_signal.emit("Снова включаем общий доступ к интернету...", "info")
            self._enable_sharing_with_restore()
            
            self.log_signal.emit("Переключение общего доступа завершено", "success")
            self.log_signal.emit("RNDIS перезагружен", "success")
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {str(e)}", "error")
    
    def _enable_sharing_quick(self):
        """Быстрое включение общего доступа"""
        try:
            commands = [
                ['sc', 'config', 'SharedAccess', 'start=auto'],
                ['net', 'start', 'SharedAccess'],
                ['powershell', '-Command', '''
                $regPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters"
                Set-ItemProperty -Path $regPath -Name "EnableRebootPersistConnection" -Value 1 -ErrorAction SilentlyContinue
                Start-Service -Name "SharedAccess" -ErrorAction SilentlyContinue
                '''],
                ['netsh', 'interface', 'ipv4', 'set', 'global', 'forwarding=enabled']
            ]
            
            success_count = 0
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        success_count += 1
                except Exception:
                    pass
            
            # Дополнительно через COM если возможно
            try:
                self._enable_com_sharing()
            except:
                pass
                
            if success_count >= 2:
                self.log_signal.emit("Общий доступ включен", "success")
            else:
                self.log_signal.emit("Частично включен", "warning")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка включения: {str(e)}", "error")
    
    def _disable_sharing_quick(self):
        """Быстрое выключение общего доступа"""
        try:
            commands = [
                ['net', 'stop', 'SharedAccess'],
                ['sc', 'config', 'SharedAccess', 'start=demand'],
                ['powershell', '-Command', '''
                $regPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters"
                Set-ItemProperty -Path $regPath -Name "EnableRebootPersistConnection" -Value 0 -ErrorAction SilentlyContinue
                Stop-Service -Name "SharedAccess" -Force -ErrorAction SilentlyContinue
                '''],
                ['netsh', 'interface', 'ipv4', 'set', 'global', 'forwarding=disabled']
            ]
            
            success_count = 0
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        success_count += 1
                except Exception:
                    pass
            
            # Дополнительно через COM если возможно
            try:
                self._disable_com_sharing()
            except:
                pass
                
            if success_count >= 2:
                self.log_signal.emit("Общий доступ выключен", "success")
            else:
                self.log_signal.emit("Частично выключен", "warning")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка выключения: {str(e)}", "error")
    
    def _enable_com_sharing(self):
        """Включение через COM если доступно"""
        try:
            import win32com.client
            import pythoncom
            
            pythoncom.CoInitialize()
            net_share = win32com.client.Dispatch("HNetCfg.HNetShare")
            
            for connection in net_share.EnumEveryConnection:
                try:
                    props = net_share.NetConnectionProps(connection)
                    config = net_share.INetSharingConfigurationForINetConnection(connection)
                    
                    if 'ethernet' in props.Name.lower():
                        if not config.SharingEnabled:
                            config.EnableSharing(0)
                            break
                except:
                    continue
                    
            pythoncom.CoUninitialize()
            
        except:
            pass
    
    def _disable_com_sharing(self):
        """Выключение через COM если доступно"""
        try:
            import win32com.client
            import pythoncom
            
            pythoncom.CoInitialize()
            net_share = win32com.client.Dispatch("HNetCfg.HNetShare")
            
            for connection in net_share.EnumEveryConnection:
                try:
                    config = net_share.INetSharingConfigurationForINetConnection(connection)
                    if config.SharingEnabled:
                        config.DisableSharing()
                except:
                    continue
                    
            pythoncom.CoUninitialize()
            
        except:
            pass
    
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
                        
                        # Если найдено активное подключение с sharing
                        if config.SharingEnabled:
                            if config.SharingType == 1:  # 1 = приватное подключение (домашняя сеть)
                                self.saved_private_connection = props.Name
                                self.log_signal.emit(f"Сохранена приватная сеть: {props.Name}", "info")
                                break
                    except:
                        continue
                        
                pythoncom.CoUninitialize()
                
            except Exception:
                # Метод 2: Через реестр
                try:
                    result = subprocess.run([
                        'reg', 'query', 
                        'HKLM\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\Connections',
                        '/s'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        # Ищем записи о приватных подключениях
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if 'IsPrivate' in line and 'REG_DWORD' in line and '0x1' in line:
                                # Найдена приватная сеть в реестре
                                self.log_signal.emit("Найдена приватная сеть в реестре", "info")
                                break
                except Exception:
                    pass
            
            # Метод 3: Через PowerShell как резерв
            if not self.saved_private_connection:
                try:
                    ps_command = """
                    Get-NetConnectionProfile | Where-Object {$_.NetworkCategory -eq 'Private'} | 
                    Select-Object -First 1 -ExpandProperty InterfaceAlias
                    """
                    
                    result = subprocess.run([
                        'powershell', '-Command', ps_command
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        self.saved_private_connection = result.stdout.strip()
                        self.log_signal.emit(f"Найдена приватная сеть: {self.saved_private_connection}", "info")
                except Exception:
                    pass
                    
        except Exception as e:
            self.log_signal.emit(f"Ошибка сохранения настроек: {str(e)}", "warning")
    
    def _enable_sharing_with_restore(self):
        """Включает общий доступ с восстановлением сохраненных настроек"""
        try:
            # Сначала включаем базовый sharing
            self._enable_sharing_quick()
            
            # Затем восстанавливаем приватное подключение если оно было сохранено
            if self.saved_private_connection:
                time.sleep(1)  # Небольшая пауза
                self.log_signal.emit(f"Восстанавливаем приватную сеть: {self.saved_private_connection}", "info")
                self._restore_private_connection()
            else:
                self.log_signal.emit("Приватная сеть не была сохранена", "warning")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка восстановления: {str(e)}", "error")
    
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
                    except:
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
                    ], capture_output=True, text=True, timeout=15)
                    
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
            ], capture_output=True, text=True, shell=True, encoding='cp866', errors='ignore')
            
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
                                 capture_output=True, shell=True)
                
                time.sleep(2)
                
                # Включаем
                for device_id in device_ids:
                    subprocess.run(f'pnputil /enable-device "{device_id}"', 
                                 capture_output=True, shell=True)
                
                self.log_signal.emit("RNDIS устройства перезапущены", "success")
            else:
                self.log_signal.emit("RNDIS устройства не найдены", "warning")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка перезапуска RNDIS: {str(e)}", "error")