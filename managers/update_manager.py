import os
import sys
import json
import tempfile
import threading
import subprocess
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMessageBox

try:
    import requests  # type: ignore
except Exception:
    requests = None  # graceful fallback below


class SimpleUpdateManager(QThread):
    """Управляет проверкой обновлений и установкой новой версии.

    Публичный интерфейс (используется из UI):
      - log_signal(str message, str level)
      - set_github_repo(str repo)
      - check_for_updates()
    """

    log_signal = pyqtSignal(str, str)
    # внутренние сигналы остаются для работы в главном потоке
    update_available_signal = pyqtSignal(str, str, str)  # version, notes, download_url
    show_confirmation_signal = pyqtSignal(str, str)      # script_path, new_exe_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.github_repo = "Feuda1/bobrik"
        self.version_url = f"https://raw.githubusercontent.com/{self.github_repo}/main/version.json"
        self.exe_url = f"https://github.com/{self.github_repo}/releases/latest/download/bobrik.exe"
        self.current_version = self._load_current_version(default="1.1.4")

        # показать диалоги в UI-потоке
        self.update_available_signal.connect(self._show_update_dialog_in_main_thread)
        self.show_confirmation_signal.connect(self._show_confirmation_dialog)

    def run(self):
        # QThread не используется как поток исполнения; нужен для сигналов
        pass

    # ---- Публичные методы

    def set_github_repo(self, repo_path: str):
        self.github_repo = repo_path
        self.version_url = f"https://raw.githubusercontent.com/{repo_path}/main/version.json"
        self.exe_url = f"https://github.com/{repo_path}/releases/latest/download/bobrik.exe"

    def check_for_updates(self):
        try:
            if not requests:
                self.log_signal.emit("Нет библиотеки requests — проверка обновлений недоступна", "error")
                return

            self.log_signal.emit("Проверяю обновления...", "info")
            threading.Thread(target=self._check_updates_async, daemon=True).start()
        except Exception as e:
            self.log_signal.emit(f"Ошибка при запуске проверки обновлений: {e}", "error")

    # ---- Внутренние методы

    def _load_current_version(self, default: str) -> str:
        try:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, 'version.json')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return str(json.load(f).get('version') or '').strip() or default
        except Exception:
            pass
        return default

    def _check_updates_async(self):
        try:
            headers = {
                'User-Agent': 'bobrik-updater/1.0',
                'Cache-Control': 'no-cache',
            }
            resp = requests.get(self.version_url, headers=headers, timeout=10)  # type: ignore
            resp.raise_for_status()
            data = resp.json()

            latest_version = str(data.get('version') or '').strip()
            release_notes = str(data.get('notes') or '').strip()
            download_url = str(data.get('download_url') or self.exe_url)

            if self._is_newer_version(latest_version, self.current_version):
                self.log_signal.emit(f"Доступна новая версия: {latest_version}", "success")
                self.update_available_signal.emit(latest_version, release_notes, download_url)
            else:
                self.log_signal.emit("Обновлений не найдено", "success")
        except Exception as e:
            self.log_signal.emit(f"Сбой проверки обновлений: {e}", "error")

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Сравнение семверсий: возвращает True, если latest > current."""
        try:
            def parse(v: str):
                parts = []
                for p in (v or "").split('.'):
                    num = "".join(ch for ch in p if ch.isdigit())
                    parts.append(int(num) if num else 0)
                return parts

            l = parse(latest)
            c = parse(current)
            m = max(len(l), len(c))
            l += [0] * (m - len(l))
            c += [0] * (m - len(c))
            return l > c
        except Exception:
            return False

    # ---- UI диалоги (в главном потоке)

    def _show_update_dialog_in_main_thread(self, version: str, notes: str, download_url: str):
        try:
            if not self.parent:
                return

            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Доступно обновление bobrik')

            text = f'Найдена новая версия {version}.\n\n'
            if notes:
                short = notes[:300] + '...' if len(notes) > 300 else notes
                text += f'Кратко о выпуске:\n{short}\n\n'
            text += 'Установить обновление сейчас?'

            msg.setText(text)
            msg.setIcon(QMessageBox.Icon.Information)

            btn_update = msg.addButton('Установить', QMessageBox.ButtonRole.YesRole)
            msg.addButton('Позже', QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(btn_update)

            msg.exec()
            if msg.clickedButton() is btn_update:
                self.log_signal.emit("Скачиваю обновление...", "info")
                threading.Thread(
                    target=self._download_and_install_update,
                    args=(download_url, version),
                    daemon=True,
                ).start()
            else:
                self.log_signal.emit("Обновление отложено пользователем", "info")
        except Exception as e:
            self.log_signal.emit(f"Ошибка показа диалога обновления: {e}", "error")

    def _download_and_install_update(self, download_url: str, version: str):
        try:
            temp_dir = tempfile.gettempdir()
            new_exe_path = os.path.join(temp_dir, f"bobrik_{version}.exe")

            headers = {'User-Agent': 'bobrik-updater/1.0'}
            resp = requests.get(download_url, stream=True, headers=headers, timeout=60)  # type: ignore
            resp.raise_for_status()

            total = int(resp.headers.get('content-length', 0))
            downloaded = 0
            last_progress = 0
            with open(new_exe_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        progress = int((downloaded / total) * 100)
                        if progress >= last_progress + 20:
                            self.log_signal.emit(f"Прогресс загрузки: {progress}%", "info")
                            last_progress = progress

            size_mb = os.path.getsize(new_exe_path) / (1024 * 1024)
            if size_mb < 5:  # тривиальная валидация
                self.log_signal.emit("Размер загруженного файла подозрительно мал — отмена", "error")
                return

            self.log_signal.emit(f"Загрузка завершена ({size_mb:.1f} МБ)", "success")
            self._create_update_script(new_exe_path)
        except Exception as e:
            self.log_signal.emit(f"Ошибка загрузки обновления: {e}", "error")

    def _create_update_script(self, new_exe_path: str):
        try:
            # В режиме исходников — просто запустим скачанный .exe (инсталлятор)
            if not getattr(sys, 'frozen', False):
                self.log_signal.emit(
                    "Обновление приложения поддерживается только для собранного exe. Запускаю скачанный файл...",
                    "warning",
                )
                try:
                    os.startfile(new_exe_path)  # type: ignore[attr-defined]
                except Exception:
                    subprocess.Popen([new_exe_path], shell=True)
                return

            current_exe = sys.executable
            temp_dir = tempfile.gettempdir()
            script_path = os.path.join(temp_dir, "bobrik_update.bat")

            script_content = f"""@echo off
