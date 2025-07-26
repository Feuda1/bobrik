import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRect

WINDOW_TITLE = ""

# Кеш для оптимизации повторных вызовов
_screen_cache = {}

# Функция для определения размера экрана и адаптивных размеров
def get_adaptive_window_size():
    """Определяет оптимальный размер окна на основе разрешения экрана"""
    # Проверяем кеш
    if 'window_size' in _screen_cache:
        return _screen_cache['window_size']
        
    app = QApplication.instance()
    if app is None:
        # Если приложение еще не создано, используем значения по умолчанию
        size = (1200, 700)
        _screen_cache['window_size'] = size
        return size
    
    # Получаем размер основного экрана
    screen = app.primaryScreen()
    screen_geometry = screen.availableGeometry()
    screen_width = screen_geometry.width()
    screen_height = screen_geometry.height()
    
    # Определяем размеры окна на основе разрешения экрана
    if screen_width <= 1024 or screen_height <= 768:
        # Маленькие экраны (POS терминалы, старые мониторы)
        window_width = min(950, screen_width - 50)
        window_height = min(600, screen_height - 50)
    elif screen_width <= 1366 or screen_height <= 768:
        # Средние экраны (ноутбуки)
        window_width = min(1100, screen_width - 100)
        window_height = min(650, screen_height - 100)
    else:
        # Большие экраны (настольные мониторы)
        window_width = min(1200, screen_width - 200)
        window_height = min(700, screen_height - 150)
    
    size = (window_width, window_height)
    _screen_cache['window_size'] = size
    return size

def get_is_small_screen():
    """Проверяет, является ли экран маленьким"""
    # Проверяем кеш
    if 'is_small_screen' in _screen_cache:
        return _screen_cache['is_small_screen']
        
    app = QApplication.instance()
    if app is None:
        _screen_cache['is_small_screen'] = False
        return False
    
    screen = app.primaryScreen()
    screen_geometry = screen.availableGeometry()
    is_small = screen_geometry.width() <= 1024 or screen_geometry.height() <= 768
    _screen_cache['is_small_screen'] = is_small
    return is_small

# Адаптивные размеры
WINDOW_WIDTH, WINDOW_HEIGHT = get_adaptive_window_size()

COLORS = {
    "background": "#0a0a0a",
    "panel": "#141414",
    "border": "#1f1f1f",
    "text": "#e0e0e0",
    "text_secondary": "#808080",
    "white": "#ffffff",
    "button": "#1f1f1f",
    "button_hover": "#262626",
    "button_active": "#1a1a1a",
    "success": "#10b981",
    "success_bg": "#065f46",
    "success_border": "#10b981",
    "error": "#ef4444",
    "warning": "#f59e0b",
    "info": "#3b82f6",
    "timestamp": "#6366f1"
}

def get_adaptive_fonts():
    """Возвращает адаптивные размеры шрифтов"""
    # Проверяем кеш
    if 'fonts' in _screen_cache:
        return _screen_cache['fonts']
        
    is_small = get_is_small_screen()
    
    if is_small:
        fonts = {
            "logo": {"size": 20, "weight": 600},
            "title": {"size": 16, "weight": 500},
            "button": {"size": 14, "weight": 500},
            "console": {"size": 11, "family": "'Consolas', 'Monaco', monospace"}
        }
    else:
        fonts = {
            "logo": {"size": 24, "weight": 600},
            "title": {"size": 18, "weight": 500},
            "button": {"size": 16, "weight": 500},
            "console": {"size": 13, "family": "'Consolas', 'Monaco', monospace"}
        }
    
    _screen_cache['fonts'] = fonts
    return fonts

FONTS = get_adaptive_fonts()

def get_adaptive_layout_params():
    """Возвращает адаптивные параметры интерфейса"""
    # Проверяем кеш
    if 'layout_params' in _screen_cache:
        return _screen_cache['layout_params']
        
    is_small = get_is_small_screen()
    
    if is_small:
        params = {
            "header_height": 60,
            "tabs_width": 100,
            "button_width": 90,
            "button_height": 40,
            "buttons_per_row": 4,  # Меньше кнопок в ряду для маленьких экранов
            "content_margins": 10,
            "content_spacing": 10,
            "console_min_height": 200
        }
    else:
        params = {
            "header_height": 70,
            "tabs_width": 120,
            "button_width": 105,
            "button_height": 45,
            "buttons_per_row": 5,
            "content_margins": 15,
            "content_spacing": 15,
            "console_min_height": 250
        }
    
    _screen_cache['layout_params'] = params
    return params

LAYOUT_PARAMS = get_adaptive_layout_params()

TOUCHSCREEN_KEYWORDS = [
    'touch', 'hid-compliant', 'touchscreen', 'digitizer', 
    'touch screen', 'multi-touch', 'finger'
]

USERNAME = os.getenv('USERNAME', 'User')

IIKO_PATHS = {
    'executable': r"C:\Program Files\iiko\iikoRMS\Front.Net\iikoFront.Net.exe",
    'logs': f"C:\\Users\\{USERNAME}\\AppData\\Roaming\\iiko\\CashServer\\Logs",
    'entities_storage': f"C:\\Users\\{USERNAME}\\AppData\\Roaming\\iiko\\CashServer\\EntitiesStorage",
    'plugin_configs': f"C:\\Users\\{USERNAME}\\AppData\\Roaming\\iiko\\CashServer\\PluginConfigs",
    'config_xml': f"C:\\Users\\{USERNAME}\\AppData\\Roaming\\iiko\\CashServer\\config.xml",
    'entities_db': f"C:\\Users\\{USERNAME}\\AppData\\Roaming\\iiko\\CashServer\\EntitiesStorage\\Entities"
}

SYSTEM_PATHS = {
    'notepad_plus': r"C:\Program Files\Notepad++\notepad++.exe",
    'startup_folder': f"C:\\Users\\{USERNAME}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
    'temp_folders': [
        os.getenv('TEMP'),
        f"C:\\Users\\{USERNAME}\\AppData\\Local\\Temp",
        r"C:\Windows\Temp"
    ]
}

IIKO_CARD_URL = "https://m1.iiko.cards/ru-RU/About/DownloadPosInstaller?useRc=False"

LOG_KEYWORDS = [
    'cash-server',
    'virtual-printer', 
    'OnlineMarkingVerificationPlugin',
    'PaymentSystem.DualConnector',
    'SberbankPlugin',
    'Transport',
    'Api.Delivery',
    'AlcoholMarkingPlugin'
]