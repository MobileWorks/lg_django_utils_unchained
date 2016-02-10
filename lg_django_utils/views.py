from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied, \
    NotAuthenticated, NotFound


class ExceptionAPIView(APIView):
    def get(self, request, *args, **kwargs):
        if 'permission' in request.query_params:
            raise PermissionDenied('uh oh, permission denied!')

        if 'validate' in request.query_params:
            raise ValidationError("uh oh, something didn't validate")

        if 'not-authed' in request.query_params:
            raise ValidationError("uh oh, you're not authenticated")

        if 'not-found' in request.query_params:
            raise ValidationError("uh oh, not found")

        raise Exception("uh oh")
