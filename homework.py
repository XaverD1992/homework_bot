import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] - %(message)s'
)
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)


def check_tokens():
    """Проверка наличия всех токенов в переменных окружения."""
    tokens = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'PRACTICUM_TOKEN']
    errors = [token for token in tokens if not globals()[token]]
    if errors:
        logger.critical('Не хватает токена в переменных окружения.')
        sys.exit('Не хватает токена в переменных окружения')


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    logger.info('Начало отправки сообщения')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as error:
        logger.error(f'Ошибка отправки сообщения: {error}')
    logger.debug(f'Бот отправил сообщение: {message}')


def get_api_answer(current_timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    logger.info('Начало обращения к API')
    payload = {'from_date': current_timestamp}
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params=payload,
        )
    except requests.RequestException as error:
        raise ConnectionError(f'Ошибка ответа API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise exceptions.APIResponseStatusCodeException(
            f'Эндпоинт недоступен: '
            f'адрес - {ENDPOINT}, '
            f'текущая дата - {payload}, '
            f'статус ответа - {response.status_code}'
        )
    logger.info('Ответ получен')
    return response.json()


def check_response(response: dict) -> None:
    """Проверяет ответ API на соответствие документации."""
    logger.info('Начало проверки ответа API')
    if not isinstance(response, dict):
        raise TypeError('Ответ не в виде словаря')
    if 'homeworks' not in response:
        raise KeyError('В ответе нету ключа "homeworks"')
    if 'current_date' not in response:
        raise KeyError('В ответе нету ключа "current_date')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Значение в homeworks не является списком')
    logger.info('Проверка ответа API завершена')


def parse_status(homework: dict) -> str:
    """Получение статуса домашней работы из ответа API."""
    logger.info('Начало извелечения статуса работы')
    if 'homework_name' not in homework:
        raise KeyError('Ключ homework_name отсутствует')
    if 'status' not in homework:
        raise KeyError('Ключ status отсутствует')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Непредусмотренное значение -{homework_status}'
                         f'для ключа "status"')
    verdict = HOMEWORK_VERDICTS[homework_status]
    logger.info('Статус извлечен')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_message = None

    while True:
        try:
            logger.debug('Начало итерации')
            response = get_api_answer(current_timestamp)
            check_response(response)
            homeworks = response.get('homeworks')
            if not homeworks:
                logger.info('Статус не изменился')
                continue
            hw_status = parse_status(homeworks[0])
            if hw_status != last_message:
                send_message(bot, hw_status)
                last_message = hw_status
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if last_message != message:
                last_message = message
                send_message(bot, message)
            logger.error(message)
        finally:
            logger.debug('Итерация завершена')
            current_timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
