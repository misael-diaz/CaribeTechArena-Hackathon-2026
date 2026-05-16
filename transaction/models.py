from django.db import models

class Transaction(models.Model):
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE, related_name='transactions')
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Venta {self.id} - {self.student.name}"

class Recarga(models.Model):
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE, related_name='recargas')
    fecha = models.DateField()
    valor = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"Recarga {self.id} - {self.student.name} ({self.valor})"
