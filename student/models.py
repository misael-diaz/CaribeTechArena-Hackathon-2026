from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=255)
    external_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    grade = models.CharField(max_length=50)
    school = models.ForeignKey('school.School', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    parent_id = models.CharField(max_length=20, blank=True, null=True)
    parent_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class StudentAllergen(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='allergens')
    allergen_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.student.name} - {self.allergen_name}"
