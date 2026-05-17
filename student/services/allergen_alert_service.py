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
    
    Envía notificaciones a los padres cuando su hijo compra un producto
    que contiene un alérgeno que tienen registrado.
    """
    
    def __init__(self):
        self.alerts_sent = []
    
    def check_and_alert(self, transaction: Transaction) -> List[dict]:
        """
        Verifica si la transacción contiene un producto con alérgenos
        que el estudiante tiene registrados y envía alertas a los padres.
        
        Args:
            transaction: La transacción a verificar
            
        Returns:
            Lista de alertas enviadas con información de cada una
        """
        alerts = []
        student = transaction.student
        product = transaction.product
        
        # Obtener alérgenos del estudiante
        student_allergens = set(
            StudentAllergen.objects
            .filter(student=student)
            .values_list('allergen_name', flat=True)
        )
        
        if not student_allergens:
            return alerts
        
        # Obtener alérgenos del producto
        product_allergens = set(
            ProductAllergen.objects
            .filter(product=product)
            .values_list('allergen_name', flat=True)
        )
        
        if not product_allergens:
            return alerts
        
        # Encontrar intersección (alérgenos en conflicto)
        matching_allergens = student_allergens & product_allergens
        
        if not matching_allergens:
            return alerts
        
        # Hay alérgenos en conflicto - enviar alertas a los padres
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
        """
        Envía una alerta individual a un padre.
        
        Args:
            parent: El padre a notificar
            student: El estudiante que compró el producto
            product: El producto comprado
            allergens: Lista de alérgenos detectados
            transaction: La transacción original
            
        Returns:
            Dict con información de la alerta o None si falló
        """
        phone = parent.phone_e164
        parent_name = parent.name or 'Padre/Madre'
        
        # Construir mensaje de alerta
        allergen_list = ', '.join(sorted(allergens))
        timestamp = transaction.created_at.strftime('%d/%m/%Y %H:%M')
        
        message = (
            f"🚨 ALERTA CRÍTICA BioFood - {parent_name}:\n\n"
            f"Tu hijo/a {student.name} ha comprado un producto que contiene "
            f"alérgenos que tiene registrados:\n\n"
            f"⚠️ Producto: {product.name}\n"
            f"⚠️ Alérgeno(s): {allergen_list}\n"
            f"⚠️ Hora: {timestamp}\n\n"
            f"Por favor, verifica el estado de tu hijo inmediatamente."
        )
        
        try:
            # Enviar mensaje vía Twilio/WhatsApp
            from chat.services import TwilioService
            
            twilio_service = TwilioService()
            message_sid = twilio_service.send_message(phone, message)
            
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
                logger.info(
                    f"Alerta de alérgeno enviada a {phone} | "
                    f"Student: {student.name} | Product: {product.name} | "
                    f"Allergens: {allergen_list}"
                )
                
                return alert_data
            else:
                logger.warning(
                    f"Twilio no envió la alerta (posible modo mock) | "
                    f"Phone: {phone} | Student: {student.name}"
                )
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
            logger.error(
                f"Error enviando alerta de alérgeno a {phone}: {e} | "
                f"Student: {student.name} | Product: {product.name}"
            )
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
        """Retorna todas las alertas enviadas en esta instancia del servicio."""
        return self.alerts_sent
