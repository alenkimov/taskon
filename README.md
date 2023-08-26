# Taskon script
[![Telegram channel](https://img.shields.io/endpoint?url=https://runkit.io/damiankrawczyk/telegram-badge/branches/master?url=https://t.me/cum_insider)](https://t.me/cum_insider)

- [Запуск под Windows](#запуск-под-windows)
- [Запуск под Ubuntu](#запуск-под-ubuntu)
- [Работа со скриптом](#работа-со-скриптом)

Скрипт для прохождения компаний Taskon. Модули:
- Аутентификация и инвайт аккаунта
- Привязка Discord
- Привязка Twitter
- Прохождение компании
- Просмотр результатов компании


## Запуск под Windows
- Установите [Python 3.11](https://www.python.org/downloads/windows/). Не забудьте поставить галочку напротив "Add Python to PATH".
- Установите пакетный менеджер [Poetry](https://python-poetry.org/docs/) вручную по [этой инструкции](https://teletype.in/@alenkimov/poetry).
- Установите MSVC и Пакет SDK для Windows по [этой инструкции](https://teletype.in/@alenkimov/web3-installation-error). Без этого при попытке установить библиотеку web3 будет возникать ошибка "Microsoft Visual C++ 14.0 or greater is required".
- Установите [git](https://git-scm.com/download/win). Это позволит с легкостью получать обновления скрипта командой `git pull`
- Откройте консоль в удобном месте...
  - Склонируйте (или [скачайте](https://github.com/alenkimov/taskon/archive/refs/heads/main.zip)) этот репозиторий:
    ```bash
    git clone https://github.com/AlenKimov/taskon
    ```
  - Перейдите в папку проекта:
    ```bash
    cd taskon
    ```
  - Установите требуемые зависимости следующей командой или запуском файла `INSTALL.bat`:
    ```bash
    poetry install
    ```
  - Запустите скрипт следующей командой или запуском файла `START.bat`:
    ```bash
    poetry run python start.py
    ```


## Запуск под Ubuntu
- Обновите систему:
```bash
sudo apt update && sudo apt upgrade -y
```
- Установите [git](https://git-scm.com/download/linux) и screen:
```bash
sudo apt install screen git -y
```
- Установите Python 3.11 и зависимости для библиотеки web3:
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.11 python3.11-dev build-essential libssl-dev libffi-dev -y
ln -s /usr/bin/python3.11/usr/bin/python
```
- Установите [Poetry](https://python-poetry.org/docs/):
```bash
curl -sSL https://install.python-poetry.org | python -
export PATH="/root/.local/bin:$PATH"
```
- Склонируйте этот репозиторий:
```bash
git clone https://github.com/alenkimov/taskon
```
- Перейдите в папку проекта:
```bash
cd taskon
```
- Установите требуемые библиотеки:
```bash
poetry install
```
- Запустите скрипт:
```bash
poetry run python start.py
```


## Работа со скриптом
После первого запуска в папке проекта появятся новые папки: `input` и `log`,
а в папке `config` появится файл `config.toml`.

### Папка `config`, конфигурация скрипта
Файлы конфигурации (`config.toml`) находятся в папке `config`.

Основной файл конфигурации это `config.toml`. Вот самые важные настройки, о которых стоит знать:
- `HIDE_SECRETS`: Скрывает чувствительные данные. Включено по умолчанию.
- `DEFAULT_INVITE_CODE`: Пригласительный код по умолчанию.
Если при заполнении таблицы опциональное значение `(optional) Invite code`
отсутствует, то будет использован пригласительный код по умолчанию.
- `ANTICAPTCHA_API_KEY`: API ключ [anticaptcha](http://getcaptchasolution.com/tmb2cervod)
- `MAX_TASKS`: Глобальный ограничитель.
От этого ограничителя зависит максимальное количество одновременно выполняемых тасков.
По умолчанию равен 5. Установка большего значения может привести к ошибкам.
- `DELAY_RANGE`: Минимальная и максимальная задержка между аккаунтами на одних и тех же прокси.
По умолчанию от 60 до 120 сек.


### Папка `input`, таблица с данными об аккаунте
В пустой папке `input` создается таблица по умолчанию, содержащая следующие поля для заполнения:
- (required) Proxy
- (required) Private key
- (optional) Invite code
- (optional) Discord token
- (optional) Twitter token
- (auto) Twitter ct0
- (auto) Site token
- (auto) Discord username
- (auto) Twitter username

Поля с тегом `(required)` являются обязательными, в то время как тег `(optional)`
обозначает опциональное поле. Поля с тегом `(auto)` заполняются скриптом автоматически
во время работы.

- Колонки таблицы **можно** менять местами, но **нельзя** переименовывать.
- **Можно** создавать собственные колонки.


### Папка `log`
В папку `log` записывается все, что происходит в консоли.
