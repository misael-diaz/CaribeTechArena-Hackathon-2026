from django.core.management.base import BaseCommand
from django.utils import timezone
from student.models import Student
from transaction.models import Transaction
from product.models import NutritionFact
import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía alertas proactivas de ausencia de consumo y exceso nutricional a los padres.'

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(self.style.WARNING(f"[{start_time}] Iniciando proceso de alertas de no-consumo y nutrición..."))
        today = date.today()
        start_of_today = timezone.make_aware(
            datetime.combine(today, datetime.min.time())
        )
        end_of_today = timezone.make_aware(
            datetime.combine(today, datetime.max.time())
        )

        # Consultamos todos los estudiantes activos (asumimos que todos los registrados están activos en el piloto)
        students = Student.objects.all().prefetch_related('parents')

        alerts_sent = 0
        students_without_consumption = []
        students_with_excess_nutrition = []

        for student in students:
            # Filtramos si tienen alguna transacción con fecha de hoy (00:00–23:59:59)
            transactions_today = Transaction.objects.filter(
                student=student,
                created_at__gte=start_of_today,
                created_at__lte=end_of_today
            ).select_related('product')

            if not transactions_today.exists():
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
            else:
                # Verificar exceso nutricional
                total_calories = 0
                sugar_flags = 0
                sodium_flags = 0
                fat_flags = 0

                for t in transactions_today:
                    # Estimación de calorías por categoría
                    name_lower = t.product.name.lower()
                    if 'coca' in name_lower or 'gaseosa' in name_lower or 'jugo' in name_lower or 'hit' in name_lower:
                        calories = 150 * t.quantity
                    elif 'papas' in name_lower or 'detodito' in name_lower or 'boliqueso' in name_lower or 'margarita' in name_lower:
                        calories = 250 * t.quantity
                    elif 'fruta' in name_lower or 'manzana' in name_lower or 'platanitos' in name_lower or 'festival' in name_lower:
                        calories = 80 * t.quantity
                    else:
                        calories = 180 * t.quantity

                    total_calories += calories

                    # Verificar flags nutricionales
                    try:
                        nf = NutritionFact.objects.filter(product_name__iexact=t.product.name).first()
                        if nf:
                            if nf.high_sugar:
                                sugar_flags += 1
                            if nf.high_sodium:
                                sodium_flags += 1
                            if nf.high_fat:
                                fat_flags += 1
                    except:
                        pass

                # Si supera umbrales, enviar alerta
                if (total_calories > 1500 or
                    sugar_flags > 3 or
                    sodium_flags > 2 or
                    fat_flags > 3):

                    parents = student.parents.all()
                    if parents:
                        students_with_excess_nutrition.append(student)
                        for parent in parents:
                            phone = parent.phone_e164
                            parent_name = parent.name or 'Padre/Madre'

                            msg = (f"⚠️ ALERTA NUTRICIONAL BioFood: Hola {parent_name}, te informamos que tu hijo/a {student.name} "
                                   f"consumió hoy una cantidad elevada de nutrientes:\n"
                                   f"• Calorías estimadas: {total_calories} kcal\n"
                                   f"• Productos altos en azúcar: {sugar_flags}\n"
                                   f"• Productos altos en sodio: {sodium_flags}\n"
                                   f"• Productos altos en grasa: {fat_flags}\n\n"
                                   f"Recomendamos revisar su alimentación y considerar opciones más saludables.")

                            self.stdout.write(f"-> [WHATSAPP API MOCK] Enviando alerta nutricional a {phone} sobre {student.name}")
                            logger.info(f"Alerta nutricional enviada a {phone} por exceso de {student.name}")
                            alerts_sent += 1

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        summary = (f"[{end_time}] Cron job finalizado en {duration:.2f} segundos. "
                   f"Se enviaron {alerts_sent} alertas:\n"
                   f"• {len(students_without_consumption)} por ausencia de consumo\n"
                   f"• {len(students_with_excess_nutrition)} por exceso nutricional.")
        self.stdout.write(self.style.SUCCESS(summary))
        logger.info(summary)