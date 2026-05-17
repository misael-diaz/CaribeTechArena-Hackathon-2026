from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from school.models import School, SchoolUser


class Command(BaseCommand):
    help = 'Crea un usuario de prueba para el colegio'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin',
                            help='Nombre de usuario')
        parser.add_argument('--password', type=str, default='admin123',
                            help='Contrasena')
        parser.add_argument('--school', type=str, default='Test School',
                            help='Nombre del colegio')
        parser.add_argument('--role', type=str, default='ADMIN',
                            choices=['ADMIN', 'CAFETERIA', 'SECRETARIA'],
                            help='Rol del usuario')
        parser.add_argument('--email', type=str, default='admin@test.com',
                            help='Email del usuario')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        school_name = options['school']
        role = options['role']
        email = options['email']

        # Crear o obtener colegio
        school, created = School.objects.get_or_create(name=school_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Colegio "{school_name}" creado'))
        else:
            self.stdout.write(f'Colegio "{school_name}" ya existe')

        # Crear usuario Django
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            self.stdout.write(f'Usuario "{username}" ya existe')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS(f'Usuario "{username}" creado'))

        # Crear o actualizar perfil de usuario de colegio
        school_user, created = SchoolUser.objects.get_or_create(
            user=user,
            defaults={
                'school': school,
                'role': role,
                'phone': '+573001234567'
            }
        )

        if not created:
            school_user.school = school
            school_user.role = role
            school_user.save()
            self.stdout.write(f'Perfil de usuario actualizado')

        # Asignar permisos
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.stdout.write(self.style.SUCCESS('\n=== CREDENCIALES ==='))
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'School: {school_name}')
        self.stdout.write(f'Role: {role}')
        self.stdout.write(self.style.SUCCESS('\nURL de login: /school/login/'))
