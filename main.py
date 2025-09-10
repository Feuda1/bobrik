import sys
import ctypes
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow

def _hide_console_window_windows():
    if sys.platform != "win32":
        return
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:
        pass

def _patch_subprocess_no_console_windows():
    if sys.platform != "win32":
        return
    try:
        import subprocess as _sp
        if getattr(_sp, "_bobrik_no_console_patched", False):
            return

        CREATE_NO_WINDOW = getattr(_sp, "CREATE_NO_WINDOW", 0x08000000)
        STARTF_USESHOWWINDOW = 0x00000001
        SW_HIDE = 0

        _orig_popen = _sp.Popen

        def _popen_no_window(*args, **kwargs):
            flags = kwargs.get("creationflags", 0) | CREATE_NO_WINDOW
            kwargs["creationflags"] = flags

            si = kwargs.get("startupinfo")
            if si is None:
                si = _sp.STARTUPINFO()
            si.dwFlags |= STARTF_USESHOWWINDOW
            si.wShowWindow = SW_HIDE
            kwargs["startupinfo"] = si

            return _orig_popen(*args, **kwargs)

        _sp.Popen = _popen_no_window
        _sp._bobrik_no_console_patched = True
    except Exception:
        pass

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    try:
        if sys.platform == "win32":
            if getattr(sys, 'frozen', False):
                script = sys.executable
            else:
                script = os.path.abspath(__file__)
            
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                f'"{script}"', 
                None, 
                1
            )
            return True
        else:
            print("Функция запроса прав администратора доступна только в Windows")
            return False
    except Exception as e:
        print(f"Ошибка при запросе прав администратора: {e}")
        return False

def main():
    # Скрыть окно консоли и запретить появление консоли у дочерних процессов
    _hide_console_window_windows()
    _patch_subprocess_no_console_windows()

    # Настраиваем автозагрузку при первом запуске
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(10, 10, 10))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    app.setPalette(palette)
    
    window = MainWindow()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
