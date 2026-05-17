from django.db import models
from django.contrib.auth.models import User

class School(models.Model):
    name = models.CharField(max_length=255)
    nit = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.name


class SchoolUser(models.Model):
    """
    Usuario personalizado para colegios.
    Se relaciona con User de Django y agrega informacion del colegio.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='school_profile')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(
        max_length=20,
        choices=[
            ('ADMIN', 'Administrador'),
            ('CAFETERIA', 'Admin Cafetería'),
            ('SECRETARIA', 'Secretaría'),
        ],
        default='SECRETARIA'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Usuario de Colegio'
        verbose_name_plural = 'Usuarios de Colegio'
        permissions = [
            ('can_view_dashboard', 'Puede ver dashboard'),
            ('can_view_notifications', 'Puede ver notificaciones'),
            ('can_manage_loans', 'Puede gestionar préstamos'),
            ('can_manage_inventory', 'Puede gestionar inventario'),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.school.name})"

    def has_permission(self, permission_codename):
        """Verifica si el usuario tiene un permiso especifico."""
        return self.user.has_perm(f'school.{permission_codename}')


class Notification(models.Model):
    """
    Notificaciones para usuarios del colegio.
    """
    PRIORITY_CHOICES = (
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('CRITICAL', 'Crítica'),
    )

    TYPE_CHOICES = (
        ('LOAN', 'Préstamo'),
        ('STOCK', 'Stock'),
        ('ALLERGEN', 'Alérgeno'),
        ('BALANCE', 'Saldo'),
        ('GENERAL', 'General'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='GENERAL')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    action_url = models.CharField(max_length=500, blank=True, null=True, help_text='URL para accion relacionada')
    metadata = models.JSONField(blank=True, null=True, help_text='Datos adicionales (JSON)')

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['school', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['priority', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.priority}] {self.title} - {self.school.name}"

    def mark_as_read(self):
        """Marca la notificacion como leida."""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


class AlertConfiguration(models.Model):
    ALERT_TYPES = (
        ('NO_CONSUMPTION', 'Sin Consumo (Mediodía)'),
        ('LOW_BALANCE', 'Saldo Bajo'),
        ('WEEKLY_SUMMARY', 'Resumen Semanal'),
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    trigger_time = models.TimeField(help_text="Hora del día en que se debe disparar la alerta")
    is_active = models.BooleanField(default=True)
    last_run_date = models.DateField(blank=True, null=True, help_text="Última vez que se ejecutó para evitar duplicados en el mismo día")

    class Meta:
        verbose_name = "Configuración de Alerta"
        verbose_name_plural = "Configuraciones de Alertas"
        unique_together = ('school', 'alert_type')

    def __str__(self):
        return f"{self.school.name} - {self.get_alert_type_display()} @ {self.trigger_time}"
