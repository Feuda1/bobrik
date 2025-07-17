from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QStackedWidget, QPushButton, QButtonGroup)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from ui.styles import MAIN_WINDOW_STYLE
from ui.widgets.header import HeaderWidget
from ui.widgets.console_panel import ConsolePanel
from ui.tabs.system_tab import SystemTab
from ui.tabs.iiko_tab import IikoTab
from ui.tabs.logs_tab import LogsTab
from ui.tabs.folders_tab import FoldersTab
from ui.tabs.network_tab import NetworkTab
from config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.console_panel.add_log("bobrik запущен", "info")
        
    def init_ui(self):
        self.setWindowTitle(" ")
        # Создаем полностью прозрачную иконку
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        self.setWindowIcon(QIcon(pixmap))
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.header = HeaderWidget()
        main_layout.addWidget(self.header)
        
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(10)
        
        tabs_scroll = QScrollArea()
        tabs_scroll.setWidgetResizable(True)
        tabs_scroll.setFixedWidth(120)
        tabs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tabs_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tabs_scroll.setStyleSheet(self.get_scroll_style())
        
        tabs_widget = QWidget()
        tabs_layout_inner = QVBoxLayout(tabs_widget)
        tabs_layout_inner.setContentsMargins(5, 5, 5, 5)
        tabs_layout_inner.setSpacing(2)
        
        self.tab_buttons = QButtonGroup()
        self.tab_buttons.setExclusive(True)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet(self.get_content_style())
        
        self.create_tabs(tabs_layout_inner)
        
        tabs_layout_inner.addStretch()
        tabs_scroll.setWidget(tabs_widget)
        
        tabs_layout.addWidget(tabs_scroll)
        tabs_layout.addWidget(self.stacked_widget, 1)
        
        content_layout.addLayout(tabs_layout, 2)
        
        self.console_panel = ConsolePanel()
        content_layout.addWidget(self.console_panel, 1)
        
        main_layout.addLayout(content_layout)
        
        self.tab_buttons.idClicked.connect(self.switch_tab)
        
        if self.tab_buttons.buttons():
            self.tab_buttons.buttons()[0].setChecked(True)
            self.stacked_widget.setCurrentIndex(0)
        
    def create_tabs(self, layout):
        """Создание вкладок"""
        tabs_data = [
            ("Система", SystemTab()),
            ("iiko", IikoTab()),
            ("Логи", LogsTab()),
            ("Папки", FoldersTab()),
            ("Сеть", NetworkTab()),
        ]
        
        for i, (name, widget) in enumerate(tabs_data):
            button = QPushButton(name)
            button.setCheckable(True)
            button.setFixedHeight(30)
            button.setStyleSheet(self.get_tab_button_style())
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            
            self.tab_buttons.addButton(button, i)
            layout.addWidget(button)
            self.stacked_widget.addWidget(widget)
            
            if hasattr(widget, 'log_signal'):
                widget.log_signal.connect(self.add_log)
        
    def switch_tab(self, tab_id):
        """Переключение вкладки"""
        self.stacked_widget.setCurrentIndex(tab_id)
        
    def get_scroll_style(self):
        return """
            QScrollArea {
                background-color: #141414;
                border: 1px solid #1f1f1f;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505050;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """
        
    def get_content_style(self):
        return """
            QStackedWidget {
                background-color: #141414;
                border: 1px solid #1f1f1f;
                border-radius: 8px;
            }
        """
        
    def get_tab_button_style(self):
        return """
            QPushButton {
                background-color: #1a1a1a;
                color: #808080;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 6px 10px;
                text-align: left;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #222222;
                color: #e0e0e0;
                border-color: #3a3a3a;
            }
            QPushButton:checked {
                background-color: #2a2a2a;
                color: #ffffff;
                border-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """
        
    def add_log(self, message, log_type="info"):
        self.console_panel.add_log(message, log_type)
        
    def closeEvent(self, event):
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if hasattr(widget, 'cleanup'):
                widget.cleanup()
        event.accept()