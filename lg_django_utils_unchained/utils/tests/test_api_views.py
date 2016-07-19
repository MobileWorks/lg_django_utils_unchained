from django.core.urlresolvers import reverse
from rest_framework.status import HTTP_200_OK

from lg_django_utils_unchained.testing.test_project.celery import app
from lg_django_utils_unchained.utils.testing import NiceAPITestCase


@app.task
def my_task():
    pass

class TaskStatusViewTests(NiceAPITestCase):
    def test_task_status_view(self):
        task = my_task.delay()
        url = reverse('task_status') + '?task_id={}'.format(task.id)
        resp = self.client.get(url)
        self.assertStatusCode(resp, HTTP_200_OK)
        self.assert_(resp.data['status'])
        self.assert_(resp.data['result'])
