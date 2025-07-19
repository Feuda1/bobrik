from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QLabel, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

class SearchItem:
    def __init__(self, title, description, tab_index, action=None, keywords=None, category="", button_text=None):
        self.title = title
        self.description = description
        self.tab_index = tab_index
        self.action = action
        self.keywords = keywords or []
        self.category = category
        self.button_text = button_text  # Текст кнопки для подсветки
        
    def matches(self, query):
        query = query.lower()
        search_targets = [
            self.title.lower(),
            self.description.lower(),
            self.category.lower()
        ] + [keyword.lower() for keyword in self.keywords]
        
        return any(query in target for target in search_targets)

    def get_relevance_score(self, query):
        query = query.lower()
        score = 0
        
        if query == self.title.lower():
            score += 1000
        elif self.title.lower().startswith(query):
            score += 500
        elif query in self.title.lower():
            score += 200
        
        for keyword in self.keywords:
            if query == keyword.lower():
                score += 300
            elif keyword.lower().startswith(query):
                score += 150
            elif query in keyword.lower():
                score += 50
        
        if query in self.description.lower():
            score += 30
            
        return score

class DropdownSearchWidget(QFrame):
    search_activated = pyqtSignal(int, object)
    search_closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_items = []
        self.is_visible = False
        self._last_selected_item = None  # Запоминаем последний выбранный элемент
        self.init_ui()
        self.index_all_items()
        
    def init_ui(self):
        self.setFixedSize(350, 400)
        self.setStyleSheet("""
            QFrame {
                background-color: #141414;
                border: 1px solid #3b82f6;
                border-radius: 8px;
            }
        """)
        
        # Тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)
        
        # Список результатов
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.execute_result)
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
                font-size: 12px;
            }
            QListWidget::item {
                background-color: transparent;
                border-bottom: 1px solid #1a1a1a;
                padding: 10px 8px;
                min-height: 40px;
                border-radius: 4px;
                margin: 1px;
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
        self.hint_label = QLabel("Начните вводить для поиска...")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 12px;
                padding: 20px;
                background-color: transparent;
            }
        """)
        layout.addWidget(self.hint_label)
        
        self.hide()
        
    def index_all_items(self):
        """Расширенное индексирование всех функций"""
        self.search_items = [
            # === СИСТЕМНЫЕ ФУНКЦИИ ===
            SearchItem("Сенсорный экран", "Включить/отключить тачскрин", 0, 
                      keywords=["тач", "touch", "экран", "дисплей", "сенсор", "touchscreen", 
                               "тачскрин", "касание", "палец", "finger", "включить", "отключить"],
                      category="система", button_text="Сенсорный\nэкран"),
            
            SearchItem("Перезагрузка", "Перезагрузить компьютер", 0,
                      keywords=["reboot", "restart", "перезапуск", "рестарт", "перезагрузка",
                               "выключить", "включить", "система", "компьютер", "пк"],
                      category="система", button_text="Перезагрузка\nсистемы"),
            
            SearchItem("Очистка", "Очистить временные файлы", 0,
                      keywords=["temp", "временные", "очистка", "cleanup", "clear", "clean",
                               "кэш", "cache", "мусор", "файлы", "освободить", "место"],
                      category="система", button_text="Очистка\nTemp файлов"),
            
            SearchItem("COM порты", "Перезапустить COM порты", 0,
                      keywords=["com", "порт", "последовательный", "serial", "port", "rs232",
                               "usb", "устройство", "принтер", "сканер", "эквайринг"],
                      category="система", button_text="Перезапуск\nCOM портов"),
            
            SearchItem("Службы", "Управление службами Windows", 0,
                      keywords=["services", "служба", "сервис", "service", "процесс", "демон"],
                      category="система", button_text="Управление\nслужбами"),
            
            SearchItem("Защитник", "Отключить защитник Windows", 0,
                      keywords=["defender", "защитник", "антивирус", "firewall", "брандмауэр",
                               "безопасность", "windows", "отключить"],
                      category="безопасность", button_text="Отключить\nзащиту"),
            
            SearchItem("Автозагрузка", "Папка автозагрузки", 0,
                      keywords=["startup", "автозапуск", "загрузка", "старт", "boot"],
                      category="система", button_text="Папка\nавтозагрузки"),
            
            SearchItem("Панель управления", "Открыть панель управления", 0,
                      keywords=["control panel", "настройки", "settings", "конфигурация"],
                      category="система", button_text="Панель\nуправления"),
            
            SearchItem("Принтер", "Перезапуск службы печати", 0,
                      keywords=["print", "printer", "spooler", "принтер", "печать", "служба"],
                      category="печать", button_text="Перезапуск\nдисп. печати"),
            
            SearchItem("Очередь печати", "Очистить очередь печати", 0,
                      keywords=["print queue", "очередь", "printer", "печать", "задания"],
                      category="печать", button_text="Очистка\nочереди печати"),
            
            SearchItem("TLS", "Настроить протокол TLS 1.2", 0,
                      keywords=["ssl", "tls", "шифрование", "протокол", "безопасность"],
                      category="сеть", button_text="Настройка\nTLS 1.2"),
            
            SearchItem("RNDIS", "Перезапустить RNDIS", 0,
                      keywords=["usb", "android", "общий доступ", "интернет", "модем"],
                      category="сеть", button_text="Перезапуск\nRNDIS"),
                      
            # === ФУНКЦИИ IIKO ===
            SearchItem("Закрыть iiko", "Завершить процесс iikoFront", 1,
                      keywords=["iiko", "фронт", "закрыть", "процесс", "завершить", "kill"],
                      category="iiko", button_text="Закрыть\niikoFront"),
            
            SearchItem("Перезапуск iiko", "Перезапустить iikoFront", 1,
                      keywords=["iiko", "фронт", "restart", "перезапуск", "запустить"],
                      category="iiko", button_text="Перезапустить\niikoFront"),
            
            SearchItem("iikoCard", "Обновить iikoCard", 1,
                      keywords=["iiko", "карта", "card", "обновление", "установка"],
                      category="iiko", button_text="Обновить\niikoCard"),
                      
            # === ЛОГИ ===
            SearchItem("Конфиг", "Открыть config.xml", 2,
                      keywords=["config", "конфиг", "настройки", "xml", "файл"],
                      category="файлы", button_text="Config.xml"),
            
            SearchItem("Лог кассы", "Лог кассового сервера", 2,
                      keywords=["cash", "касса", "сервер", "лог", "log"],
                      category="логи", button_text="Лог\ncash-server"),
            
            SearchItem("Маркировка", "Лог онлайн маркировки", 2,
                      keywords=["marking", "маркировка", "честный знак", "online"],
                      category="логи", button_text="Лог\nOnlineMarking"),
            
            SearchItem("Платежи", "Лог платежного коннектора", 2,
                      keywords=["dual", "connector", "payment", "платеж", "эквайринг"],
                      category="логи", button_text="Лог\ndualConnector"),
            
            SearchItem("Сбербанк", "Лог плагина Сбербанка", 2,
                      keywords=["sberbank", "сбербанк", "plugin", "плагин"],
                      category="логи", button_text="Лог\nSberbankPlugin"),
            
            SearchItem("Виртуальный принтер", "Лог виртуального принтера", 2,
                      keywords=["virtual", "printer", "принтер", "виртуальный"],
                      category="логи", button_text="Лог\nVirtualPrinter"),
            
            SearchItem("Ошибки", "Лог ошибок", 2,
                      keywords=["error", "ошибка", "err", "exception"],
                      category="логи", button_text="Лог\nError"),
            
            SearchItem("Транспорт", "Лог транспортного API", 2,
                      keywords=["transport", "api", "транспорт", "доставка"],
                      category="логи", button_text="Лог\nApi.Transport"),
            
            SearchItem("Архив логов", "Собрать логи в архив", 2,
                      keywords=["collect", "archive", "архив", "сбор", "zip"],
                      category="логи", button_text="Собрать\nлоги"),
                      
            # === ПАПКИ ===
            SearchItem("База данных", "Папка EntitiesStorage", 3,
                      keywords=["entities", "storage", "сущности", "база", "данные"],
                      category="папки", button_text="EntitiesStorage"),
            
            SearchItem("Плагины", "Папка PluginConfig", 3,
                      keywords=["plugin", "config", "плагин", "конфигурация"],
                      category="папки", button_text="PluginConfig"),
            
            SearchItem("Папка логов", "Открыть папку логов", 3,
                      keywords=["logs", "папка", "директория", "folder"],
                      category="папки", button_text="Logs"),
                      
            # === СЕТЬ ===
            SearchItem("IP адрес", "Показать IP конфигурацию", 4,
                      keywords=["ip", "ipconfig", "сеть", "network", "адрес"],
                      category="сеть", button_text="IP\nконфигурация"),
                      
            # === ПРОГРАММЫ ===
            SearchItem("7-Zip", "Архиватор 7-Zip", 5,
                      keywords=["архив", "zip", "rar", "архиватор", "7z"],
                      category="программы", button_text="7-Zip"),
            
            SearchItem("Сканер IP", "Advanced IP Scanner", 5,
                      keywords=["scanner", "сканер", "ip", "сеть", "network"],
                      category="программы", button_text="Advanced IP Scanner"),
            
            SearchItem("Удаленный доступ", "AnyDesk", 5,
                      keywords=["remote", "удаленный", "доступ", "anydesk"],
                      category="программы", button_text="AnyDesk"),
            
            SearchItem("Ассистент", "Программа Ассистент", 5,
                      keywords=["assistant", "помощник", "ассистент"],
                      category="программы", button_text="Ассистент"),
            
            SearchItem("Тестер портов", "Com Port Checker", 5,
                      keywords=["com", "port", "checker", "порт", "тест"],
                      category="программы", button_text="Com Port Checker"),
            
            SearchItem("База данных", "Database Net", 5,
                      keywords=["database", "db", "база", "данные", "sql"],
                      category="программы", button_text="Database Net"),
            
            SearchItem("Редактор", "Notepad++ редактор", 5,
                      keywords=["notepad", "editor", "редактор", "текст"],
                      category="программы", button_text="Notepad++"),
            
            SearchItem("Тест принтера", "Printer TEST", 5,
                      keywords=["printer", "test", "принтер", "тест"],
                      category="программы", button_text="Printer TEST V3.1C"),
            
            SearchItem("Помощник доступа", "Rhelper", 5,
                      keywords=["rhelper", "remote", "helper", "помощник"],
                      category="программы", button_text="Rhelper")
        ]
        
    def perform_search(self, query):
        query = query.strip()
        
        if not query:
            self.show_hint()
            return
            
        self.hide_hint()
        self.results_list.clear()
        
        # Поиск и сортировка
        matches = []
        for item in self.search_items:
            if item.matches(query):
                relevance = item.get_relevance_score(query)
                matches.append((item, relevance))
                
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Добавление результатов (максимум 6)
        for item, _ in matches[:6]:
            list_item = QListWidgetItem()
            text = f"{item.title}\n{item.description}"
            list_item.setText(text)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.results_list.addItem(list_item)
            
        if not matches:
            no_results = QListWidgetItem("Ничего не найдено")
            no_results.setFlags(Qt.ItemFlag.NoItemFlags)
            self.results_list.addItem(no_results)
            
    def show_hint(self):
        """Показать подсказку"""
        self.results_list.hide()
        self.hint_label.show()
        
    def hide_hint(self):
        """Скрыть подсказку"""
        self.hint_label.hide()
        self.results_list.show()
        
    def execute_first_result(self):
        """Выполнить первый результат"""
        if self.results_list.count() > 0:
            first_item = self.results_list.item(0)
            if first_item and first_item.flags() & Qt.ItemFlag.ItemIsEnabled:
                # Запоминаем первый элемент как выбранный
                search_item = first_item.data(Qt.ItemDataRole.UserRole)
                if search_item:
                    self._last_selected_item = search_item
                self.execute_result(first_item)
                
    def execute_result(self, item):
        """Выполнить выбранный результат"""
        search_item = item.data(Qt.ItemDataRole.UserRole)
        if search_item:
            # Запоминаем последний выбранный элемент
            self._last_selected_item = search_item
            self.search_activated.emit(search_item.tab_index, search_item.action)
            self.hide_dropdown()
            
    def show_dropdown(self, x, y):
        """Показать выпадающее меню"""
        if not self.is_visible:
            # Позиционируем точно под строкой поиска
            target_x = x
            target_y = y
            target_width = 350
            target_height = 400
            
            # Проверяем, не выходит ли за границы родительского виджета
            if self.parent():
                parent_rect = self.parent().rect()
                if target_x + target_width > parent_rect.right():
                    target_x = parent_rect.right() - target_width - 10
                if target_y + target_height > parent_rect.bottom():
                    target_y = y - target_height - 5  # Показать над строкой поиска
            
            # Устанавливаем позицию и показываем
            self.setGeometry(target_x, target_y, target_width, target_height)
            self.show()
            self.is_visible = True
            
    def hide_dropdown(self):
        """Скрыть выпадающее меню"""
        if self.is_visible:
            self.hide()
            self.is_visible = False
            self.results_list.clear()
            self.show_hint()
            self.search_closed.emit()
            
    def clear_search(self):
        """Очистить поиск"""
        self.results_list.clear()
        self.show_hint()