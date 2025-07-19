from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, 
                             QListWidgetItem, QLabel, QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QPixmap

class SearchItem:
    def __init__(self, title, description, tab_index, action=None, keywords=None):
        self.title = title
        self.description = description
        self.tab_index = tab_index
        self.action = action
        self.keywords = keywords or []
        
    def matches(self, query):
        query = query.lower()
        # Поиск в названии, описании и ключевых словах
        return (query in self.title.lower() or 
                query in self.description.lower() or
                any(query in keyword.lower() for keyword in self.keywords))

class GlobalSearchWidget(QWidget):
    search_activated = pyqtSignal(int, object)  # tab_index, action
    search_closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_items = []
        self.init_ui()
        self.index_all_items()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Поле поиска
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(15, 15, 15, 10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Глобальный поиск по всем функциям...")
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.execute_first_result)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                border: 2px solid #3b82f6;
                border-radius: 8px;
                padding: 8px 16px;
                color: #e0e0e0;
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit:focus {
                border-color: #60a5fa;
                background-color: #262626;
            }
        """)
        search_layout.addWidget(self.search_input)
        
        close_button = QPushButton("✕")
        close_button.setFixedSize(40, 40)
        close_button.clicked.connect(self.close_search)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                color: #e0e0e0;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ef4444;
                border-color: #ef4444;
            }
        """)
        search_layout.addWidget(close_button)
        
        layout.addLayout(search_layout)
        
        # Список результатов
        self.results_list = QListWidget()
        self.results_list.setMaximumHeight(400)
        self.results_list.itemClicked.connect(self.execute_result)
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #141414;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                margin: 0px 15px 15px 15px;
                outline: none;
            }
            QListWidget::item {
                background-color: transparent;
                border-bottom: 1px solid #1a1a1a;
                padding: 12px;
                min-height: 50px;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #3b82f6;
                color: white;
            }
        """)
        layout.addWidget(self.results_list)
        
        # Подсказка
        self.hint_label = QLabel("Начните вводить для поиска функций...")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 13px;
                padding: 20px;
                background-color: #0f0f0f;
                border-radius: 6px;
                margin: 0px 15px 15px 15px;
            }
        """)
        layout.addWidget(self.hint_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #0a0a0a;
                border: 2px solid #3b82f6;
                border-radius: 12px;
            }
        """)
        
    def index_all_items(self):
        """Индексирует все кнопки и функции из всех вкладок"""
        self.search_items = [
            # Системные функции (вкладка 0)
            SearchItem("Сенсорный экран", "Включить/отключить сенсорный экран", 0, 
                      keywords=["тач", "touch", "экран", "дисплей"]),
            SearchItem("Перезагрузка системы", "Перезагрузить компьютер", 0,
                      keywords=["reboot", "restart", "перезапуск"]),
            SearchItem("Очистка Temp файлов", "Очистить временные файлы", 0,
                      keywords=["temp", "временные", "очистка", "cleanup"]),
            SearchItem("COM порты", "Перезапустить COM порты", 0,
                      keywords=["com", "порт", "последовательный"]),
            SearchItem("Службы", "Управление службами Windows", 0,
                      keywords=["services", "служба", "сервис"]),
            SearchItem("Защита Windows", "Отключить защитник и брандмауэр", 0,
                      keywords=["defender", "защитник", "антивирус", "firewall"]),
            SearchItem("Автозагрузка", "Открыть папку автозагрузки", 0,
                      keywords=["startup", "автозапуск"]),
            SearchItem("Панель управления", "Открыть панель управления", 0,
                      keywords=["control panel", "настройки"]),
            SearchItem("Диспетчер печати", "Перезапустить службу печати", 0,
                      keywords=["print", "printer", "spooler", "принтер"]),
            SearchItem("Очередь печати", "Очистить очередь печати", 0,
                      keywords=["print queue", "очередь"]),
            SearchItem("TLS 1.2", "Настроить протокол TLS 1.2", 0,
                      keywords=["ssl", "tls", "шифрование"]),
            SearchItem("RNDIS", "Перезапустить RNDIS устройства", 0,
                      keywords=["usb", "android", "общий доступ"]),
                      
            # iiko функции (вкладка 1)
            SearchItem("Закрыть iikoFront", "Завершить процесс iikoFront.Net", 1,
                      keywords=["iiko", "фронт", "закрыть", "процесс"]),
            SearchItem("Перезапустить iikoFront", "Перезапуск iikoFront.Net", 1,
                      keywords=["iiko", "фронт", "restart", "перезапуск"]),
            SearchItem("Обновить iikoCard", "Загрузить и установить iikoCard", 1,
                      keywords=["iiko", "карта", "card", "обновление"]),
                      
            # Логи (вкладка 2)
            SearchItem("Config.xml", "Открыть конфигурационный файл", 2,
                      keywords=["config", "конфиг", "настройки", "xml"]),
            SearchItem("Cash-server лог", "Просмотр логов кассового сервера", 2,
                      keywords=["cash", "касса", "сервер", "лог"]),
            SearchItem("OnlineMarking лог", "Логи онлайн маркировки", 2,
                      keywords=["marking", "маркировка", "честный знак"]),
            SearchItem("DualConnector лог", "Логи платежного коннектора", 2,
                      keywords=["dual", "connector", "payment", "платеж"]),
            SearchItem("SberbankPlugin лог", "Логи плагина Сбербанка", 2,
                      keywords=["sberbank", "сбербанк", "plugin"]),
            SearchItem("VirtualPrinter лог", "Логи виртуального принтера", 2,
                      keywords=["virtual", "printer", "принтер"]),
            SearchItem("Error лог", "Логи ошибок", 2,
                      keywords=["error", "ошибка", "err"]),
            SearchItem("Transport лог", "Логи транспортного API", 2,
                      keywords=["transport", "api", "транспорт"]),
            SearchItem("Собрать логи", "Создать архив с логами", 2,
                      keywords=["collect", "archive", "архив", "сбор"]),
                      
            # Папки (вкладка 3)
            SearchItem("EntitiesStorage", "Открыть папку EntitiesStorage", 3,
                      keywords=["entities", "storage", "сущности"]),
            SearchItem("PluginConfig", "Открыть папку конфигурации плагинов", 3,
                      keywords=["plugin", "config", "плагин"]),
            SearchItem("Logs папка", "Открыть папку с логами", 3,
                      keywords=["logs", "папка", "директория"]),
                      
            # Сеть (вкладка 4)
            SearchItem("IP конфигурация", "Показать сетевые настройки", 4,
                      keywords=["ip", "ipconfig", "сеть", "network"]),
                      
            # Программы (вкладка 5)
            SearchItem("7-Zip", "Установить архиватор 7-Zip", 5,
                      keywords=["архив", "zip", "rar", "архиватор"]),
            SearchItem("Advanced IP Scanner", "Установить сканер IP адресов", 5,
                      keywords=["scanner", "сканер", "ip", "сеть"]),
            SearchItem("AnyDesk", "Установить программу удаленного доступа", 5,
                      keywords=["remote", "удаленный", "доступ"]),
            SearchItem("Ассистент", "Установить программу Ассистент", 5,
                      keywords=["assistant", "помощник"]),
            SearchItem("Com Port Checker", "Установить проверку COM портов", 5,
                      keywords=["com", "port", "checker", "порт"]),
            SearchItem("Database Net", "Установить работу с базами данных", 5,
                      keywords=["database", "db", "база", "данные"]),
            SearchItem("Notepad++", "Установить текстовый редактор", 5,
                      keywords=["notepad", "editor", "редактор", "текст"]),
            SearchItem("Printer TEST", "Установить тестер принтеров", 5,
                      keywords=["printer", "test", "принтер", "тест"]),
            SearchItem("Rhelper", "Установить помощник удаленного доступа", 5,
                      keywords=["rhelper", "remote", "helper"])
        ]
        
    def perform_search(self):
        query = self.search_input.text().strip()
        
        if not query:
            self.results_list.clear()
            self.hint_label.setText("Начните вводить для поиска функций...")
            self.hint_label.show()
            self.results_list.hide()
            return
            
        self.hint_label.hide()
        self.results_list.show()
        self.results_list.clear()
        
        # Поиск подходящих элементов
        matches = []
        for item in self.search_items:
            if item.matches(query):
                matches.append(item)
                
        # Сортировка по релевантности
        matches.sort(key=lambda x: (
            x.title.lower().startswith(query.lower()),  # Точное начало названия
            query.lower() in x.title.lower(),            # Содержание в названии
            query.lower() in x.description.lower()       # Содержание в описании
        ), reverse=True)
        
        # Добавление результатов
        for item in matches[:10]:  # Максимум 10 результатов
            list_item = QListWidgetItem()
            
            # Определяем название вкладки
            tab_names = ["Система", "iiko", "Логи", "Папки", "Сеть", "Программы"]
            tab_name = tab_names[item.tab_index] if item.tab_index < len(tab_names) else "Неизвестно"
            
            # Форматированный текст
            text = f"🔧 {item.title}\n💭 {item.description}\n📁 Вкладка: {tab_name}"
            list_item.setText(text)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            
            self.results_list.addItem(list_item)
            
        if not matches:
            no_results = QListWidgetItem("🔍 Ничего не найдено")
            no_results.setFlags(Qt.ItemFlag.NoItemFlags)
            self.results_list.addItem(no_results)
            
    def execute_first_result(self):
        """Выполнить первый результат при нажатии Enter"""
        if self.results_list.count() > 0:
            first_item = self.results_list.item(0)
            if first_item:
                self.execute_result(first_item)
                
    def execute_result(self, item):
        """Выполнить выбранный результат"""
        search_item = item.data(Qt.ItemDataRole.UserRole)
        if search_item:
            self.search_activated.emit(search_item.tab_index, search_item.action)
            self.close_search()
            
    def close_search(self):
        """Закрыть поиск"""
        self.search_closed.emit()
        
    def focus_search(self):
        """Установить фокус на поле поиска"""
        self.search_input.setFocus()
        self.search_input.selectAll()
        
    def clear_search(self):
        """Очистить поиск"""
        self.search_input.clear()
        self.results_list.clear()
        self.hint_label.show()
        self.results_list.hide()