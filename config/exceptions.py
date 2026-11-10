from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.views import exception_handler

VALIDATION_ERROR_MESSAGE = 'Помилка валідації'
AUTH_REQUIRED_MESSAGE = 'Потрібна авторизація'
PERMISSION_DENIED_MESSAGE = 'Недостатньо прав'


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Операцію неможливо виконати через конфлікт даних.'
    default_code = 'conflict'


class Unauthorized(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = AUTH_REQUIRED_MESSAGE
    default_code = 'unauthorized'
    auth_header = 'Bearer realm="api"'


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
        body = build_error_body(VALIDATION_ERROR_MESSAGE, exc.detail)
    elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        body = build_error_body(AUTH_REQUIRED_MESSAGE)
    elif isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
        body = build_error_body(PERMISSION_DENIED_MESSAGE)
    elif isinstance(exc, APIException):
        body = build_error_body(exc.detail)
    else:
        body = build_error_body(
            response.data.get('detail', 'Сталася помилка.')
        )
    response.data = body
    return response
