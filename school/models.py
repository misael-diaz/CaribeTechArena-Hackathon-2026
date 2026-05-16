from django.db import models

class School(models.Model):
    name = models.CharField(max_length=255)
    nit = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.name
