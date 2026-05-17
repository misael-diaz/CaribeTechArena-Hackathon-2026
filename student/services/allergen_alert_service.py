import logging
from typing import List, Optional
from django.utils import timezone
from student.models import Student, StudentAllergen
from product.models import ProductAllergen
from transaction.models import Transaction
from parent.models import Parent

logger = logging.getLogger(__name__)


class AllergenAlertService:
    """
    Service para gestionar alertas de alérgenos.
    Envía WhatsApp a padres y crea notificaciones en el portal del colegio.
    """

    def __init__(self):
        self.alerts_sent = []

    def check_and_alert(self, transaction: Transaction) -> List[dict]:
        """Verifica alérgenos y envía alertas."""
        alerts = []
        student = transaction.student
        product = transaction.product

        student_allergens = set(
            StudentAllergen.objects
            .filter(student=student)
            .values_list('allergen_name', flat=True)
        )

        if not student_allergens:
            return alerts

        product_allergens = set(
            ProductAllergen.objects
            .filter(product=product)
            .values_list('allergen_name', flat=True)
        )

        if not product_allergens:
            return alerts

        matching_allergens = student_allergens & product_allergens

        if not matching_allergens:
            return alerts

        parents = student.parents.all()

        for parent in parents:
            alert_data = self._send_alert(
                parent=parent,
                student=student,
                product=product,
                allergens=matching_allergens,
                transaction=transaction
            )
            if alert_data:
                alerts.append(alert_data)

        return alerts

    def _send_alert(
        self,
        parent: Parent,
        student: Student,
        product: 'Product',
        allergens: set,
        transaction: Transaction
    ) -> Optional[dict]:
        """Envía alerta WhatsApp y crea notificación en portal."""
        phone = parent.phone_e164
        parent_name = parent.name or 'Padre/Madre'

        allergen_list = ', '.join(sorted(allergens))
        timestamp = transaction.created_at.strftime('%d/%m/%Y %H:%M')

        message = (
            f"🚨 ALERTA CRITICA BioFood - {parent_name}:\n\n"
            f"Tu hijo/a {student.name} compro producto con alérgenos:\n\n"
            f"⚠️ Producto: {product.name}\n"
            f"⚠️ Alérgeno(s): {allergen_list}\n"
            f"⚠️ Hora: {timestamp}\n\n"
            f"Verifica el estado de tu hijo."
        )

        try:
            # Enviar WhatsApp
            from chat.twilio_service import TwilioService
            twilio_service = TwilioService()
            message_sid = twilio_service.send_message(phone, message)

            # CREAR NOTIFICACION EN EL PORTAL DEL COLEGIO
            from school.models import Notification
            Notification.objects.create(
                school=student.school,
                title=f'ALERTA Alérgeno: {student.name}',
                message=f'{student.name} compro {product.name} que contiene: {allergen_list}. Se notifico a los padres.',
                priority='CRITICAL',
                type='ALLERGEN',
                action_url=f'/student/allergens/{student.id}/',
                metadata={
                    'student_id': student.id,
                    'product_id': product.id,
                    'transaction_id': transaction.id,
                    'allergens': list(allergens),
                    'parent_id': parent.id
                }
            )

            if message_sid:
                alert_data = {
                    'parent_id': parent.id,
                    'parent_phone': phone,
                    'student_id': student.id,
                    'product_id': product.id,
                    'allergens': list(allergens),
                    'transaction_id': transaction.id,
                    'message_sid': message_sid,
                    'sent_at': timezone.now(),
                    'status': 'sent'
                }

                self.alerts_sent.append(alert_data)
                logger.info(f"Alerta alérgeno enviada | {phone} | {student.name} | {allergen_list}")
                return alert_data
            else:
                logger.warning(f"Twilio mock | {phone} | {student.name}")
                return {
                    'parent_id': parent.id,
                    'parent_phone': phone,
                    'student_id': student.id,
                    'product_id': product.id,
                    'allergens': list(allergens),
                    'transaction_id': transaction.id,
                    'message_sid': None,
                    'sent_at': timezone.now(),
                    'status': 'mock'
                }

        except Exception as e:
            logger.error(f"Error alerta alérgeno {phone}: {e}")
            return {
                'parent_id': parent.id,
                'parent_phone': phone,
                'student_id': student.id,
                'product_id': product.id,
                'allergens': list(allergens),
                'transaction_id': transaction.id,
                'message_sid': None,
                'sent_at': timezone.now(),
                'status': 'failed',
                'error': str(e)
            }

    def get_alerts_sent(self) -> List[dict]:
        return self.alerts_sent
