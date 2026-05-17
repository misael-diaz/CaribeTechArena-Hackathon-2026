from django.db import models

class School(models.Model):
    name = models.CharField(max_length=255)
    nit = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.name

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
