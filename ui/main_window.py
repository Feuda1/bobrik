from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget
from PyQt6.QtCore import Qt
from ui.styles import MAIN_WINDOW_STYLE
from ui.widgets.header import HeaderWidget
from ui.widgets.console_panel import ConsolePanel
from ui.tabs.system_tab import SystemTab
from config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.console_panel.add_log("Bobrik запущен", "info")
        
    def init_ui(self):
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.header = HeaderWidget()
        main_layout.addWidget(self.header)
        
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Левая панель с вкладками
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self.get_tab_style())
        
        # Добавляем вкладки
        self.system_tab = SystemTab()
        self.system_tab.log_signal.connect(self.add_log)
        self.tab_widget.addTab(self.system_tab, "Система")
        
        # Заготовки для будущих вкладок
        self.tab_widget.addTab(QWidget(), "Сеть")
        self.tab_widget.addTab(QWidget(), "Файлы")
        self.tab_widget.addTab(QWidget(), "Процессы")
        self.tab_widget.addTab(QWidget(), "Инструменты")
        
        content_layout.addWidget(self.tab_widget, 2)
        
        # Правая панель с консолью
        self.console_panel = ConsolePanel()
        content_layout.addWidget(self.console_panel, 1)
        
        main_layout.addLayout(content_layout)
        
    def get_tab_style(self):
        return """
            QTabWidget::pane {
                background-color: #141414;
                border: 1px solid #1f1f1f;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #1a1a1a;
                color: #808080;
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #141414;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #222222;
                color: #e0e0e0;
            }
        """
        
    def add_log(self, message, log_type="info"):
        self.console_panel.add_log(message, log_type)
        
    def closeEvent(self, event):
        # Вызываем cleanup для всех вкладок
        if hasattr(self.system_tab, 'cleanup'):
            self.system_tab.cleanup()
        event.accept()