from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F
from school.models import School, SchoolUser, Notification
from transaction.models import Loan
from cafeteria.models import Inventory
from student.models import StudentAllergen
from datetime import timedelta


class Command(BaseCommand):
    help = 'Ingesta notificaciones reales desde la base de datos'

    def handle(self, *args, **options):
        schools = School.objects.all()
        
        if not schools:
            self.stdout.write(self.style.ERROR('No hay colegios registrados'))
            return

        total_created = 0

        for school in schools:
            self.stdout.write(f'\nProcesando colegio: {school.name}')
            
            # 1. Notificaciones de préstamos pendientes
            pending_loans = Loan.objects.filter(
                parent__students__school=school,
                status='PENDING'
            ).select_related('student', 'parent').order_by('-created_at')[:10]
            
            for loan in pending_loans:
                notification, created = Notification.objects.get_or_create(
                    school=school,
                    type='LOAN',
                    metadata__loan_id=loan.id,
                    defaults={
                        'title': f'Prestamo pendiente: {loan.student.name}',
                        'message': f'{loan.student.name} solicito ${loan.amount}. Padre: {loan.parent.name or loan.parent.phone_e164}',
                        'priority': 'HIGH',
                        'action_url': f'/transaction/api/loan/approve/{loan.approval_token}/'
                    }
                )
                if created:
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Prestamo: {loan.student.name} - ${loan.amount}'))

            # 2. Notificaciones de stock crítico
            critical_inventory = Inventory.objects.filter(
                school=school,
                current_stock__lte=0
            ).select_related('product').order_by('current_stock')[:10]
            
            for inv in critical_inventory:
                notification, created = Notification.objects.get_or_create(
                    school=school,
                    type='STOCK',
                    metadata__product_id=inv.product.id,
                    defaults={
                        'title': f'STock CRITICO: {inv.product.name}',
                        'message': f'El producto {inv.product.name} tiene {inv.current_stock} unidades (minimo: {inv.minimum_stock})',
                        'priority': 'CRITICAL',
                        'action_url': '/cafeteria/inventory/'
                    }
                )
                if created:
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Stock CRITICO: {inv.product.name} ({inv.current_stock})'))

            # 3. Notificaciones de stock bajo
            low_inventory = Inventory.objects.filter(
                school=school,
                current_stock__gt=0,
                current_stock__lte=F('minimum_stock')
            ).select_related('product').order_by('current_stock')[:10]
            
            for inv in low_inventory:
                notification, created = Notification.objects.get_or_create(
                    school=school,
                    type='STOCK',
                    metadata__product_id=inv.product.id,
                    defaults={
                        'title': f'Stock bajo: {inv.product.name}',
                        'message': f'El producto {inv.product.name} tiene {inv.current_stock} unidades (minimo: {inv.minimum_stock})',
                        'priority': 'MEDIUM',
                        'action_url': '/cafeteria/inventory/'
                    }
                )
                if created:
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Stock bajo: {inv.product.name} ({inv.current_stock})'))

            # 4. Notificaciones de alérgenos (últimas 24 horas)
            from transaction.models import Transaction
            allergen_transactions = Transaction.objects.filter(
                student__school=school,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).select_related('student', 'product').order_by('-created_at')[:10]
            
            for t in allergen_transactions:
                # Verificar si hay alérgenos en común
                student_allergens = set(
                    StudentAllergen.objects
                    .filter(student=t.student)
                    .values_list('allergen_name', flat=True)
                )
                
                if student_allergens:
                    product_allergens = set(
                        t.product.allergens.values_list('allergen_name', flat=True)
                    )
                    
                    matching = student_allergens & product_allergens
                    
                    if matching:
                        notification, created = Notification.objects.get_or_create(
                            school=school,
                            type='ALLERGEN',
                            metadata__transaction_id=t.id,
                            defaults={
                                'title': f'ALERTA Alérgeno: {t.student.name}',
                                'message': f'{t.student.name} compro {t.product.name} que contiene: {", ".join(matching)}',
                                'priority': 'CRITICAL',
                                'action_url': f'/student/allergens/{t.student.id}/'
                            }
                        )
                        if created:
                            total_created += 1
                            self.stdout.write(self.style.SUCCESS(f'  ✓ Alérgeno: {t.student.name} - {", ".join(matching)}'))

        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(f'Total notificaciones creadas: {total_created}')
        self.stdout.write(f'Colegios procesados: {schools.count()}')
