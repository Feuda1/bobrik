import sys
import ctypes
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow

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
    if not is_admin():
        print("Программа требует права администратора для полной функциональности.")
        print("Перезапуск с правами администратора...")
        
        if run_as_admin():
            sys.exit(0)
        else:
            print("Не удалось получить права администратора.")
            print("Программа будет запущена с ограниченной функциональностью.")
    else:
        print("Программа запущена с правами администратора.")
    
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