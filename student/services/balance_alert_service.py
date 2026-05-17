import logging
from typing import List
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from student.models import Student
from school.models import School, Notification
from transaction.models import Transaction

logger = logging.getLogger(__name__)

LOW_BALANCE_THRESHOLD = Decimal('5000.00')


class BalanceAlertService:

    def __init__(self):
        self.alerts_created = []

    def check_and_alert(self) -> List[dict]:
        alerts = []
        schools = School.objects.all()

        for school in schools:
            low_balance_students = Student.objects.filter(
                school=school,
                balance__lte=LOW_BALANCE_THRESHOLD
            ).order_by('balance')

            if not low_balance_students:
                continue

            count = low_balance_students.count()
            min_balance = low_balance_students.first().balance

            names = ', '.join(
                s.name for s in low_balance_students[:5]
            )
            if count > 5:
                names += f' y {count - 5} mas'

            last_week = timezone.now() - timedelta(days=7)
            recent_buyers = low_balance_students.filter(
                transactions__created_at__gte=last_week
            ).distinct().count()

            try:
                notification = Notification.objects.create(
                    school=school,
                    title=f'Saldo bajo: {count} estudiante{"s" if count != 1 else ""}',
                    message=(
                        f'{count} estudiante{"s" if count != 1 else ""} tiene'
                        f' saldo menor a ${float(LOW_BALANCE_THRESHOLD):.0f}. '
                        f'Saldo mas bajo: ${float(min_balance):.0f}. '
                        f'{recent_buyers} compraron en los ultimos 7 dias. '
                        f'Afectados: {names}.'
                    ),
                    priority='MEDIUM',
                    type='BALANCE',
                    action_url='/school/kiosko/',
                    metadata={
                        'student_count': count,
                        'min_balance': float(min_balance),
                        'threshold': float(LOW_BALANCE_THRESHOLD),
                        'recent_buyers': recent_buyers,
                        'student_ids': list(low_balance_students.values_list('id', flat=True)),
                    }
                )

                alert_data = {
                    'school_id': school.id,
                    'school_name': school.name,
                    'student_count': count,
                    'notification_id': notification.id,
                    'created_at': timezone.now(),
                }

                self.alerts_created.append(alert_data)
                logger.info(
                    f'Alerta saldo creada | {school.name} | '
                    f'{count} estudiantes con saldo < ${float(LOW_BALANCE_THRESHOLD):.0f}'
                )
                alerts.append(alert_data)

            except Exception as e:
                logger.error(f'Error creating balance alert for {school.name}: {e}')

        return alerts

    def check_and_alert_all_schools(self) -> List[dict]:
        return self.check_and_alert()

    def get_alerts_created(self) -> List[dict]:
        return self.alerts_created
