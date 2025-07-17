import os

WINDOW_TITLE = ""
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

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

FONTS = {
    "logo": {"size": 24, "weight": 600},
    "title": {"size": 18, "weight": 500},
    "button": {"size": 16, "weight": 500},
    "console": {"size": 13, "family": "'Consolas', 'Monaco', monospace"}
}

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