from django.db.models.signals import post_save
from django.dispatch import receiver
from transaction.models import Transaction
from student.services import AllergenAlertService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def check_allergen_alert(sender, instance, created, **kwargs):
    """
    Signal que se dispara cuando se crea una nueva transacción.
    
    Verifica si el producto comprado contiene alérgenos que el estudiante
    tiene registrados y envía alertas a los padres si hay coincidencia.
    
    Solo se ejecuta cuando se crea una nueva transacción (no en updates).
    """
    if not created:
        return
    
    try:
        service = AllergenAlertService()
        alerts = service.check_and_alert(instance)
        
        if alerts:
            logger.info(
                f"Signal de alérgeno ejecutado | Transaction: {instance.id} | "
                f"Alertas enviadas: {len(alerts)}"
            )
        else:
            # Log solo para debugging, no es error
            logger.debug(
                f"Signal de alérgeno ejecutado | Transaction: {instance.id} | "
                f"No se enviaron alertas (sin coincidencias)"
            )
            
    except Exception as e:
        # Log el error pero no romper la transacción
        logger.error(f"Error en signal de alérgeno para transacción {instance.id}: {e}")
