import logging
from typing import List, Optional
from django.db.models import F
from django.utils import timezone
from cafeteria.models import Inventory, CafeteriaAdmin
from chat.services import TwilioService

logger = logging.getLogger(__name__)


class StockAlertService:
    """
    Service para gestionar alertas de stock crítico.

    Envía notificaciones vía WhatsApp a los administradores de cafetería
    cuando un producto tiene current_stock <= minimum_stock.
    """

    def __init__(self):
        self.alerts_sent = []

    def check_and_alert(self, inventory: Inventory) -> List[dict]:
        """
        Verifica si el inventario tiene stock crítico y envía alertas
        a los administradores de la cafetería.

        Args:
            inventory: El inventario a verificar

        Returns:
            Lista de alertas enviadas con información de cada una
        """
        alerts = []

        # Verificar si el stock es crítico
        if inventory.current_stock > inventory.minimum_stock:
            return alerts

        # Obtener administradores de la cafetería
        admins = CafeteriaAdmin.objects.filter(school=inventory.school)

        if not admins:
            logger.warning(
                f"No hay administradores registrados para la cafetería "
                f"{inventory.school.name}. No se envían alertas."
            )
            return alerts

        # Enviar alerta a cada administrador
        for admin in admins:
            alert_data = self._send_alert(
                admin=admin,
                inventory=inventory
            )
            if alert_data:
                alerts.append(alert_data)

        return alerts

    def _send_alert(
        self,
        admin: CafeteriaAdmin,
        inventory: Inventory
    ) -> Optional[dict]:
        """
        Envía una alerta individual a un administrador.

        Args:
            admin: El administrador a notificar
            inventory: El inventario con stock crítico

        Returns:
            Dict con información de la alerta o None si falló
        """
        phone = admin.phone_e164
        school_name = inventory.school.name
        product_name = inventory.product.name
        current = inventory.current_stock
        minimum = inventory.minimum_stock

        # Construir mensaje de alerta
        timestamp = timezone.now().strftime('%d/%m/%Y %H:%M')

        message = (
            f"📦 ALERTA DE STOCK BioFood - {school_name}:\n\n"
            f"Producto en stock crítico:\n\n"
            f"⚠️ Producto: {product_name}\n"
            f"⚠️ Stock actual: {current} unidades\n"
            f"⚠️ Stock mínimo: {minimum} unidades\n"
            f"⚠️ Fecha: {timestamp}\n\n"
            f"Por favor, realice el pedido antes de que se agote."
        )

        try:
            # Enviar mensaje vía Twilio/WhatsApp
            twilio_service = TwilioService()
            message_sid = twilio_service.send_message(phone, message)

            if message_sid:
                alert_data = {
                    'admin_id': admin.id,
                    'admin_phone': phone,
                    'school_id': inventory.school.id,
                    'product_id': inventory.product.id,
                    'inventory_id': inventory.id,
                    'current_stock': current,
                    'minimum_stock': minimum,
                    'message_sid': message_sid,
                    'sent_at': timezone.now(),
                    'status': 'sent'
                }

                self.alerts_sent.append(alert_data)
                logger.info(
                    f"Alerta de stock enviada a {phone} | "
                    f"School: {school_name} | Product: {product_name} | "
                    f"Stock: {current}/{minimum}"
                )

                return alert_data
            else:
                logger.warning(
                    f"Twilio no envió la alerta (posible modo mock) | "
                    f"Phone: {phone} | School: {school_name}"
                )
                return {
                    'admin_id': admin.id,
                    'admin_phone': phone,
                    'school_id': inventory.school.id,
                    'product_id': inventory.product.id,
                    'inventory_id': inventory.id,
                    'current_stock': current,
                    'minimum_stock': minimum,
                    'message_sid': None,
                    'sent_at': timezone.now(),
                    'status': 'mock'
                }

        except Exception as e:
            logger.error(
                f"Error enviando alerta de stock a {phone}: {e} | "
                f"School: {school_name} | Product: {product_name}"
            )
            return {
                'admin_id': admin.id,
                'admin_phone': phone,
                'school_id': inventory.school.id,
                'product_id': inventory.product.id,
                'inventory_id': inventory.id,
                'current_stock': current,
                'minimum_stock': minimum,
                'message_sid': None,
                'sent_at': timezone.now(),
                'status': 'failed',
                'error': str(e)
            }

    def get_alerts_sent(self) -> List[dict]:
        """Retorna todas las alertas enviadas en esta instancia del servicio."""
        return self.alerts_sent

    def check_all_critical_stock(self) -> List[dict]:
        """
        Verifica todos los inventarios con stock crítico y envía alertas.

        Usado por el cron job para revisar todo el inventario.

        Returns:
            Lista de todas las alertas enviadas
        """
        all_alerts = []

        # Obtener todos los inventarios con stock crítico
        critical_inventories = Inventory.objects.filter(
            current_stock__lte=F('minimum_stock')
        ).select_related('product', 'school')

        for inventory in critical_inventories:
            alerts = self.check_and_alert(inventory)
            all_alerts.extend(alerts)

        return all_alerts
