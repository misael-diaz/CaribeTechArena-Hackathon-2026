import logging
from typing import List, Optional
from django.db.models import F
from django.utils import timezone
from cafeteria.models import Inventory, CafeteriaAdmin

logger = logging.getLogger(__name__)


class TwilioServiceWrapper:
    """Wrapper para TwilioService para evitar circular imports."""

    def __init__(self):
        from chat.twilio_service import TwilioService as _TwilioService
        self._service = _TwilioService()

    def send_message(self, to_number, body):
        return self._service.send_message(to_number, body)


class StockAlertService:
    """
    Service para gestionar alertas de stock crítico.
    Envía notificaciones vía WhatsApp y crea notificaciones en el portal.
    """

    def __init__(self):
        self.alerts_sent = []

    def check_and_alert(self, inventory: Inventory) -> List[dict]:
        """Verifica stock crítico y envía alertas."""
        alerts = []

        if inventory.current_stock > inventory.minimum_stock:
            return alerts

        self._create_portal_notification(inventory)

        admins = CafeteriaAdmin.objects.filter(school=inventory.school)

        if not admins:
            logger.warning(f"No hay admins para {inventory.school.name}")
            return alerts

        for admin in admins:
            alert_data = self._send_alert(admin=admin, inventory=inventory)
            if alert_data:
                alerts.append(alert_data)

        return alerts

    def _create_portal_notification(self, inventory: Inventory):
        from school.models import Notification
        priority = 'CRITICAL' if inventory.current_stock == 0 else 'HIGH'
        Notification.objects.create(
            school=inventory.school,
            title=f'Stock {"CRITICO" if inventory.current_stock == 0 else "BAJO"}: {inventory.product.name}',
            message=f'El producto {inventory.product.name} tiene {inventory.current_stock} unidades (minimo: {inventory.minimum_stock}).',
            priority=priority,
            type='STOCK',
            action_url='/cafeteria/inventory/',
            metadata={
                'inventory_id': inventory.id,
                'product_id': inventory.product.id,
                'current_stock': inventory.current_stock,
                'minimum_stock': inventory.minimum_stock
            }
        )

    def _send_alert(self, admin: CafeteriaAdmin, inventory: Inventory) -> Optional[dict]:
        """Envía alerta WhatsApp y crea notificación en portal."""
        phone = admin.phone_e164
        school_name = inventory.school.name
        product_name = inventory.product.name
        current = inventory.current_stock
        minimum = inventory.minimum_stock

        timestamp = timezone.now().strftime('%d/%m/%Y %H:%M')

        message = (
            f"📦 ALERTA DE STOCK BioFood - {school_name}:\n\n"
            f"Producto: {product_name}\n"
            f"Stock: {current} unidades (minimo: {minimum})\n"
            f"Fecha: {timestamp}\n\n"
            f"Por favor realice el pedido."
        )

        try:
            # Enviar WhatsApp
            twilio_service = TwilioServiceWrapper()
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
                logger.info(f"Alerta stock enviada | {school_name} | {product_name} | {current}/{minimum}")
                return alert_data
            else:
                logger.warning(f"Twilio mock | {phone} | {school_name}")
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
            logger.error(f"Error alerta stock {phone}: {e}")
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
        return self.alerts_sent

    def check_all_critical_stock(self) -> List[dict]:
        """Verifica todo el inventario crítico."""
        all_alerts = []

        critical_inventories = Inventory.objects.filter(
            current_stock__lte=F('minimum_stock')
        ).select_related('product', 'school')

        for inventory in critical_inventories:
            alerts = self.check_and_alert(inventory)
            all_alerts.extend(alerts)

        return all_alerts
