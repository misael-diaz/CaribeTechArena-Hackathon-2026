from django.core.management.base import BaseCommand
from django.utils import timezone
from cafeteria.models import Inventory, CafeteriaAdmin
from cafeteria.services import StockAlertService
from django.db.models import F
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía alertas de stock crítico como fallback (cron job de las 7:00 AM).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué alertas se enviarían, no las envía'
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        dry_run = options.get('dry_run', False)

        self.stdout.write(
            self.style.WARNING(
                f"[{start_time}] Iniciando cron job de alertas de stock..."
            )
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN: No se enviarán mensajes reales"))

        # Obtener todos los inventarios con stock crítico
        critical_inventories = Inventory.objects.filter(
            current_stock__lte=F('minimum_stock')
        ).select_related('product', 'school')

        total_critical = critical_inventories.count()
        self.stdout.write(
            f"Encontrados {total_critical} productos con stock crítico"
        )

        alerts_sent = 0
        alerts_failed = 0
        processed = 0

        for inventory in critical_inventories:
            processed += 1
            product_name = inventory.product.name
            school_name = inventory.school.name
            current = inventory.current_stock
            minimum = inventory.minimum_stock

            if dry_run:
                admins = CafeteriaAdmin.objects.filter(school=inventory.school)
                for admin in admins:
                    self.stdout.write(
                        f"[DRY-RUN] Alerta: {admin.phone_e164} | "
                        f"School: {school_name} | "
                        f"Product: {product_name} | "
                        f"Stock: {current}/{minimum}"
                    )
                    alerts_sent += 1
            else:
                # Usar el service para enviar la alerta
                service = StockAlertService()
                results = service.check_and_alert(inventory)

                for result in results:
                    if result.get('status') == 'sent':
                        alerts_sent += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Alerta enviada a {result['admin_phone']} | "
                                f"School: {school_name} | "
                                f"Product: {product_name} | "
                                f"Stock: {current}/{minimum}"
                            )
                        )
                    elif result.get('status') == 'mock':
                        alerts_sent += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠ Alerta mock (Twilio no configurado) para {result['admin_phone']} | "
                                f"School: {school_name}"
                            )
                        )
                    else:
                        alerts_failed += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Alerta fallida para {result['admin_phone']} | "
                                f"School: {school_name}"
                            )
                        )

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        summary = (
            f"[{end_time}] Cron job finalizado en {duration:.2f} segundos. | "
            f"Inventarios procesados: {processed} | "
            f"Alertas enviadas: {alerts_sent} | "
            f"Alertas fallidas: {alerts_failed}"
        )

        self.stdout.write(self.style.SUCCESS(summary))
        logger.info(summary)
