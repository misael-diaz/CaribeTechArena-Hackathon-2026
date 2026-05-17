from django.core.management.base import BaseCommand
from django.utils import timezone
from school.models import School
from student.models import Student, StudentAllergen
from parent.models import Parent
from product.models import Product, ProductAllergen, NutritionFact
from transaction.models import Transaction, Recarga
from cafeteria.models import Inventory
from transaction.models import Transaction
from school.models import Notification
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Crea un colegio de ejemplo con estudiantes, padres, productos, transacciones y stock'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-name',
            type=str,
            default='Colegio Prueba BioFood',
            help='Nombre del colegio a crear (default: Colegio Prueba BioFood)'
        )
        parser.add_argument(
            '--nit',
            type=str,
            default='901234567',
            help='NIT del colegio (default: 901234567)'
        )

    def handle(self, *args, **options):
        school_name = options['school_name']
        nit = options['nit']

        # --- 1. Crear colegio ---
        school, created = School.objects.get_or_create(
            name=school_name,
            defaults={'nit': nit}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Colegio creado: {school.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Colegio ya existe: {school.name}'))

        # --- 2. Crear estudiantes ---
        students_data = [
            {'name': 'Juan Pérez', 'grade': '5°', 'balance': 12500},
            {'name': 'María Gómez', 'grade': '4°', 'balance': 8200},
            {'name': 'Carlos López', 'grade': '6°', 'balance': 15000},
        ]

        students = []
        for data in students_data:
            student, created = Student.objects.get_or_create(
                name=data['name'],
                school=school,
                defaults={
                    'grade': data['grade'],
                    'balance': data['balance'],
                }
            )
            students.append(student)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Estudiante: {student.name}'))

        # --- 3. Crear padres y vincular ---
        parents_data = [
            {
                'phone': '+573001234567',
                'name': 'Carlos Pérez',
                'students': [students[0], students[1]]
            },
            {
                'phone': '+573106085252',
                'name': 'Ana Gómez',
                'students': [students[2]]
            },
        ]

        for p_data in parents_data:
            parent, created = Parent.objects.get_or_create(
                phone_e164=p_data['phone'],
                defaults={'name': p_data['name']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Padre creado: {parent.name} ({parent.phone_e164})'))
            
            # Vincular estudiantes
            for student in p_data['students']:
                if student not in parent.students.all():
                    parent.students.add(student)
                    self.stdout.write(self.style.SUCCESS(f'  → Vinculado a {student.name}'))

        # --- 4. Crear productos ---
        products_data = [
            {
                'name': 'Coca-Cola 400ml',
                'category': 'Bebidas',
                'price': 1500,
                'allergens': [],
                'nutrition': {'high_sugar': True, 'high_sodium': False, 'high_fat': False}
            },
            {
                'name': 'Papas Margarita 45g',
                'category': 'Snacks',
                'price': 2200,
                'allergens': ['maní'],
                'nutrition': {'high_sugar': False, 'high_sodium': True, 'high_fat': True}
            },
            {
                'name': 'Manzana Roja',
                'category': 'Frutas',
                'price': 1800,
                'allergens': [],
                'nutrition': {'high_sugar': False, 'high_sodium': False, 'high_fat': False}
            },
            {
                'name': 'Detodito',
                'category': 'Snacks',
                'price': 2000,
                'allergens': ['maní', 'leche'],
                'nutrition': {'high_sugar': True, 'high_sodium': True, 'high_fat': True}
            },
            {
                'name': 'Jugo Natural Naranja',
                'category': 'Bebidas',
                'price': 2800,
                'allergens': [],
                'nutrition': {'high_sugar': True, 'high_sodium': False, 'high_fat': False}
            },
        ]

        products = []
        for p_data in products_data:
            product, created = Product.objects.get_or_create(
                name=p_data['name'],
                defaults={
                    'category': p_data['category'],
                    'price': p_data['price']
                }
            )
            products.append(product)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Producto: {product.name}'))

            # Agregar alérgenos
            for allergen_name in p_data['allergens']:
                ProductAllergen.objects.get_or_create(
                    product=product,
                    allergen_name=allergen_name
                )

            # Agregar nutrición
            NutritionFact.objects.get_or_create(
                product_name=product.name,
                defaults=p_data['nutrition']
            )

        # --- 5. Crear inventario (stock) ---
        for product in products:
            inventory, created = Inventory.objects.get_or_create(
                school=school,
                product=product,
                defaults={
                    'current_stock': 50,
                    'minimum_stock': 10
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Stock inicial: {product.name} ({inventory.current_stock})'))

        # --- 6. Crear transacciones de HOY (00:00–23:59:59) ---
        today = timezone.now().date()
        start_of_today = timezone.make_aware(
            datetime.combine(today, datetime.min.time())
        )
        end_of_today = timezone.make_aware(
            datetime.combine(today, datetime.max.time())
        )

        transactions_data = [
            # Juan Pérez
            {'student': students[0], 'product': products[0], 'quantity': 2, 'price': 1500, 'created_at': start_of_today + timedelta(hours=10)},
            {'student': students[0], 'product': products[2], 'quantity': 1, 'price': 1800, 'created_at': start_of_today + timedelta(hours=11)},
            # María Gómez
            {'student': students[1], 'product': products[1], 'quantity': 1, 'price': 2200, 'created_at': start_of_today + timedelta(hours=12)},
            {'student': students[1], 'product': products[4], 'quantity': 1, 'price': 2800, 'created_at': start_of_today + timedelta(hours=13)},
            # Carlos López
            {'student': students[2], 'product': products[3], 'quantity': 1, 'price': 2000, 'created_at': start_of_today + timedelta(hours=14)},
            {'student': students[2], 'product': products[2], 'quantity': 2, 'price': 1800, 'created_at': start_of_today + timedelta(hours=15)},
            {'student': students[2], 'product': products[0], 'quantity': 1, 'price': 1500, 'created_at': start_of_today + timedelta(hours=16)},
        ]

        for t_data in transactions_data:
            Transaction.objects.get_or_create(
                student=t_data['student'],
                product=t_data['product'],
                quantity=t_data['quantity'],
                price=t_data['price'],
                defaults={'created_at': t_data['created_at']}
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Transacción: {t_data["student"].name} → {t_data["product"].name}'))

        # --- 7. Crear recargas ---
        Recarga.objects.get_or_create(
            student=students[0],
            valor=10000,
            fecha=start_of_today + timedelta(hours=9),
            defaults={'description': 'Recarga inicial'}
        )
        self.stdout.write(self.style.SUCCESS('✓ Recarga inicial creada'))

        # --- 8. Crear notificaciones de ejemplo ---
        Notification.objects.get_or_create(
            school=school,
            title='Bienvenidos a BioFood',
            message='Tu colegio ya está configurado. ¡Comienza a usar el sistema!',
            priority='LOW',
            type='GENERAL',
            defaults={'created_at': timezone.now()}
        )
        self.stdout.write(self.style.SUCCESS('✓ Notificación de bienvenida creada'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Seeder completado con éxito.'))
        self.stdout.write(self.style.SUCCESS(f'→ Colegio: {school.name}'))
        self.stdout.write(self.style.SUCCESS(f'→ Estudiantes: {len(students)}'))
        self.stdout.write(self.style.SUCCESS(f'→ Transacciones de hoy: {len(transactions_data)}'))