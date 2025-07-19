from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QStackedWidget, QPushButton, QButtonGroup,
                             QSystemTrayIcon, QMenu, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QAction, QKeySequence, QShortcut
from ui.styles import MAIN_WINDOW_STYLE
from ui.widgets.header import HeaderWidget
from ui.widgets.console_panel import ConsolePanel
from ui.widgets.global_search import GlobalSearchWidget
from ui.tabs.system_tab import SystemTab
from ui.tabs.iiko_tab import IikoTab
from ui.tabs.logs_tab import LogsTab
from ui.tabs.folders_tab import FoldersTab
from ui.tabs.network_tab import NetworkTab
from ui.widgets.pin_dialog import PinDialog
from config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT

try:
    from ui.tabs.installer_tab import InstallerTab
    INSTALLER_AVAILABLE = True
except ImportError:
    INSTALLER_AVAILABLE = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tray_icon = None
        self.is_authenticated = False
        
        self.idle_timer = QTimer()
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(self.auto_lock)
        self.idle_timeout = 10 * 60 * 1000
        
        self.init_tray_icon()
        self.init_ui()
        
        self.hide()
        
        self.console_panel.add_log("bobrik запущен в трее", "info")
        
    def init_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "Системный трей",
                               "Системный трей недоступен в этой системе.")
            return
        
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.black)
        icon = QIcon(pixmap)
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)
        
        tray_menu = QMenu()
        
        show_action = QAction("Показать bobrik", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
    def init_ui(self):
        self.setWindowTitle(" ")
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
        self.header.search_requested.connect(self.open_global_search)
        main_layout.addWidget(self.header)
        
        # Основной контент в стеке (обычный интерфейс + поиск)
        self.main_stack = QStackedWidget()
        
        # Обычный интерфейс
        normal_widget = QWidget()
        content_layout = QHBoxLayout(normal_widget)
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
        self.console_panel.activity_detected.connect(self.reset_idle_timer)
        content_layout.addWidget(self.console_panel, 1)
        
        self.main_stack.addWidget(normal_widget)
        
        # Глобальный поиск
        self.global_search = GlobalSearchWidget(self)
        self.global_search.search_activated.connect(self.handle_search_result)
        self.global_search.search_closed.connect(self.close_global_search)
        self.main_stack.addWidget(self.global_search)
        
        main_layout.addWidget(self.main_stack)
        
        self.tab_buttons.idClicked.connect(self.switch_tab)
        
        if self.tab_buttons.buttons():
            self.tab_buttons.buttons()[0].setChecked(True)
            self.stacked_widget.setCurrentIndex(0)
            
        # Горячие клавиши
        self.setup_shortcuts()
        
    def create_tabs(self, layout):
        tabs_data = [
            ("Система", SystemTab()),
            ("iiko", IikoTab()),
            ("Логи", LogsTab()),
            ("Папки", FoldersTab()),
            ("Сеть", NetworkTab()),
        ]
        
        if INSTALLER_AVAILABLE:
            tabs_data.append(("Программы", InstallerTab()))
        
        for i, (name, widget) in enumerate(tabs_data):
            button = QPushButton(name)
            button.setCheckable(True)
            button.setFixedHeight(30)
            button.setStyleSheet(self.get_tab_button_style())
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            
            button.clicked.connect(self.reset_idle_timer)
            
            self.tab_buttons.addButton(button, i)
            layout.addWidget(button)
            self.stacked_widget.addWidget(widget)
            
            if hasattr(widget, 'log_signal'):
                widget.log_signal.connect(self.add_log)
            
            self.connect_widget_activity(widget)
    
    def connect_widget_activity(self, widget):
        widget.mousePressEvent = self.wrap_event(widget.mousePressEvent)
        widget.keyPressEvent = self.wrap_event(widget.keyPressEvent)
        
        from PyQt6.QtWidgets import QPushButton
        buttons = widget.findChildren(QPushButton)
        for button in buttons:
            button.clicked.connect(self.reset_idle_timer)
    
    def wrap_event(self, original_event):
        def wrapped_event(event):
            self.reset_idle_timer()
            return original_event(event)
        return wrapped_event
        
    def switch_tab(self, tab_id):
        self.stacked_widget.setCurrentIndex(tab_id)
        self.reset_idle_timer()
        
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
        
    def reset_idle_timer(self):
        if self.is_authenticated and self.isVisible():
            self.idle_timer.stop()
            self.idle_timer.start(self.idle_timeout)
    
    def auto_lock(self):
        if self.is_authenticated and self.isVisible():
            self.console_panel.add_log("🔒 Автоблокировка: бездействие более 10 минут", "warning")
            self.is_authenticated = False
            self.hide_to_tray()
            
    def mousePressEvent(self, event):
        self.reset_idle_timer()
        super().mousePressEvent(event)
        
    def keyPressEvent(self, event):
        self.reset_idle_timer()
        super().keyPressEvent(event)
        
    def mouseMoveEvent(self, event):
        self.reset_idle_timer()
        super().mouseMoveEvent(event)
        
    def wheelEvent(self, event):
        self.reset_idle_timer()
        super().wheelEvent(event)
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
    
    def show_window(self):
        if not self.is_authenticated:
            self.show_pin_dialog()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            self.reset_idle_timer()
    
    def show_pin_dialog(self):
        pin_dialog = PinDialog(self)
        pin_dialog.pin_accepted.connect(self.on_pin_accepted)
        
        if pin_dialog.exec() == pin_dialog.DialogCode.Accepted:
            pass
        else:
            pass
    
    def on_pin_accepted(self):
        self.is_authenticated = True
        self.console_panel.add_log("Авторизация успешна", "success")
        
        self.show()
        self.raise_()
        self.activateWindow()
        self.reset_idle_timer()
    
    def hide_to_tray(self):
        self.idle_timer.stop()
        self.hide()
    
    def quit_application(self):
        msg = QMessageBox(self)
        msg.setWindowTitle('Выход из программы')
        msg.setText('Вы действительно хотите закрыть bobrik?')
        msg.setIcon(QMessageBox.Icon.Question)
        
        yes_button = msg.addButton('Да', QMessageBox.ButtonRole.YesRole)
        no_button = msg.addButton('Нет', QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(no_button)
        
        msg.exec()
        
        if msg.clickedButton() == yes_button:
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if hasattr(widget, 'cleanup'):
                    widget.cleanup()
            
            if self.tray_icon:
                self.tray_icon.hide()
            
            QApplication.instance().quit()
        
    def closeEvent(self, event):
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide_to_tray()
        else:
            event.accept()
            
    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                if self.tray_icon and self.tray_icon.isVisible():
                    event.ignore()
                    self.hide_to_tray()
                    return
        super().changeEvent(event)
    
    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        # Ctrl+K для глобального поиска
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.activated.connect(self.open_global_search)
        
        # Escape для закрытия поиска
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.close_global_search)
        
    def open_global_search(self):
        """Открыть глобальный поиск"""
        if self.is_authenticated:
            self.main_stack.setCurrentWidget(self.global_search)
            self.global_search.focus_search()
            self.console_panel.add_log("🔍 Глобальный поиск открыт (Ctrl+K)", "info")
            
    def close_global_search(self):
        """Закрыть глобальный поиск"""
        if self.main_stack.currentWidget() == self.global_search:
            self.main_stack.setCurrentIndex(0)  # Вернуться к обычному интерфейсу
            self.global_search.clear_search()
            
    def handle_search_result(self, tab_index, action):
        """Обработка результата поиска"""
        # Переключиться на нужную вкладку
        if 0 <= tab_index < len(self.tab_buttons.buttons()):
            self.tab_buttons.buttons()[tab_index].setChecked(True)
            self.stacked_widget.setCurrentIndex(tab_index)
            
            # Показать сообщение о переходе
            tab_names = ["Система", "iiko", "Логи", "Папки", "Сеть", "Программы"]
            tab_name = tab_names[tab_index] if tab_index < len(tab_names) else "Неизвестно"
            self.console_panel.add_log(f"📍 Переход на вкладку: {tab_name}", "info")
            
            # Если есть специальное действие, выполнить его
            if action:
                # Здесь можно добавить выполнение конкретных действий
                pass