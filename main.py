import sys
import ctypes
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow

def is_admin():
    """Проверяет, запущена ли программа от имени администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Перезапускает программу от имени администратора"""
    try:
        if sys.platform == "win32":
            # Получаем путь к текущему исполняемому файлу
            if getattr(sys, 'frozen', False):
                # Если это скомпилированный exe файл
                script = sys.executable
            else:
                # Если это Python скрипт
                script = os.path.abspath(__file__)
            
            # Перезапускаем с правами администратора
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
    # Проверяем, запущена ли программа от имени администратора
    if not is_admin():
        print("Программа требует права администратора для полной функциональности.")
        print("Перезапуск с правами администратора...")
        
        # Пытаемся перезапустить с правами администратора
        if run_as_admin():
            # Если удалось перезапустить, закрываем текущий процесс
            sys.exit(0)
        else:
            print("Не удалось получить права администратора.")
            print("Программа будет запущена с ограниченной функциональностью.")
            # Продолжаем работу без прав администратора
    else:
        print("Программа запущена с правами администратора.")
    
    # Создаем приложение Qt
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Настраиваем темную тему
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(10, 10, 10))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    app.setPalette(palette)
    
    # Создаем главное окно
    window = MainWindow()
    # НЕ показываем окно - оно будет в трее
    # window.show()  # Закомментировано - запуск в трее
    
    # Запускаем приложение
    sys.exit(app.exec())

if __name__ == "__main__":
    main()