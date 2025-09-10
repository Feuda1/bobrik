import os
import sys
import subprocess
from typing import Optional

try:
    import winreg  # type: ignore
except Exception:
    winreg = None

def is_first_run():
    """Проверяет, первый ли это запуск"""
    config_dir = os.path.join(os.getenv('APPDATA'), 'bobrik')
    config_file = os.path.join(config_dir, 'startup_added.txt')
    return not os.path.exists(config_file)

def mark_startup_added():
    """Отмечает, что автозагрузка была настроена"""
    config_dir = os.path.join(os.getenv('APPDATA'), 'bobrik')
    try:
        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, 'startup_added.txt'), 'w') as f:
            f.write('startup_configured')
        return True
    except:
        return False

def add_to_startup():
    """Добавляет в реестр автозагрузки"""
    try:
        if sys.platform != "win32":
            return False
            
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        
        print(f"Добавляем в автозагрузку: {exe_path}")
        
        # Добавляем в реестр
        cmd = [
            'reg', 'add', 
            r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
            '/v', 'bobrik', 
            '/t', 'REG_SZ', 
            '/d', f'"{exe_path}"', 
            '/f'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Добавлено в реестр автозагрузки")
            return True
        else:
            print(f"❌ Ошибка добавления в реестр: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при добавлении в автозагрузку: {e}")
        return False

def check_startup_exists():
    """Проверяет, есть ли запись в автозагрузке"""
    try:
        result = subprocess.run([
            'reg', 'query', 
            r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
            '/v', 'bobrik'
        ], capture_output=True, text=True)
        
        return result.returncode == 0
    except:
        return False

def setup_startup_if_first_run():
    """Настраивает автозагрузку при первом запуске"""
    try:
        print("Проверяем настройку автозагрузки...")
        
        if is_first_run():
            print("🎉 Первый запуск - настраиваем автозагрузку")
            
            if add_to_startup():
                mark_startup_added()
                print("✅ bobrik настроен для автозапуска")
            else:
                mark_startup_added()  # Отмечаем чтобы не пытаться снова
                print("❌ Не удалось настроить автозагрузку")
        else:
            # Проверяем что автозагрузка на месте
            if check_startup_exists():
                print("✅ Автозагрузка уже настроена")
            else:
                print("⚠️ Автозагрузка отсутствует, восстанавливаем")
                add_to_startup()
                
    except Exception as e:
        print(f"❌ Ошибка настройки автозагрузки: {e}")

# Для тестирования
if __name__ == "__main__":
    setup_startup_if_first_run()

# New autostart API (used by UI)

def autostart_is_enabled() -> bool:
    try:
        import winreg  # type: ignore
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            try:
                winreg.QueryValueEx(key, 'bobrik')
                return True
            except FileNotFoundError:
                return False
    except Exception:
        return False


def autostart_enable() -> bool:
    try:
        import winreg  # type: ignore
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        if getattr(sys, 'frozen', False):
            target = sys.executable
        else:
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))
            target = '"' + sys.executable + '" ' + '"' + script_path + '"'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, 'bobrik', 0, winreg.REG_SZ, target)
        return True
    except FileNotFoundError:
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:  # type: ignore[name-defined]
                winreg.SetValueEx(key, 'bobrik', 0, winreg.REG_SZ, target)
            return True
        except Exception:
            return False
    except Exception:
        return False


def autostart_disable() -> bool:
    try:
        import winreg  # type: ignore
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, 'bobrik')
                return True
            except FileNotFoundError:
                return True
    except Exception:
        return False
