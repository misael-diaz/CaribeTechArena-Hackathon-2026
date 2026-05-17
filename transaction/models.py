from django.db import models

class Transaction(models.Model):
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE, related_name='transactions', db_index=True)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Venta {self.id} - {self.student.name}"

class Recarga(models.Model):
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE, related_name='recargas', db_index=True)
    fecha = models.DateField(db_index=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['student', '-fecha']),
        ]

    def __str__(self):
        return f"Recarga {self.id} - {self.student.name} ({self.valor})"
