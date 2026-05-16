from django.db import models

class ParentPhoneMap(models.Model):
    phone_e164 = models.CharField(max_length=20)
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE, related_name='parents')

    def __str__(self):
        return f"{self.phone_e164} -> {self.student.name}"
