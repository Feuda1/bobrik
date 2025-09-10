import subprocess
import sys
import time
import threading
from PyQt6.QtCore import QThread, pyqtSignal

from config import TOUCHSCREEN_KEYWORDS


class TouchscreenManager(QThread):
    log_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(bool)  # True = disabled

    def __init__(self):
        super().__init__()
        self.is_disabled = False
        self.device_ids = []

    def run(self):
        pass

    # Discovery
    def find_touchscreen_devices(self):
        try:
            if sys.platform != 'win32':
                self.log_signal.emit('Доступно только на Windows', 'error')
                return
            result = subprocess.run(['pnputil', '/enum-devices', '/connected'], capture_output=True, text=True)
            output = result.stdout or ''
            self.device_ids = []
            desc = ''
            inst = ''
            for raw in output.splitlines():
                line = raw.strip()
                if not line:
                    if desc and inst and any(k in desc.lower() for k in TOUCHSCREEN_KEYWORDS):
                        self.device_ids.append(inst)
                        self.log_signal.emit(f'Найдено устройство: {desc} [{inst}]', 'info')
                    desc = ''
                    inst = ''
                    continue
                low = line.lower()
                if low.startswith('device description') or low.startswith('описание устройства'):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        desc = parts[1].strip()
                elif low.startswith('instance id') or low.startswith('идентификатор экземпляра'):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        inst = parts[1].strip()
            if desc and inst and any(k in desc.lower() for k in TOUCHSCREEN_KEYWORDS):
                self.device_ids.append(inst)
                self.log_signal.emit(f'Найдено устройство: {desc} [{inst}]', 'info')
            if not self.device_ids:
                self.log_signal.emit('Тач-устройства не найдены', 'warning')
            else:
                self.log_signal.emit(f'Найдено устройств: {len(self.device_ids)}', 'success')
        except Exception as e:
            self.log_signal.emit(f'Ошибка поиска тач-устройств: {e}', 'error')

    # Toggle
    def toggle_touchscreen(self):
        if not self.device_ids:
            self.log_signal.emit('Ищу тач-устройства...', 'info')
            self.find_touchscreen_devices()
        if not self.device_ids:
            self.log_signal.emit('Нет устройств для операции', 'error')
            return
        if self.is_disabled:
            self.enable_touchscreen()
        else:
            self.disable_touchscreen()

    def _exec_pnputil(self, args):
        return subprocess.run(args, capture_output=True, text=True)

    def disable_touchscreen(self):
        try:
            ok = 0
            for dev in self.device_ids:
                r = self._exec_pnputil(['pnputil', '/disable-device', dev])
                if r.returncode == 0:
                    ok += 1
            if ok:
                self.is_disabled = True
                self.status_signal.emit(True)
                self.log_signal.emit(f'Отключено устройств: {ok}', 'success')
            else:
                self.log_signal.emit('Не удалось отключить устройства (возможны ограничения)', 'error')
        except Exception as e:
            self.log_signal.emit(f'Ошибка отключения: {e}', 'error')

    def enable_touchscreen(self):
        try:
            ok = 0
            for dev in self.device_ids:
                r = self._exec_pnputil(['pnputil', '/enable-device', dev])
                if r.returncode == 0:
                    ok += 1
            if ok:
                self.is_disabled = False
                self.status_signal.emit(False)
                self.log_signal.emit(f'Включено устройств: {ok}', 'success')
            else:
                self.log_signal.emit('Не удалось включить устройства', 'error')
        except Exception as e:
            self.log_signal.emit(f'Ошибка включения: {e}', 'error')

    def reboot_touchscreen(self):
        try:
            if not self.device_ids:
                self.log_signal.emit('Ищу тач-устройства...', 'info')
                self.find_touchscreen_devices()
            if not self.device_ids:
                self.log_signal.emit('Нет устройств для перезапуска', 'error')
                return
            was_disabled = self.is_disabled
            disabled = 0
            for dev in self.device_ids:
                if self._exec_pnputil(['pnputil', '/disable-device', dev]).returncode == 0:
                    disabled += 1
            self.log_signal.emit(f'Отключено: {disabled}', 'info')
            time.sleep(2)
            enabled = 0
            for dev in self.device_ids:
                if self._exec_pnputil(['pnputil', '/enable-device', dev]).returncode == 0:
                    enabled += 1
            self.log_signal.emit(f'Включено: {enabled}', 'info')
            self.is_disabled = was_disabled
            self.status_signal.emit(self.is_disabled)
            self.log_signal.emit('Перезапуск сенсора завершен', 'success')
        except Exception as e:
            self.log_signal.emit(f'Ошибка перезапуска: {e}', 'error')

