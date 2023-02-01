class MissingRequiredTokenException(Exception):
    """Не все переменные окружения доступны."""
    pass


class APIResponseStatusCodeException(Exception):
    """Эндпоинт недоступен."""
    pass


class IncorrectAPIResponseException(Exception):
    """Некорректный API ответ."""
    pass


class CheckResponseException(Exception):
    """Формат ответа API не соответсвует документации."""
    pass


class SendMessageFailure(Exception):
    """Ошибка при отправке сообщения в чат."""
    pass