import logging
import os
import sys
import time
from http import HTTPStatus
from xmlrpc.client import Boolean

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
THIRTY_DAYS_TIMESTAMP = 2592000
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(log_handler)


def check_tokens() -> Boolean:
    """Проверка наличия всех токенов в переменных окружения."""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Бот отправил сообщение: {message}')
    except Exception as error:
        logger.error(f'Ошибка отправки сообщения: {error}')


def get_api_answer(old_timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    payload = {'from_date': old_timestamp}
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params=payload,
        )
    except response.status_code != HTTPStatus.OK:
        logger.error('Эндпоинт недоступен')
    if response.status_code != HTTPStatus.OK:
        raise exceptions.APIResponseStatusCodeException('Эндпоинт недоступен')
    return response.json()


def check_response(response: dict) -> dict:
    """Проверяет ответ API на соответствие документации."""
    try:
        homeworks_list = response['homeworks']
    except KeyError as key_error:
        msg = f'Ошибка доступа по ключу homeworks: {key_error}'
        logger.error(msg)
        raise exceptions.CheckResponseException(msg)
    if homeworks_list is None:
        logger.error(msg)
        raise exceptions.CheckResponseException('В ответе API нет списка'
                                                'с домашними работами')
    if not homeworks_list:
        logger.error(msg)
        raise exceptions.CheckResponseException('Список с домашними'
                                                'работами пуст')
    if not isinstance(homeworks_list, list):
        msg = 'В ответе API домашняя работа представлена не списком'
        logger.error(msg)
        raise TypeError(msg)
    return homeworks_list


def parse_status(homework: dict) -> str:
    """Получение статуса домашней работы из ответа API."""
    if 'homework_name' not in homework:
        raise KeyError('Ключ homework_name отсутствует')
    if 'status' not in homework:
        raise KeyError('Ключ status отсутствует')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError(f'{homework_status} отсутствует в словаре verdicts')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствует необходимая переменная среды')
        raise exceptions.MissingRequiredTokenException('Отсутствует'
                                                       'необходимая'
                                                       'переменная среды')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    old_timestamp = int(time.time() - THIRTY_DAYS_TIMESTAMP)
    previous_status = None
    previous_error = None

    while True:
        try:
            response = get_api_answer(old_timestamp)
        except exceptions.IncorrectAPIResponseException as incorrect_response:
            if str(incorrect_response) != previous_error:
                previous_error = str(incorrect_response)
                send_message(bot, incorrect_response)
            logger.error(incorrect_response)
            time.sleep(RETRY_PERIOD)
            continue
        try:
            homeworks = check_response(response)
            hw_status = homeworks[0].get('status')
            if hw_status == previous_status:
                logger.debug('Обновления статуса нет')
            else:
                previous_status = hw_status
                message = parse_status(homeworks[0])
                send_message(bot, message)

            time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if previous_error != str(error):
                previous_error = str(error)
                send_message(bot, message)
            logger.error(message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
