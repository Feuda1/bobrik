from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QStackedWidget, QPushButton, QButtonGroup,
                             QSystemTrayIcon, QMenu, QMessageBox, QApplication, QSplitter)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QPixmap, QAction, QKeySequence, QShortcut, QColor, QPainter, QBrush, QPen
from ui.styles import MAIN_WINDOW_STYLE
from ui.widgets.header import HeaderWidget
from ui.widgets.console_panel import ConsolePanel
from ui.widgets.dropdown_search import DropdownSearchWidget
from ui.tabs.system_tab import SystemTab
from ui.tabs.iiko_tab import IikoTab
from ui.tabs.logs_tab import LogsTab
from ui.tabs.folders_tab import FoldersTab
from ui.tabs.network_tab import NetworkTab
from ui.widgets.touch_auth_dialog import TouchAuthDialog
from managers.update_manager import SimpleUpdateManager
from config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, LAYOUT_PARAMS, get_is_small_screen

try:
    from ui.tabs.installer_tab import InstallerTab
    INSTALLER_AVAILABLE = True
except ImportError:
    INSTALLER_AVAILABLE = False

try:
    from ui.tabs.plugins_tab import PluginsTab
    PLUGINS_AVAILABLE = True
except ImportError:
    PLUGINS_AVAILABLE = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tray_icon = None
        self.is_authenticated = False
        self.is_small_screen = get_is_small_screen()
        
        self.idle_timer = QTimer()
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(self.auto_lock)
        self.idle_timeout = 10 * 60 * 1000
        
        self.init_tray_icon()
        self.init_ui()
        
        self.hide()
        
        self.console_panel.add_log("bobrik запущен в трее", "info")
        if self.is_small_screen:
            self.console_panel.add_log("Обнаружен маленький экран - включен компактный режим", "info")
        
        # Менеджер обновлений
        self.update_manager = SimpleUpdateManager(self)
        self.update_manager.log_signal.connect(self.add_log)
        self.update_manager.set_github_repo("Feuda1/bobrik")
        
    def init_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "Системный трей",
                               "Системный трей недоступен в этой системе.")
            return
        
        icon = self.load_tray_icon()
        
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
        
        window_icon = self.load_window_icon()
        self.setWindowIcon(window_icon)
        
        # Адаптивные размеры окна
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(800 if self.is_small_screen else 1000, 
                          500 if self.is_small_screen else 600)
        
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок с адаптивной высотой
        self.header = HeaderWidget()
        self.header.search_text_changed.connect(self.on_search_text_changed)
        self.header.search_focus_gained.connect(self.on_search_focus_gained)
        self.header.search_focus_lost.connect(self.on_search_focus_lost)
        self.header.search_position_requested.connect(self.position_dropdown_search)
        self.header.exit_requested.connect(self.quit_application)
        self.header.check_updates_requested.connect(self.check_updates)
        main_layout.addWidget(self.header)
        
        # Основной контент с адаптивными отступами
        content_layout = QHBoxLayout()
        margins = LAYOUT_PARAMS['content_margins']
        spacing = LAYOUT_PARAMS['content_spacing']
        content_layout.setContentsMargins(margins, margins, margins, margins)
        content_layout.setSpacing(spacing)
        
        # Для маленьких экранов используем сплиттер для изменения размеров
        if self.is_small_screen:
            self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
            
            # Левая часть - вкладки и контент
            left_widget = QWidget()
            left_layout = QHBoxLayout(left_widget)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(spacing)
            
            self.create_tabs_content(left_layout)
            
            # Правая часть - консоль
            self.console_panel = ConsolePanel()
            self.console_panel.activity_detected.connect(self.reset_idle_timer)
            
            self.main_splitter.addWidget(left_widget)
            self.main_splitter.addWidget(self.console_panel)
            
            # Устанавливаем пропорции: 60% контент, 40% консоль
            self.main_splitter.setSizes([600, 400])
            self.main_splitter.setCollapsible(0, False)  # Контент нельзя полностью скрыть
            self.main_splitter.setCollapsible(1, True)   # Консоль можно скрыть
            
            content_layout.addWidget(self.main_splitter)
        else:
            # Для больших экранов используем обычный layout
            self.create_tabs_content(content_layout)
            
            self.console_panel = ConsolePanel()
            self.console_panel.activity_detected.connect(self.reset_idle_timer)
            content_layout.addWidget(self.console_panel, 1)
        
        main_layout.addLayout(content_layout)
        
        # Выпадающий поиск
        self.dropdown_search = DropdownSearchWidget(self)
        self.dropdown_search.search_activated.connect(self.handle_search_result)
        self.dropdown_search.search_closed.connect(self.on_search_closed)
        
        self.tab_buttons.idClicked.connect(self.switch_tab)
        
        if self.tab_buttons.buttons():
            self.tab_buttons.buttons()[0].setChecked(True)
            self.stacked_widget.setCurrentIndex(0)
            
        self.setup_shortcuts()
        
        # Таймер для задержки поиска
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_delayed_search)
        self.pending_search_text = ""
        
    def create_tabs_content(self, parent_layout):
        """Создает область вкладок и контента"""
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(LAYOUT_PARAMS['content_spacing'])
        
        # Область вкладок с адаптивной шириной
        tabs_scroll = QScrollArea()
        tabs_scroll.setWidgetResizable(True)
        tabs_scroll.setFixedWidth(LAYOUT_PARAMS['tabs_width'])
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
        
        parent_layout.addLayout(tabs_layout, 2)
        
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
            
        if PLUGINS_AVAILABLE:
            tabs_data.append(("Плагины", PluginsTab()))
        
        # Адаптивная высота кнопок вкладок
        button_height = 25 if self.is_small_screen else 30
        
        for i, (name, widget) in enumerate(tabs_data):
            button = QPushButton(name)
            button.setCheckable(True)
            button.setFixedHeight(button_height)
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
        font_size = 11 if self.is_small_screen else 12
        return f"""
            QPushButton {{
                background-color: #1a1a1a;
                color: #808080;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 6px 10px;
                text-align: left;
                font-size: {font_size}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #222222;
                color: #e0e0e0;
                border-color: #3a3a3a;
            }}
            QPushButton:checked {{
                background-color: #2a2a2a;
                color: #ffffff;
                border-color: #4a4a4a;
            }}
            QPushButton:pressed {{
                background-color: #1a1a1a;
            }}
        """
        
    def resizeEvent(self, event):
        """Обработка изменения размера окна"""
        super().resizeEvent(event)
        
        # Для маленьких экранов автоматически скрываем консоль при очень малой ширине
        if self.is_small_screen and hasattr(self, 'main_splitter'):
            window_width = event.size().width()
            if window_width < 900:
                # Скрываем консоль
                self.main_splitter.setSizes([window_width, 0])
            elif window_width > 1000:
                # Показываем консоль
                self.main_splitter.setSizes([int(window_width * 0.6), int(window_width * 0.4)])
        
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
        if self.dropdown_search.is_visible:
            search_rect = self.dropdown_search.geometry()
            if not search_rect.contains(event.pos()):
                self.dropdown_search.hide_dropdown()
                
        self.reset_idle_timer()
        super().mousePressEvent(event)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.dropdown_search.is_visible:
            self.dropdown_search.hide_dropdown()
            self.header.clear_search()
            
        elif event.key() == Qt.Key.Key_Return and self.dropdown_search.is_visible:
            self.dropdown_search.execute_first_result()
            
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
        auth_dialog = TouchAuthDialog(self)
        auth_dialog.auth_accepted.connect(self.on_pin_accepted)
        
        if auth_dialog.exec() == auth_dialog.DialogCode.Accepted:
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
        self.dropdown_search.hide_dropdown()
        self.hide()
    
    def quit_application(self):
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
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.activated.connect(self.focus_header_search)
        
    def focus_header_search(self):
        if self.is_authenticated:
            self.header.focus_search()
            self.console_panel.add_log("🔍 Поиск активирован (Ctrl+K)", "info")
    
    def check_updates(self):
        self.update_manager.check_for_updates()
        self.reset_idle_timer()
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ИКОНКАМИ ===
    
    def load_tray_icon(self):
        return self.create_default_icon()

    def create_default_icon(self):
        try:
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            painter.setBrush(QBrush(QColor(26, 26, 26)))
            painter.setPen(QPen(QColor(64, 64, 64), 2))
            painter.drawEllipse(2, 2, 28, 28)
            
            painter.setPen(QPen(QColor(224, 224, 224)))
            font = painter.font()
            font.setPointSize(18)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "b")
            
            painter.end()
            
            return QIcon(pixmap)
            
        except Exception as e:
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(26, 26, 26))
            return QIcon(pixmap)

    def load_window_icon(self):
        return self.create_default_icon()
    
    # === ОБРАБОТЧИКИ ПОИСКА ===
    
    def on_search_text_changed(self, text):
        if not text.strip():
            self.dropdown_search.hide_dropdown()
            return
        
        self.pending_search_text = text
        self.search_timer.stop()
        self.search_timer.start(300)
    
    def perform_delayed_search(self):
        if self.pending_search_text and self.dropdown_search.is_visible:
            self.dropdown_search.perform_search(self.pending_search_text)
    
    def on_search_focus_gained(self):
        text = self.header.get_search_text()
        if text.strip():
            self.header.emit_search_position()
    
    def on_search_focus_lost(self):
        QTimer.singleShot(150, self.check_hide_search)
    
    def check_hide_search(self):
        focused_widget = QApplication.focusWidget()
        if (focused_widget != self.header.search_input and 
            focused_widget != self.dropdown_search.results_list):
            self.dropdown_search.hide_dropdown()
    
    def position_dropdown_search(self, x, y):
        if self.is_authenticated and self.header.get_search_text().strip():
            self.dropdown_search.show_dropdown(x, y)
    
    def on_search_closed(self):
        pass
        
    def handle_search_result(self, tab_index, action):
        search_item = None
        if hasattr(self.dropdown_search, '_last_selected_item'):
            search_item = self.dropdown_search._last_selected_item
        
        if 0 <= tab_index < len(self.tab_buttons.buttons()):
            self.tab_buttons.buttons()[tab_index].setChecked(True)
            self.stacked_widget.setCurrentIndex(tab_index)
            
            tab_names = ["Система", "iiko", "Логи", "Папки", "Сеть", "Программы", "Плагины"]
            tab_name = tab_names[tab_index] if tab_index < len(tab_names) else "Неизвестно"
            self.console_panel.add_log(f"📍 Переход: {tab_name}", "info")
            
            if search_item and hasattr(search_item, 'button_text') and search_item.button_text:
                self.highlight_button_in_tab(tab_index, search_item.button_text)
            
            self.header.clear_search()
            
            if action:
                pass
                
    def highlight_button_in_tab(self, tab_index, button_text):
        try:
            tab_widget = self.stacked_widget.widget(tab_index)
            if not tab_widget:
                return
                
            from PyQt6.QtWidgets import QPushButton
            buttons = tab_widget.findChildren(QPushButton)
            
            for button in buttons:
                if button.text() == button_text:
                    self.apply_highlight_style(button)
                    QTimer.singleShot(3000, lambda: self.remove_highlight_style(button))
                    self.console_panel.add_log(f"🔍 Найдено: {button_text}", "info")
                    break
                    
        except Exception as e:
            print(f"Ошибка подсветки кнопки: {e}")
            
    def apply_highlight_style(self, button):
        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7c3aed,
                    stop: 1 #5b21b6);
                border: 2px solid #a855f7;
                border-radius: 4px;
                color: #ffffff;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 2px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #8b5cf6,
                    stop: 1 #6d28d9);
                border-color: #c084fc;
            }
            QPushButton:pressed {
                background: #6d28d9;
                border-color: #a855f7;
            }
        """)
        
    def remove_highlight_style(self, button):
        button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 2px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)