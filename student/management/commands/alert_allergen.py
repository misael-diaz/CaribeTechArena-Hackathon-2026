from django.core.management.base import BaseCommand
from django.utils import timezone
from student.models import Student, StudentAllergen
from product.models import ProductAllergen
from transaction.models import Transaction
from student.services import AllergenAlertService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía alertas de alérgenos como fallback para transacciones sin alertar (cron job).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=5,
            help='Número de minutos hacia atrás para buscar transacciones sin alertar (default: 5)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué alertas se enviarían, no las envía'
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        minutes = options.get('minutes', 5)
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(
            self.style.WARNING(
                f"[{start_time}] Iniciando cron job de alertas de alérgenos (fallback)..."
            )
        )
        self.stdout.write(f"Buscando transacciones de los últimos {minutes} minutos")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN: No se enviarán mensajes reales"))
        
        # Calcular el tiempo límite
        time_limit = start_time - timezone.timedelta(minutes=minutes)
        
        # Obtener todas las transacciones recientes
        recent_transactions = Transaction.objects.filter(
            created_at__gte=time_limit
        ).select_related('student', 'product').order_by('-created_at')
        
        total_transactions = recent_transactions.count()
        self.stdout.write(f"Encontradas {total_transactions} transacciones recientes")
        
        alerts_sent = 0
        alerts_failed = 0
        processed = 0
        
        for transaction in recent_transactions:
            processed += 1
            
            # Verificar si el estudiante tiene alérgenos registrados
            student_allergens = set(
                StudentAllergen.objects
                .filter(student=transaction.student)
                .values_list('allergen_name', flat=True)
            )
            
            if not student_allergens:
                continue
            
            # Verificar si el producto tiene alérgenos
            product_allergens = set(
                ProductAllergen.objects
                .filter(product=transaction.product)
                .values_list('allergen_name', flat=True)
            )
            
            if not product_allergens:
                continue
            
            # Encontrar intersección
            matching_allergens = student_allergens & product_allergens
            
            if not matching_allergens:
                continue
            
            # Hay coincidencia - enviar alerta
            allergen_list = ', '.join(sorted(matching_allergens))
            
            if dry_run:
                parents = transaction.student.parents.all()
                for parent in parents:
                    self.stdout.write(
                        f"[DRY-RUN] Alerta: {parent.phone_e164} | "
                        f"Student: {transaction.student.name} | "
                        f"Product: {transaction.product.name} | "
                        f"Allergens: {allergen_list}"
                    )
                    alerts_sent += 1
            else:
                # Usar el service para enviar la alerta
                service = AllergenAlertService()
                results = service.check_and_alert(transaction)
                
                for result in results:
                    if result.get('status') == 'sent':
                        alerts_sent += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Alerta enviada a {result['parent_phone']} | "
                                f"Student: {transaction.student.name} | "
                                f"Product: {transaction.product.name} | "
                                f"Allergens: {allergen_list}"
                            )
                        )
                    elif result.get('status') == 'mock':
                        alerts_sent += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠ Alerta mock (Twilio no configurado) para {result['parent_phone']} | "
                                f"Student: {transaction.student.name}"
                            )
                        )
                    else:
                        alerts_failed += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Alerta fallida para {result['parent_phone']} | "
                                f"Student: {transaction.student.name}"
                            )
                        )
        
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = (
            f"[{end_time}] Cron job finalizado en {duration:.2f} segundos. | "
            f"Transacciones procesadas: {processed} | "
            f"Alertas enviadas: {alerts_sent} | "
            f"Alertas fallidas: {alerts_failed}"
        )
        
        self.stdout.write(self.style.SUCCESS(summary))
        logger.info(summary)
