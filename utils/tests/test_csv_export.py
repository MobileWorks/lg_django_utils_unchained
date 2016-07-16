from __future__ import absolute_import

from testing.test_project.celery import app
from django.test.testcases import TestCase
import requests

from utils.exports import S3CSVExport
from utils.formatters import CSVFormatter
from testing.test_app.models import TestModel


class TestCSVFormatter(CSVFormatter):
    headers = ['Field 1', 'Field 2']
    fields = ['field1', 'field2']


class TestCSVExport(S3CSVExport):
    writer_class = TestCSVFormatter


@app.task(bind=True)
def build_test_csv_export(self, queryset):
    return TestCSVExport(queryset).build_csv_export(task_instance=self)


class CSVExportTestCase(TestCase):
    def test_csv_export(self):
        # GIVEN a CSV export class
        # WHEN I build a csv export on S3 using that class
        test_instance1 = TestModel.objects.create(field1='foo')
        test_instance2 = TestModel.objects.create(field1='bar')
        queryset = TestModel.objects.all().order_by('id')
        task = build_test_csv_export.delay(queryset=queryset)
        url = task.result['download_link']
        # THEN I can download that csv
        csv_file = requests.get(url)
        csv_iter = csv_file.iter_lines()
        # AND verify the header and data matches the fields I
        # specified from the model
        headers = csv_iter.next()
        expected_headers = ','.join(["{}".format(header) for header in TestCSVFormatter.headers])
        self.assertEqual(headers, expected_headers)

        for model_instance in [test_instance1, test_instance2]:
            instance_row = csv_iter.next()
            instance_expected_row = ','.join(
                ["{}".format(getattr(model_instance, field)) for field in TestCSVFormatter.fields]
                )
            self.assertEqual(instance_row, instance_expected_row)
