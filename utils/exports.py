from datetime import datetime
import os
import resource
import types
import uuid

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from celery import states
from django.conf import settings
import smart_open

import unicodecsv as csv


class S3CSVExport(object):
    writer_class = None
    FILENAME_FORMAT = "leadgenius_{model_name}_download_{now}.csv"
    FILENAME_DATETIME_FORMAT = "%Y-%m-%d_%H:%M"

    def __init__(self, queryset):
        self.queryset = queryset
        if os.environ.get('TRACK_CSV_EXPORT_MEMORY'):
            self.track_memory = True
            self.memory_sample_interval = os.environ.get('CSV_EXPORT_MEMORY_SAMPLE_INTERVAL', 500)
            self.sample_memory()
        else:
            self.track_memory = False
        assert self.writer_class, "You must set writer_class on a CSVExport"
        self.writer = self.get_writer()

    def generate_filename(self):
        return self.FILENAME_FORMAT.format(
            model_name=self.queryset.model._meta.verbose_name,
            now=datetime.now().strftime(self.FILENAME_DATETIME_FORMAT)
            )

    def obfuscate_filename(self, filename):
        return "{}/{}".format(uuid.uuid4(), filename)

    def get_writer(self):
        return self.writer_class()

    def get_header_row(self):
        """Return an iterable of headers, or None for no header row"""
        return self.writer.get_header_row()

    def get_data_generator(self):
        """Return a generator where each item in the iterable corresponds to one row in the csv"""
        return (self.writer.get_row(obj) for obj in self.queryset.iterator())

    def get_s3_key(self):
        conn = S3Connection(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY
        )
        bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME_EXPORTS)
        key = Key(bucket)
        return key

    def get_download_url(self, key):
        # make a publicly available url with a short-ish expiration, relying on a random uuid
        # for security by obscurity
        key.make_public()
        url = key.generate_url(expires_in=settings.AWS_EXPORTS_URL_EXPIRATION,  # seconds
            query_auth=False)
        return url

    def sample_memory(self):
        if not hasattr(self, 'mem_usage'):
            self.mem_usage = []  # initialize
        maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self.mem_usage.append(maxrss / 1000000.0)

    def write_to_s3(self, header_row, data_generator):
        key = self.get_s3_key()
        key.key = self.obfuscate_filename(self.generate_filename())
        # https://github.com/RaRe-Technologies/smart_open

        total = self.queryset.count()
        start_time = datetime.now()
        with smart_open.smart_open(key, 'wb') as fout:
            writer = csv.writer(fout)

            if header_row:
                writer.writerow(header_row)

            for row_num, row in enumerate(data_generator):
                if self.track_memory and row_num % self.memory_sample_interval == 0:
                    self.sample_memory()
                status = {
                    "total": total,
                    "processed": row_num,
                    "duration_in_seconds": int((datetime.now() - start_time).total_seconds())
                    }
                if self.task_instance:
                    self.task_instance.update_state(state=states.STARTED, meta=status)
                writer.writerow(row)

        url = self.get_download_url(key)
        return url

    def build_csv_export(self, task_instance=None):
        self.task_instance = task_instance
        header_row = self.get_header_row()
        data_generator = self.get_data_generator()
        # avoid accidentally loading a huge queryset into memory
        assert isinstance(data_generator, types.GeneratorType), \
            "Oops - data_generator must be a generator object to avoid overconsumption of memory"
        download_link = self.write_to_s3(header_row=header_row, data_generator=data_generator)
        result = {
            'success': True,
            'download_link': download_link
            }

        if self.track_memory:
            result.update({"mem_in_MB": self.mem_usage})

        if self.task_instance:
            self.task_instance.update_state(state=states.SUCCESS, meta=result)
        return result


