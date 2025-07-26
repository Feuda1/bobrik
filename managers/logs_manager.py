import subprocess
import os
import zipfile
import datetime
import glob
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from config import IIKO_PATHS, SYSTEM_PATHS, LOG_KEYWORDS

class LogsManager(QThread):
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
    def run(self):
        pass
        
    def open_log_file(self, log_type):
        """Открывает лог файл в редакторе"""
        self.log_signal.emit(f"Открываем {log_type}...", "info")
        threading.Thread(target=self._open_log_async, args=(log_type,), daemon=True).start()
        
    def _open_log_async(self, log_type):
        """Открывает лог файл асинхронно"""
        try:
            log_files = self._find_log_files(log_type)
            
            if not log_files:
                self.log_signal.emit(f"Лог файлы {log_type} не найдены", "warning")
                return
                
            latest_file = max(log_files, key=os.path.getmtime)
            
            editor_path = SYSTEM_PATHS['notepad_plus']
            if os.path.exists(editor_path):
                subprocess.Popen([editor_path, latest_file])
                self.log_signal.emit(f"Открыт {log_type} в Notepad++", "success")
            else:
                subprocess.Popen(['notepad', latest_file])
                self.log_signal.emit(f"Открыт {log_type} в Блокноте", "success")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при открытии лога {log_type}: {str(e)}", "error")
            
    def open_config_xml(self):
        """Открывает файл config.xml"""
        self.log_signal.emit("Открываем config.xml...", "info")
        threading.Thread(target=self._open_config_async, daemon=True).start()
        
    def _open_config_async(self):
        """Открывает config.xml асинхронно"""
        try:
            config_path = IIKO_PATHS['config_xml']
            
            if not os.path.exists(config_path):
                self.log_signal.emit("Файл config.xml не найден", "error")
                return
                
            editor_path = SYSTEM_PATHS['notepad_plus']
            if os.path.exists(editor_path):
                subprocess.Popen([editor_path, config_path])
                self.log_signal.emit("Открыт config.xml в Notepad++", "success")
            else:
                subprocess.Popen(['notepad', config_path])
                self.log_signal.emit("Открыт config.xml в Блокноте", "success")
                
        except Exception as e:
            self.log_signal.emit(f"Ошибка при открытии config.xml: {str(e)}", "error")
            
    def collect_logs(self):
        """Собирает логи в архив"""
        try:
            msg = QMessageBox(self.parent)
            msg.setWindowTitle('Сбор логов')
            msg.setText('Включить базу данных в архив?')
            msg.setIcon(QMessageBox.Icon.Question)
            
            with_db_button = msg.addButton('С базой данных', QMessageBox.ButtonRole.YesRole)
            without_db_button = msg.addButton('Только логи', QMessageBox.ButtonRole.NoRole)
            cancel_button = msg.addButton('Отмена', QMessageBox.ButtonRole.RejectRole)
            
            msg.exec()
            
            if msg.clickedButton() == cancel_button:
                self.log_signal.emit("Сбор логов отменен", "info")
                return
                
            include_db = msg.clickedButton() == with_db_button
            
            save_path, _ = QFileDialog.getSaveFileName(
                self.parent,
                'Сохранить архив логов',
                f'iiko_logs_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
                'ZIP файлы (*.zip)'
            )
            
            if not save_path:
                self.log_signal.emit("Сбор логов отменен", "info")
                return
                
            self.log_signal.emit("Начинаем сбор логов...", "info")
            
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                files_added = 0
                
                today_logs = self._get_today_logs()
                
                for log_file in today_logs:
                    try:
                        arcname = os.path.basename(log_file)
                        zipf.write(log_file, arcname)
                        files_added += 1
                        self.log_signal.emit(f"Добавлен: {arcname}", "info")
                    except Exception as e:
                        self.log_signal.emit(f"Ошибка при добавлении {log_file}: {str(e)}", "warning")
                        
                if include_db:
                    db_file = self._get_latest_database()
                    if db_file:
                        try:
                            arcname = os.path.basename(db_file)
                            zipf.write(db_file, arcname)
                            files_added += 1
                            self.log_signal.emit(f"Добавлена база данных: {arcname}", "info")
                        except Exception as e:
                            self.log_signal.emit(f"Ошибка при добавлении БД: {str(e)}", "warning")
                    else:
                        self.log_signal.emit("База данных не найдена", "warning")
                        
            self.log_signal.emit(f"Архив создан: {save_path} ({files_added} файлов)", "success")
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при сборе логов: {str(e)}", "error")
            
    def _find_log_files(self, log_type):
        """Находит лог файлы по типу"""
        try:
            logs_dir = IIKO_PATHS['logs']
            if not os.path.exists(logs_dir):
                return []
                
            log_files = []
            
            if log_type == "cash-server":
                pattern = os.path.join(logs_dir, "*cash-server*.log")
            elif log_type == "virtual-printer":
                pattern = os.path.join(logs_dir, "*virtual-printer*.log")
            elif log_type == "error":
                pattern = os.path.join(logs_dir, "*error*.log")
            else:
                for keyword in LOG_KEYWORDS:
                    if keyword.lower() in log_type.lower():
                        pattern = os.path.join(logs_dir, f"*{keyword}*.log")
                        break
                else:
                    pattern = os.path.join(logs_dir, f"*{log_type}*.log")
                    
            log_files = glob.glob(pattern)
            
            today = datetime.date.today()
            today_files = []
            
            for file_path in log_files:
                try:
                    file_date = datetime.date.fromtimestamp(os.path.getmtime(file_path))
                    if file_date == today:
                        today_files.append(file_path)
                except:
                    continue
                    
            return today_files
            
        except Exception:
            return []
            
    def _get_today_logs(self):
        """Получает все логи за сегодня"""
        try:
            logs_dir = IIKO_PATHS['logs']
            if not os.path.exists(logs_dir):
                return []
                
            today = datetime.date.today()
            today_logs = []
            
            for file in os.listdir(logs_dir):
                if file.endswith('.log'):
                    file_path = os.path.join(logs_dir, file)
                    try:
                        file_date = datetime.date.fromtimestamp(os.path.getmtime(file_path))
                        if file_date == today:
                            today_logs.append(file_path)
                    except:
                        continue
                        
            return today_logs
            
        except Exception:
            return []
            
    def _get_latest_database(self):
        """Получает актуальную базу данных"""
        try:
            db_dir = IIKO_PATHS['entities_db']
            if not os.path.exists(db_dir):
                return None
                
            db_files = []
            
            for ext in ['*.sdf', '*.db']:
                pattern = os.path.join(db_dir, ext)
                db_files.extend(glob.glob(pattern))
                
            if not db_files:
                return None
                
            latest_db = max(db_files, key=os.path.getmtime)
            return latest_db
            
        except Exception:
            return None
            
    def open_folder(self, folder_type):
        """Открывает папку в проводнике"""
        self.log_signal.emit(f"Открываем папку {folder_type}...", "info")
        threading.Thread(target=self._open_folder_async, args=(folder_type,), daemon=True).start()
        
    def _open_folder_async(self, folder_type):
        """Открывает папку асинхронно"""
        try:
            if folder_type == "entities_storage":
                folder_path = IIKO_PATHS['entities_storage']
            elif folder_type == "plugin_configs":
                folder_path = IIKO_PATHS['plugin_configs']
            elif folder_type == "logs":
                folder_path = IIKO_PATHS['logs']
            else:
                self.log_signal.emit(f"Неизвестный тип папки: {folder_type}", "error")
                return
                
            if not os.path.exists(folder_path):
                self.log_signal.emit(f"Папка не существует: {folder_path}", "error")
                return
                
            subprocess.Popen(['explorer', folder_path])
            self.log_signal.emit(f"Открыта папка {folder_type}", "success")
            
        except Exception as e:
            self.log_signal.emit(f"Ошибка при открытии папки {folder_type}: {str(e)}", "error")