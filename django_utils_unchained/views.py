from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied, \
    NotAuthenticated, NotFound


class ExceptionAPIView(APIView):
    def get(self, request, *args, **kwargs):
        if request.query_params.get('permission'):
            raise PermissionDenied('uh oh, permission denied!')

        if request.query_params.get('validate'):
            raise ValidationError("uh oh, something didn't validate")

        if request.query_params.get('not-authed'):
            raise ValidationError("uh oh, you're not authenticated")

        if request.query_params.get('not-found'):
            raise ValidationError("uh oh, not found")

        raise Exception("uh oh")
