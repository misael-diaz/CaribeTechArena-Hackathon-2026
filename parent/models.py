from django.db import models

class Parent(models.Model):
    phone_e164 = models.CharField(max_length=20, unique=True, verbose_name="Teléfono (E.164)")
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre del Padre")
    students = models.ManyToManyField('student.Student', related_name='parents', verbose_name="Estudiantes (Hijos)")

    class Meta:
        verbose_name = "Padre"
        verbose_name_plural = "Padres"

    def __str__(self):
        return f"{self.name or self.phone_e164} ({self.students.count()} hijos)"

    def get_students(self):
        return Parent.objects.filter(phone_e164=self.phone_e164).values('students__name')
