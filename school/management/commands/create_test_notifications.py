from django.core.management.base import BaseCommand
from django.utils import timezone
from school.models import School, SchoolUser, Notification
from transaction.models import Loan
from datetime import timedelta


class Command(BaseCommand):
    help = 'Crea notificaciones de prueba para el dashboard'

    def handle(self, *args, **options):
        # Obtener primer colegio
        school = School.objects.first()
        if not school:
            self.stdout.write(self.style.ERROR('No hay colegios registrados'))
            return

        # Obtener primer usuario del colegio
        school_user = SchoolUser.objects.filter(school=school).first()
        if not school_user:
            self.stdout.write(self.style.ERROR('No hay usuarios para este colegio'))
            return

        user = school_user.user

        # Crear notificaciones de prueba
        notifications_data = [
            # Prestamos
            {
                'title': 'Nuevo prestamo solicitado',
                'message': 'Juanito Perez solicito un prestamo de $5.00 porque se le agoto el saldo.',
                'priority': 'HIGH',
                'type': 'LOAN',
                'action_url': '/transaction/api/loan/pending/'
            },
            {
                'title': 'Prestamo aprobado',
                'message': 'Maria Rodriguez aprobo el prestamo de $3.50 para su hijo Carlos.',
                'priority': 'MEDIUM',
                'type': 'LOAN',
            },
            # Stock
            {
                'title': 'Stock critico: Gaseosa Coca-Cola',
                'message': 'El producto Coca-Cola 400ml tiene solo 3 unidades restantes (minimo: 10).',
                'priority': 'CRITICAL',
                'type': 'STOCK',
                'action_url': '/cafeteria/inventory/'
            },
            {
                'title': 'Stock bajo: Papas Margarita',
                'message': 'El producto Papas Margarita 45g tiene 8 unidades (minimo: 10).',
                'priority': 'MEDIUM',
                'type': 'STOCK',
            },
            # Alérgenos
            {
                'title': 'ALERTA: Alérgeno detectado',
                'message': 'Juanito Gomez compro un producto que contiene MANI y tiene registrado este alergeno.',
                'priority': 'CRITICAL',
                'type': 'ALLERGEN',
            },
            {
                'title': 'Alerta de alérgeno enviada',
                'message': 'Se envio notificacion a los padres de Maria Lopez sobre compra con alérgenos.',
                'priority': 'HIGH',
                'type': 'ALLERGEN',
            },
            # Balance
            {
                'title': 'Saldo bajo multiple',
                'message': '5 estudiantes tienen saldo menor a $2.00 en el ultimo dia.',
                'priority': 'LOW',
                'type': 'BALANCE',
            },
            # General
            {
                'title': 'Bienvenido al sistema',
                'message': 'Tu cuenta ha sido creada exitosamente. Explora el dashboard para ver las notificaciones.',
                'priority': 'LOW',
                'type': 'GENERAL',
            },
        ]

        created_count = 0
        for data in notifications_data:
            notification = Notification.objects.create(
                school=school,
                user=school_user,
                **data
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'✓ Notificacion creada: {data["title"]}'))

        # Marcar algunas como leidas
        Notification.objects.filter(type='GENERAL').update(
            is_read=True,
            read_at=timezone.now()
        )

        self.stdout.write(self.style.SUCCESS(f'\n{created_count} notificaciones creadas'))
        self.stdout.write(f'Colegio: {school.name}')
        self.stdout.write(f'Usuario: {user.username}')
        self.stdout.write(self.style.SUCCESS('\nIngresa a: http://localhost:8000/school/login/'))
        self.stdout.write('Credenciales: admin / admin123')
