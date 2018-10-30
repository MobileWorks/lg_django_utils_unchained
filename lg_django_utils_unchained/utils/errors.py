import logging

from django.conf import settings
from raven.contrib.django.raven_compat.models import sentry_exception_handler
from rest_framework.exceptions import ValidationError, PermissionDenied, \
    NotAuthenticated, NotFound
from rest_framework.response import Response
from rest_framework.views import exception_handler


SILENT_DRF_EXCEPTIONS = [
    ValidationError,
    PermissionDenied,
    NotAuthenticated,
    NotFound
]


def custom_exception_handler(exc, context):
    """
    DRF:
    http://www.django-rest-framework.org/api-guide/exceptions/#custom-exception-handling
    Sentry/Raven:
    http://raven.readthedocs.org/en/latest/integrations/django.html#usage
    """
    response = exception_handler(exc, context)

    if not isinstance(exc, tuple(SILENT_DRF_EXCEPTIONS)):
        sentry_exception_handler(request=context['request']._request)

    logging.exception(exc.message, exc_info=exc)

    # throw the error in dev and testing
    if response or settings.ENVIRONMENT not in ['production', 'staging']:
        return response
    return Response({'error': exc.message}, status=500)
