from django.core.management.base import BaseCommand
from student.services.balance_alert_service import BalanceAlertService


class Command(BaseCommand):
    help = 'Verifica saldos bajos y crea notificaciones'

    def handle(self, *args, **options):
        service = BalanceAlertService()
        alerts = service.check_and_alert_all_schools()

        if not alerts:
            self.stdout.write(self.style.SUCCESS('No se detectaron saldos bajos.'))
            return

        for alert in alerts:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{alert["school_name"]}: {alert["student_count"]} estudiantes con saldo bajo'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'\n{len(alerts)} alertas creadas')
        )
