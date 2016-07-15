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


class TaskStatusView(APIView):
    """
    Task status tracking

    GET /status?task_id=<celery task id>
    Output: {"status": "", "result": null|""|{}}

    Status PENDING can mean the task hasn't been picked up or doesn't exist
    """
    def _format_output(self, output):
        if isinstance(output, Exception):
            return "{}: {}".format(output.__class__.__name__, output.message)
        elif not isinstance(output, (dict, list, basestring, int, float)):
            return str(output)
        return output

    def get(self, request):
        task_id = request.GET.get('task_id')

        task = AsyncResult(id=task_id)
        data = {'status': task.status,
                'result': self._format_output(task.result)}

        return Response(data)


class ASyncTaskViewMixin(object):
    """
    Kick off an async task and return the task id
    """
    task = NotImplemented

    def get_task_kwargs(self):
        return {}

    def post(self, *args, **kwargs):
        task = self.task.delay(**self.get_task_kwargs())
        return Response(data={"task_id": task.id})
