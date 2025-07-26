from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from managers.logs_manager import LogsManager

class LogsTab(QWidget):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.logs_manager = LogsManager(self)
        self.logs_manager.log_signal.connect(self.log_signal.emit)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        title = QLabel("Открытие логов")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 500;
                padding-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        buttons_container = QWidget()
        buttons_container.setFixedSize(545, 150)  # Увеличиваем ширину для 5 кнопок
        buttons_container.setStyleSheet("QWidget { background-color: transparent; }")
        
        grid = QGridLayout(buttons_container)
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)
        
        config_button = self.create_button("Config.xml", False)
        config_button.clicked.connect(self.open_config_xml)
        grid.addWidget(config_button, 0, 0)
        
        cash_button = self.create_button("Лог\ncash-server", False)
        cash_button.clicked.connect(lambda: self.open_log("cash-server"))
        grid.addWidget(cash_button, 0, 1)
        
        marking_button = self.create_button("Лог\nOnlineMarking", False)
        marking_button.clicked.connect(lambda: self.open_log("OnlineMarkingVerificationPlugin"))
        grid.addWidget(marking_button, 0, 2)
        
        dual_button = self.create_button("Лог\ndualConnector", False)
        dual_button.clicked.connect(lambda: self.open_log("PaymentSystem.DualConnector"))
        grid.addWidget(dual_button, 0, 3)
        
        alcohol_button = self.create_button("Лог\nAlcoholMarking", False)
        alcohol_button.clicked.connect(lambda: self.open_log("AlcoholMarkingPlugin"))
        grid.addWidget(alcohol_button, 0, 4)
        
        sber_button = self.create_button("Лог\nSberbankPlugin", False)
        sber_button.clicked.connect(lambda: self.open_log("SberbankPlugin"))
        grid.addWidget(sber_button, 1, 0)
        
        printer_button = self.create_button("Лог\nVirtualPrinter", False)
        printer_button.clicked.connect(lambda: self.open_log("virtual-printer"))
        grid.addWidget(printer_button, 1, 1)
        
        error_button = self.create_button("Лог\nError", False)
        error_button.clicked.connect(lambda: self.open_log("error"))
        grid.addWidget(error_button, 1, 2)
        
        transport_button = self.create_button("Лог\nApi.Transport", False)
        transport_button.clicked.connect(lambda: self.open_log("Transport"))
        grid.addWidget(transport_button, 1, 3)
        
        collect_button = self.create_button("Собрать\nлоги", False)
        collect_button.clicked.connect(self.collect_logs)
        collect_button.setStyleSheet("""
            QPushButton {
                background-color: #1e40af;
                border: 1px solid #3b82f6;
                border-radius: 4px;
                color: #3b82f6;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 2px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
                border-color: #60a5fa;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
            }
        """)
        grid.addWidget(collect_button, 1, 4)
        
        layout.addWidget(buttons_container)
        layout.addStretch()
        
    def create_button(self, text, is_active, enabled=True, is_toggle=False):
        button = QPushButton(text)
        button.setFixedSize(105, 45)
        button.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)
        button.setEnabled(enabled)
        self.update_button_style(button, is_active, enabled, is_toggle)
        return button
        
    def update_button_style(self, button, is_active, enabled=True, is_toggle=False):
        if not enabled:
            style = """
                QPushButton {
                    background-color: #0f0f0f;
                    border: 1px solid #1a1a1a;
                    border-radius: 4px;
                    color: #404040;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 4px 2px;
                }
            """
        else:
            style = """
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
            """
        button.setStyleSheet(style)
        
    def open_config_xml(self):
        self.logs_manager.open_config_xml()
        
    def open_log(self, log_type):
        self.logs_manager.open_log_file(log_type)
        
    def collect_logs(self):
        self.logs_manager.collect_logs()