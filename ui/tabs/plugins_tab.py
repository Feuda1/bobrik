from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGridLayout, QScrollArea, QLineEdit, QMessageBox, QComboBox,
                             QProgressBar, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
import subprocess
import sys
import os
import tempfile
import shutil
import zipfile
import re
from urllib.parse import urljoin, unquote

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUIREMENTS = True
except ImportError:
    HAS_REQUIREMENTS = False

class PluginParser(QThread):
    plugin_found = pyqtSignal(str, list)  # name, versions (убираем description)
    parsing_finished = pyqtSignal()
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, plugins_config):
        super().__init__()
        self.plugins_config = plugins_config
        
    def run(self):
        if not HAS_REQUIREMENTS:
            self.log_signal.emit("Требуются библиотеки: pip install requests beautifulsoup4", "error")
            return
            
        for plugin_name, plugin_url in self.plugins_config.items():
            try:
                self.log_signal.emit(f"Парсинг {plugin_name}...", "info")
                versions = self.parse_plugin_versions(plugin_url)
                if versions:
                    self.plugin_found.emit(plugin_name, versions)
                    self.log_signal.emit(f"Найдено {len(versions)} версий для {plugin_name}", "success")
                else:
                    self.log_signal.emit(f"Версии не найдены для {plugin_name}", "warning")
            except Exception as e:
                self.log_signal.emit(f"Ошибка парсинга {plugin_name}: {str(e)}", "error")
                
        self.parsing_finished.emit()
        
    def parse_plugin_versions(self, plugin_url):
        """Парсит доступные версии плагина"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(plugin_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            versions = []
            
            # Ищем ссылки на архивы (.zip)
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.zip'):
                    # Получаем полную ссылку
                    full_url = urljoin(plugin_url, href)
                    # Извлекаем название версии из имени файла
                    filename = unquote(os.path.basename(href))
                    version_name = filename.replace('.zip', '')
                    
                    versions.append({
                        'name': version_name,
                        'url': full_url,
                        'filename': filename
                    })
            
            # Сортируем версии (новые сверху)
            versions.sort(key=lambda x: x['name'], reverse=True)
            return versions
            
        except Exception as e:
            raise Exception(f"Ошибка парсинга: {str(e)}")

class PluginDownloader(QThread):
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str, bool)  # path, success
    
    def __init__(self, plugin_name, version_info):
        super().__init__()
        self.plugin_name = plugin_name
        self.version_info = version_info
        
    def run(self):
        try:
            if not HAS_REQUIREMENTS:
                self.log_signal.emit("Требуются библиотеки requests и beautifulsoup4", "error")
                self.finished_signal.emit("", False)
                return
                
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            file_path = os.path.join(downloads_path, self.version_info['filename'])
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            self.log_signal.emit(f"Загрузка {self.plugin_name} {self.version_info['name']}...", "info")
            
            response = requests.get(self.version_info['url'], stream=True, headers=headers, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_progress = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = min(90, int((downloaded / total_size) * 90))
                            if progress >= last_progress + 10:
                                self.progress_signal.emit(progress)
                                last_progress = progress
            
            self.progress_signal.emit(100)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.log_signal.emit(f"Загрузка завершена ({file_size_mb:.1f} МБ)", "success")
            
            # Разархивируем
            self.extract_plugin(file_path)
            
            self.finished_signal.emit(file_path, True)
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка загрузки: {str(e)}", "error")
            self.finished_signal.emit("", False)
    
    def extract_plugin(self, zip_path):
        """Извлекает плагин и снимает блокировку"""
        try:
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            extract_dir = os.path.join(downloads_path, f"{self.plugin_name}_{self.version_info['name']}")
            
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            
            os.makedirs(extract_dir)
            
            # Извлекаем архив
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            self.log_signal.emit(f"Архив извлечен в {extract_dir}", "info")
            
            # Снимаем блокировку с всех файлов
            self.unblock_files(extract_dir)
            
            # Удаляем архив
            os.remove(zip_path)
            
            # Открываем папку
            subprocess.Popen(['explorer', extract_dir])
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка извлечения: {str(e)}", "error")
    
    def unblock_files(self, directory):
        """Снимает блокировку Windows с файлов"""
        try:
            unblocked_count = 0
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Снимаем атрибут блокировки через PowerShell
                        cmd = f'powershell -Command "Unblock-File -Path \'{file_path}\'"'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        if result.returncode == 0:
                            unblocked_count += 1
                    except Exception:
                        continue
            
            if unblocked_count > 0:
                self.log_signal.emit(f"Снята блокировка с {unblocked_count} файлов", "success")
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка снятия блокировки: {str(e)}", "warning")

class PluginsTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        
        # Конфигурация плагинов
        self.plugins_config = {
            'AlcoholMarkingPlugin': 'https://rapid.iiko.ru/plugins/AlcoholMarkingPlugin/',
            'OnlineMarkingVerification': 'https://rapid.iiko.ru/plugins/Resto%20OnlineMarkingVerification/',
            'Sberbank': 'https://rapid.iiko.ru/plugins/Smart%20Sberbank/',
            'DualConnector': 'https://rapid.iiko.ru/plugins/Resto.Front.Api.PaymentSystem.DualConnector/',
            'Arrivals': 'https://rapid.iiko.ru/plugins/Arrivals/'
        }
        
        self.plugins_data = {}
        self.parser = None
        self.downloader = None
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        title = QLabel("Плагины iiko")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 500;
                padding-bottom: 5px;
            }
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Кнопка обновления списка
        self.refresh_button = QPushButton("🔄 Обновить список")
        self.refresh_button.setFixedSize(140, 35)
        self.refresh_button.clicked.connect(self.refresh_plugins_list)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #1e40af;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                color: #3b82f6;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
                border-color: #60a5fa;
                color: #60a5fa;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
            }
        """)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Поиск плагинов
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск плагинов...")
        self.search_edit.setFixedHeight(35)
        self.search_edit.textChanged.connect(self.filter_plugins)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        layout.addWidget(self.search_edit)
        
        # Скроллируемая область с плагинами
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
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
        """)
        
        self.content_widget = QWidget()
        self.plugins_layout = QVBoxLayout(self.content_widget)
        self.plugins_layout.setSpacing(10)
        self.plugins_layout.setContentsMargins(10, 10, 10, 10)
        self.plugins_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Сообщение о состоянии
        self.status_label = QLabel("Нажмите 'Обновить список' для загрузки доступных плагинов")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 14px;
                padding: 40px;
                background-color: #0f0f0f;
                border-radius: 8px;
                border: 1px solid #2a2a2a;
            }
        """)
        self.plugins_layout.addWidget(self.status_label)
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
        
        # Проверяем зависимости
        if not HAS_REQUIREMENTS:
            self.show_requirements_message()
    
    def show_requirements_message(self):
        """Показывает сообщение о необходимых зависимостях"""
        self.status_label.setText("""
        ⚠️ Для работы с плагинами требуются дополнительные библиотеки:
        
        pip install requests beautifulsoup4
        
        Установите их и перезапустите программу.
        """)
        self.refresh_button.setEnabled(False)
    
    def refresh_plugins_list(self):
        """Обновляет список доступных плагинов"""
        if not HAS_REQUIREMENTS:
            self.log_signal.emit("Установите требуемые библиотеки: pip install requests beautifulsoup4", "error")
            return
        
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("⏳ Загрузка...")
        
        self.status_label.setText("Загрузка списка плагинов...")
        self.plugins_data.clear()
        
        # Очищаем текущий список
        for i in reversed(range(self.plugins_layout.count())):
            child = self.plugins_layout.itemAt(i).widget()
            if child and child != self.status_label:
                child.setParent(None)
        
        # Запускаем парсер
        self.parser = PluginParser(self.plugins_config)
        self.parser.plugin_found.connect(self.on_plugin_found)
        self.parser.parsing_finished.connect(self.on_parsing_finished)
        self.parser.log_signal.connect(self.log_signal.emit)
        self.parser.start()
    
    def on_plugin_found(self, plugin_name, versions):
        """Обрабатывает найденный плагин"""
        self.plugins_data[plugin_name] = {
            'versions': versions
        }
        self.create_plugin_widget(plugin_name, "", versions)  # Пустое описание
    
    def on_parsing_finished(self):
        """Завершение парсинга"""
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("🔄 Обновить список")
        
        if self.plugins_data:
            self.status_label.hide()
            self.log_signal.emit(f"Загружено {len(self.plugins_data)} плагинов", "success")
        else:
            self.status_label.setText("Плагины не найдены. Проверьте подключение к интернету.")
    
    def create_plugin_widget(self, plugin_name, description, versions):
        """Создает упрощенный виджет для плагина"""
        plugin_frame = QWidget()
        plugin_frame.setFixedHeight(60)  # Фиксированная высота
        plugin_frame.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
            }
        """)
        
        layout = QHBoxLayout(plugin_frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # Название плагина
        name_label = QLabel(plugin_name)
        name_label.setFixedWidth(200)  # Фиксированная ширина
        name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        layout.addWidget(name_label)
        
        # Выбор версии
        version_combo = QComboBox()
        version_combo.setFixedSize(200, 35)  # Фиксированный размер
        version_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Предотвращаем прокрутку колесом
        for version in versions:
            version_combo.addItem(version['name'], version)
        
        version_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 10px;
                color: #e0e0e0;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #4a4a4a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #808080;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                selection-background-color: #3b82f6;
                color: #e0e0e0;
            }
        """)
        
        # Отключаем прокрутку колесом для комбобокса
        version_combo.wheelEvent = lambda event: None
        
        layout.addWidget(version_combo)
        
        layout.addStretch()
        
        # Кнопка установки
        install_button = QPushButton("Установить")
        install_button.setFixedSize(120, 35)  # Увеличиваем ширину
        install_button.clicked.connect(
            lambda: self.install_plugin(plugin_name, version_combo.currentData())
        )
        install_button.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                border: 1px solid #10b981;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #047857;
                border-color: #34d399;
            }
            QPushButton:pressed {
                background-color: #065f46;
            }
        """)
        layout.addWidget(install_button)
        
        # Скрываем статус и добавляем плагин
        if self.status_label.isVisible():
            self.status_label.hide()
        
        self.plugins_layout.addWidget(plugin_frame)
    
    def filter_plugins(self):
        """Фильтрует плагины по поиску"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.plugins_layout.count()):
            widget = self.plugins_layout.itemAt(i).widget()
            if widget and widget != self.status_label:
                # Ищем название плагина в виджете
                name_labels = widget.findChildren(QLabel)
                if name_labels:
                    plugin_name = name_labels[0].text().lower()
                    widget.setVisible(search_text in plugin_name)
    
    def install_plugin(self, plugin_name, version_info):
        """Устанавливает выбранный плагин"""
        if not version_info:
            self.log_signal.emit("Версия не выбрана", "error")
            return
        
        msg = QMessageBox(self)
        msg.setWindowTitle('Установка плагина')
        msg.setText(f'Установить {plugin_name} версии {version_info["name"]}?\n\nПлагин будет загружен и извлечен в папку Загрузки.')
        msg.setIcon(QMessageBox.Icon.Question)
        
        yes_button = msg.addButton('Установить', QMessageBox.ButtonRole.YesRole)
        no_button = msg.addButton('Отмена', QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(yes_button)
        
        msg.exec()
        
        if msg.clickedButton() == yes_button:
            self.download_plugin(plugin_name, version_info)
    
    def download_plugin(self, plugin_name, version_info):
        """Загружает и устанавливает плагин"""
        self.log_signal.emit(f"Начинается установка {plugin_name}...", "info")
        
        self.downloader = PluginDownloader(plugin_name, version_info)
        self.downloader.log_signal.connect(self.log_signal.emit)
        self.downloader.finished_signal.connect(self.on_plugin_installed)
        self.downloader.start()
    
    def on_plugin_installed(self, file_path, success):
        """Обрабатывает результат установки плагина"""
        if success:
            self.log_signal.emit("Плагин успешно установлен и разблокирован", "success")
        else:
            self.log_signal.emit("Ошибка установки плагина", "error")