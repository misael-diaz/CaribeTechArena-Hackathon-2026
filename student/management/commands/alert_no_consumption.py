from django.core.management.base import BaseCommand
from django.utils import timezone
from student.models import Student
from transaction.models import Transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Envía alertas proactivas de ausencia de consumo a los padres si sus hijos no han comprado nada hoy.'

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(self.style.WARNING(f"[{start_time}] Iniciando proceso de alertas de no-consumo..."))
        today = timezone.now().date()
        
        # Consultamos todos los estudiantes activos (asumimos que todos los registrados están activos en el piloto)
        students = Student.objects.all().prefetch_related('parents')
        
        alerts_sent = 0
        students_without_consumption = []
        
        for student in students:
            # Filtramos si tienen alguna transacción con fecha de hoy
            has_transactions_today = Transaction.objects.filter(
                student=student, 
                created_at__date=today
            ).exists()
            
            if not has_transactions_today:
                parents = student.parents.all()
                if parents:
                    students_without_consumption.append(student)
                    for parent in parents:
                        phone = parent.phone_e164
                        parent_name = parent.name or 'Padre/Madre'
                        msg = (f"⚠️ Alerta BioFood: Hola {parent_name}, te informamos que tu hijo/a {student.name} "
                               f"no ha registrado ninguna compra en la cafetería el día de hoy hasta este momento. "
                               f"Te sugerimos verificar si está bien o si requiere recarga de saldo.")
                        
                        # Aquí se integraría la API de Twilio o WhatsApp de Meta.
                        # Por seguridad en el despliegue actual, lo registramos en los logs.
                        self.stdout.write(f"-> [WHATSAPP API MOCK] Enviando mensaje a {phone} sobre {student.name}")
                        logger.info(f"Alerta enviada a {phone} por ausencia de consumo de {student.name}")
                        alerts_sent += 1
        
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = (f"[{end_time}] Cron job finalizado en {duration:.2f} segundos. "
                   f"Se enviaron {alerts_sent} alertas para {len(students_without_consumption)} estudiantes sin consumo.")
        self.stdout.write(self.style.SUCCESS(summary))
        logger.info(summary)