echo Obnovlenie bobrik...
timeout /t 2 /nobreak > nul

echo Sozdanie rezervnoy kopii...
if exist "{current_exe}.backup" del /q "{current_exe}.backup" 2>nul
ren "{current_exe}" "{os.path.basename(current_exe)}.backup" 2>nul

echo Ustanovka novoy versii...
copy /y "{new_exe_path}" "{current_exe}" 2>nul

if exist "{current_exe}" (
  echo Zapusk obnovlennoy versii...
  start "" "{current_exe}"
  timeout /t 2 /nobreak > nul
  del /q "{new_exe_path}" 2>nul
  echo Obnovlenie zaversheno uspeshno
) else (
  echo Oshibka obnovleniya, vosstanovlenie rezervnoy kopii...
  ren "{os.path.basename(current_exe)}.backup" "{os.path.basename(current_exe)}" 2>nul
)

del /q "%~f0" 2>nul
"""

            with open(script_path, 'w', encoding='ascii', errors='ignore') as f:
                f.write(script_content)

            # Подтверждение перед установкой
            self.show_confirmation_signal.emit(script_path, new_exe_path)
        except Exception as e:
            self.log_signal.emit(f"Ошибка подготовки обновления: {e}", "error")

    def _show_confirmation_dialog(self, script_path: str, new_exe_path: str):
        try:
            if not self.parent:
                self.log_signal.emit("Нет родительского окна для диалога подтверждения", "error")
                return

            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Подтверждение установки')
            msg.setText('Готово к установке обновления bobrik. Продолжить сейчас?')
            msg.setIcon(QMessageBox.Icon.Question)

            btn_yes = msg.addButton('Установить', QMessageBox.ButtonRole.YesRole)
            msg.addButton('Отмена', QMessageBox.ButtonRole.NoRole)

            msg.exec()
            if msg.clickedButton() is btn_yes:
                self._start_update_process(script_path)
            else:
                self._cleanup_update_files(script_path, new_exe_path)
                self.log_signal.emit("Установка отменена пользователем", "info")
        except Exception as e:
            self.log_signal.emit(f"Ошибка диалога подтверждения: {e}", "error")

    def _start_update_process(self, script_path: str):
        try:
            proc = subprocess.Popen([script_path], shell=True, cwd=os.path.dirname(script_path))
            self.log_signal.emit(f"Запущен установщик обновления (PID {proc.pid})", "info")
            # Закрыть приложение через 3 секунды — дать .bat забрать exe
            QTimer.singleShot(3000, self._close_application)
        except Exception as e:
            self.log_signal.emit(f"Ошибка запуска обновления: {e}", "error")

    def _cleanup_update_files(self, script_path: str, new_exe_path: str):
        try:
            if os.path.exists(new_exe_path):
                try:
                    os.remove(new_exe_path)
                except Exception:
                    pass
            if os.path.exists(script_path):
                try:
                    os.remove(script_path)
                except Exception:
                    pass
        except Exception as e:
            self.log_signal.emit(f"Ошибка очистки временных файлов: {e}", "warning")

    def _close_application(self):
        try:
            if hasattr(self.parent, 'quit_application'):
                self.parent.quit_application()
            else:
                sys.exit(0)
        except Exception:
            sys.exit(0)

