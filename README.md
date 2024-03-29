# Homework Bot

## Описание

Телеграм-бот для отслеживания статуса проверки домашней работы на Яндекс.Практикум. Присылает сообщения, когда статус изменен - взято в проверку, есть замечания, зачтено.
## Стек технологий:  


Python 3.7  
python-dotenv 0.19.0  
python-telegram-bot 13.7 

## Установка:

### Локальный запуск проекта

1. Клонируйте репозиторий:
```
git clone git@github.com:AbbadonAA/homework_bot.git
```
2. Создайте и активируйте виртуальное окружение:
```
python3 -m venv venv
source venv/bin/activate
```
3. Установите зависимости:
```
pip install -r requirements.txt
```
4. При помощи @BotFather в Telegram создайте нового бота и получите API TOKEN
5. Получите токен сервиса Практикум.Домашка (PR TOKEN) по адресу:
   
   https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a
6. При помощи @userinfobot получите (команда - "me") TELEGRAM CHAT ID
7. В директории /infra создайте файл .env со следующим содержанием:
```
PR_TOKEN=<PR TOKEN>
MY_TOKEN=<API TOKEN>
CHAT_ID=<TELEGRAM CHAT ID>
```
8. В файле homework.py внесите изменения:
```
# path = r'C:\Dev\homework_bot\infra\.env' - раскомментируйте строку
# load_dotenv(path) - раскомментируйте строку
load_dotenv() - закомментируйте строку
```

9. После внесения изменений в корневой директории выполните команду:

```
python homework.py
```
10. Бот запущен и отслеживает изменения статуса проверки домашней работы.

### Запуск на сервере (необходим Docker):

1. Создайте директорию /infra
2. Скопируйте в директорию /infra файл docker-compose.yaml
3. Создайте в директории /infra файл .env со следующим содержанием:
```
PR_TOKEN=<PR TOKEN>
MY_TOKEN=<API TOKEN>
CHAT_ID=<TELEGRAM CHAT ID>
```
4. Находясь в директории /infra с файлом docker-compose.yaml выполните команду:
```
sudo docker-compose up -d
```
5. Docker-контейнер с ботом запущен, бот отслеживание изменения статуса проверки домашней работы.


### Автор
Суворов Владислав
