from django.db.models.signals import post_save
from django.dispatch import receiver
from cafeteria.models import Inventory
from cafeteria.services import StockAlertService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Inventory)
def check_stock_alert(sender, instance, **kwargs):
    """
    Signal que se dispara cuando se actualiza un inventario.

    Verifica si el producto tiene stock crítico (current_stock <= minimum_stock)
    y envía alertas a los administradores de la cafetería.
    """
    try:
        service = StockAlertService()
        alerts = service.check_and_alert(instance)

        if alerts:
            logger.info(
                f"Signal de stock ejecutado | Inventory: {instance.id} | "
                f"Alertas enviadas: {len(alerts)}"
            )
        else:
            # Log solo para debugging, no es error
            logger.debug(
                f"Signal de stock ejecutado | Inventory: {instance.id} | "
                f"No se enviaron alertas (stock normal)"
            )

    except Exception as e:
        # Log el error pero no romper la operación
        logger.error(f"Error en signal de stock para inventario {instance.id}: {e}")
