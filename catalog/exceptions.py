from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler

VALIDATION_ERROR_MESSAGE = 'Помилка валідації даних.'


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Операцію неможливо виконати через конфлікт даних.'
    default_code = 'conflict'


def build_error_body(message, details=None):
    body = {'error': str(message)}
    if details is not None:
        body['details'] = details
    return body


def unified_exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        exc = Conflict(
            "Неможливо видалити об'єкт: з ним пов'язані інші записи."
        )

    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        response.data = build_error_body(VALIDATION_ERROR_MESSAGE, exc.detail)
    elif isinstance(exc, APIException):
        response.data = build_error_body(exc.detail)
    else:
        response.data = build_error_body(
            response.data.get('detail', 'Сталася помилка.')
        )
    return response
