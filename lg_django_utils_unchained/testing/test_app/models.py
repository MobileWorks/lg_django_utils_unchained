from django.db import models


class TestModel(models.Model):
    field1 = models.CharField(max_length=5)
    field2 = models.DateTimeField(auto_now_add=True)
