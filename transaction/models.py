from django.db import models
import secrets

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


class Loan(models.Model):
    """
    Prestamo temporal cuando el estudiante se queda sin saldo.
    Se carga a la cuenta del padre como deuda.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pendiente de aprobacion'),
        ('APPROVED', 'Aprobado'),
        ('REJECTED', 'Rechazado'),
        ('PAID', 'Pagado'),
    )
    
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE, related_name='loans', db_index=True)
    parent = models.ForeignKey('parent.Parent', on_delete=models.CASCADE, related_name='loans', db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='loan')
    approval_token = models.CharField(max_length=64, unique=True, db_index=True, help_text='Token para aprobar via link')
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['parent', 'status']),
        ]
    
    def __str__(self):
        return f"Prestamo ${self.amount} - {self.student.name} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.approval_token:
            self.approval_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def is_pending(self):
        return self.status == 'PENDING'
    
    def is_approved(self):
        return self.status == 'APPROVED'
    
    def is_paid(self):
        return self.status == 'PAID'
