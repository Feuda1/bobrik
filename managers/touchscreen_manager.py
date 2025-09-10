import subprocess
import sys
import time
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from config import TOUCHSCREEN_KEYWORDS

class TouchscreenManager(QThread):
    log_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.is_disabled = False
        self.device_ids = []
        
    def run(self):
        pass
        
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
        """Перезапускает сенсорный экран с выбором калибровки"""
        try:
            if not self.device_ids:
                self.log_signal.emit("Поиск сенсорных устройств...", "info")
                self.find_touchscreen_devices()
                
            if not self.device_ids:
                self.log_signal.emit("Сенсорные устройства не найдены для перезапуска", "error")
                return
                
            # Показываем диалог выбора
            msg = QMessageBox()
            msg.setWindowTitle('Перезапуск сенсорного экрана')
            msg.setText('Выберите действие:')
            msg.setIcon(QMessageBox.Icon.Question)
            
            reboot_button = msg.addButton('🔄 Только перезапуск', QMessageBox.ButtonRole.YesRole)
            calibrate_button = msg.addButton('🎯 Перезапуск + калибровка', QMessageBox.ButtonRole.ActionRole)
            cancel_button = msg.addButton('❌ Отмена', QMessageBox.ButtonRole.RejectRole)
            
            msg.setDefaultButton(reboot_button)
            msg.exec()
            
            if msg.clickedButton() == cancel_button:
                self.log_signal.emit("Перезапуск сенсорного экрана отменен", "info")
                return
            elif msg.clickedButton() == calibrate_button:
                self.log_signal.emit("Начинаем перезапуск с калибровкой...", "info")
                threading.Thread(target=self._reboot_with_calibration, daemon=True).start()
            else:
                self.log_signal.emit("Начинаем обычный перезапуск сенсорного экрана...", "info")
                threading.Thread(target=self._reboot_only, daemon=True).start()
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при перезапуске сенсорного экрана: {str(e)}", "error")
            
    def _reboot_only(self):
        """Обычный перезапуск без калибровки"""
        try:
            was_disabled = self.is_disabled
            
            self.log_signal.emit("Отключаем сенсорные устройства...", "info")
            disabled_count = 0
            
            for device_id in self.device_ids:
                try:
                    cmd = f'pnputil /disable-device "{device_id}"'
                    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, 
                                          encoding='utf-8', errors='ignore', 
                                          creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        disabled_count += 1
                except:
                    continue
                    
            if disabled_count > 0:
                self.log_signal.emit(f"Отключено {disabled_count} сенсорных устройств", "info")
            else:
                self.log_signal.emit("Не удалось отключить устройства", "warning")
                return
                
            self.log_signal.emit("Ожидание 3 секунды...", "info")
            time.sleep(3)
            
            self.log_signal.emit("Включаем сенсорные устройства...", "info")
            enabled_count = 0
            
            for device_id in self.device_ids:
                try:
                    cmd = f'pnputil /enable-device "{device_id}"'
                    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, 
                                          encoding='utf-8', errors='ignore',
                                          creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        enabled_count += 1
                except:
                    continue
                    
            if enabled_count > 0:
                if was_disabled:
                    self.is_disabled = True
                    self.status_signal.emit(True)
                else:
                    self.is_disabled = False
                    self.status_signal.emit(False)
                    
                self.log_signal.emit(f"Включено {enabled_count} сенсорных устройств", "info")
                self.log_signal.emit("Перезапуск сенсорного экрана завершен", "success")
                self.show_desktop_notification_reboot()
            else:
                self.log_signal.emit("Не удалось включить устройства", "error")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при перезапуске: {str(e)}", "error")
    
    def _reboot_with_calibration(self):
        """Перезапуск с калибровкой"""
        try:
            # Сначала делаем обычный перезапуск
            self._reboot_only()
            
            # Ждем 2 секунды
            time.sleep(2)
            
            # Запускаем калибровку
            self.log_signal.emit("Запуск калибровки сенсорного экрана...", "info")
            self._open_calibration()
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при перезапуске с калибровкой: {str(e)}", "error")
    
    def _open_calibration(self):
        """Открывает калибровку сенсорного экрана"""
        try:
            if sys.platform != "win32":
                self.log_signal.emit("Калибровка доступна только в Windows", "error")
                return
            
            calibration_opened = False
            
            # Метод 1: tabcal.exe - стандартная калибровка Windows
            try:
                subprocess.Popen(['tabcal.exe'], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
                self.log_signal.emit("Запущена стандартная калибровка Windows", "success")
                calibration_opened = True
            except FileNotFoundError:
                pass
            except Exception:
                pass
            
            # Метод 2: Настройки планшетного ПК
            if not calibration_opened:
                try:
                    subprocess.Popen(['control', 'tabletpc.cpl'], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    self.log_signal.emit("Открыты настройки планшетного ПК", "success")
                    self.log_signal.emit("Выберите вкладку 'Калибровка'", "info")
                    calibration_opened = True
                except Exception:
                    pass
            
            # Метод 3: Настройки пера Windows
            if not calibration_opened:
                try:
                    subprocess.Popen(['ms-settings:pen'], 
                                   creationflags=subprocess.CREATE_NO_WINDOW, shell=True)
                    self.log_signal.emit("Открыты настройки пера Windows", "success")
                    calibration_opened = True
                except Exception:
                    pass
            
            # Метод 4: Диспетчер устройств
            if not calibration_opened:
                try:
                    subprocess.Popen(['devmgmt.msc'], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    self.log_signal.emit("Открыт диспетчер устройств", "info")
                    self.log_signal.emit("Найдите устройства HID для настройки", "info")
                    calibration_opened = True
                except Exception:
                    pass
            
            if calibration_opened:
                self.log_signal.emit("💡 Для точной калибровки используйте стилус", "info")
                self.log_signal.emit("🎯 Нажимайте точно в центр целей", "info")
            else:
                self.log_signal.emit("❌ Не удалось открыть калибровку", "error")
                self.log_signal.emit("💡 Найдите 'Калибровка' в настройках Windows", "info")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка калибровки: {str(e)}", "error")
            
    def show_desktop_notification(self, is_disabled):
        """Показывает уведомление о включении/отключении"""
        try:
            if is_disabled:
                subprocess.Popen(['msg', '*', '/TIME:3', 'Сенсорный экран ОТКЛЮЧЕН'], 
                               shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(['msg', '*', '/TIME:3', 'Сенсорный экран ВКЛЮЧЕН'], 
                               shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
            
    def show_desktop_notification_reboot(self):
        """Показывает уведомление о перезапуске"""
        try:
            subprocess.Popen(['msg', '*', '/TIME:4', 'Сенсорный экран ПЕРЕЗАПУЩЕН'], 
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass