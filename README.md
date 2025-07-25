## Что это такое?

**bobrik** - это программа-помощник для работы с POS терминалами и частично с iiko. Она помогает быстро решать типичные проблемы и выполнять рутинные задачи одним кликом.

## Установка и первый запуск

1. **Скачайте** `bobrik.exe` 
2. **Запустите** от имени администратора
3. **При первом запуске** программа автоматически добавится в автозагрузку Windows
4. **Введите PIN-код** `2289` для входа
5. **Программа свернется в трей**

## Как пользоваться

### Вход в программу
- **Двойной клик** по иконке в трее
- **Введите PIN-код**: `2289`

### Поиск функций
- **Нажмите Ctrl+K** или кликните в строку поиска вверху
- **Начните печатать** 
- **Выберите результат** 

---

## Все функции программы

### 🖥️ Система

#### Сенсорный экран
- **Отключить/включить** тачскрин
- **Перезапустить** сенсорный экран

#### Перезагрузка и очистка
- **Перезагрузка системы**
- **Очистка временных файлов**
- **Очистка очереди печати**

#### COM порты и устройства
- **Перезапуск COM портов**
- **Перезапуск диспетчера печати**
- **Управление службами**

#### Безопасность и настройки
- **Отключить защиту Windows**
- **Настройка TLS 1.2**
- **Папка автозагрузки**
- **Панель управления**

#### Сеть
- **Перезапуск RNDIS**

---

### 🏪 iiko

#### Управление программой
- **Закрыть iikoFront**
- **Перезапустить iikoFront**
- **Обновить iikoCard**

---

### 📝 Логи и файлы

#### Просмотр логов
- **Config.xml**
- **Лог кассы**
- **Лог маркировки алкоголя**
- **Лог онлайн маркировки**
- **Лог платежей**
- **Лог Сбербанка**
- **Лог принтера**
- **Лог ошибок**
- **Лог транспорта**

#### Сбор логов
- **Собрать логи**

---

### 📁 Папки

#### Быстрый доступ
- **EntitiesStorage**
- **PluginConfig**
- **Logs**
- **Plugins**

---

### 🌐 Сеть

#### Диагностика и утилиты
- **IP конфигурация**
- **Ping** - проверка соединения с сервером
- **FullDiagnostic** - полная сетевая диагностика с сохранением отчета

---

### 💾 Программы

#### Установка полезных программ
- **7-Zip**
- **Advanced IP Scanner**
- **AnyDesk**
- **Ассистент**
- **Com Port Checker**
- **Database Net**
- **Notepad++**
- **Printer TEST**
- **Rhelper**
- **OrderCheck**
- **CLEAR.bat**
- **iikoTools** (обычная версия)
- **iikoTools SQLite**

---

### 🔌 Плагины

#### Установка плагинов iiko
- **Маркировка алкоголя**
- **Онлайн маркировка**
- **Плагин Сбербанка**
- **Dual Connector**
- **Arrivals**

---

## Новое в версии 1.1.0

### 🌐 Сетевые функции
- **Ping** - простая проверка соединения с отображением результатов в консоли
- **FullDiagnostic** - комплексная диагностика сети с сохранением отчета на рабочий стол

### 🛠️ Утилиты iiko
- **iikoTools** - установка основной версии
- **iikoTools SQLite** - установка SQLite версии
- **Лог AlcoholMarking** - добавлен в раздел логов

### 📦 Программы
- **CLEAR.bat** - утилита для очистки iiko
- Улучшенная установка с сохранением на рабочий стол

---

## Горячие клавиши

- **Ctrl+K** - открыть поиск
- **Enter** - выполнить первый результат поиска
- **Escape** - закрыть поиск

---

## Автозагрузка

При первом запуске программа автоматически:
- Добавляется в автозагрузку Windows
- Будет запускаться при включении компьютера
- Работает в фоне (в трее)

---

## Права администратора

Программа **требует права администратора** для полной работы:
- Управления службами
- Работы с реестром
- Управления устройствами
- Установки программ
- Сетевой диагностики

---

## Поддержка и обновления

### Автоматические обновления
- Кнопка **🔄** в правом верхнем углу
- Проверяет новые версии на GitHub
- Автоматически скачивает и устанавливает

---

## Возможные проблемы

### Забыл PIN-код
- PIN-код: `2289`

### Программа не добавилась в автозагрузку
- Удалите папку `%APPDATA%\bobrik`
- Перезапустите программу от имени администратора

### Как удалить из автозагрузки
- Откройте `regedit.exe`
- Идите в `HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run`
- Удалите запись `bobrik`

### Проблемы с сетевой диагностикой
- Убедитесь, что программа запущена от имени администратора
- Проверьте подключение к интернету
- Для FullDiagnostic требуются права администратора

---

## Системные требования

- **ОС**: Windows 7/10/11
- **Права**: Администратор (рекомендуется)
- **Место**: ~50 МБ
- **RAM**: ~40-100 МБ в работе
- **Сеть**: Для автообновлений и загрузки программ

---

*Версия документации: 1.1.4*
