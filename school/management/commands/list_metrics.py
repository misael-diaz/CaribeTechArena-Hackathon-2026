from django.core.management.base import BaseCommand
from school.models import EndpointMetric
from django.utils import timezone


class Command(BaseCommand):
    help = 'Lista las últimas métricas de endpoints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Número de métricas a mostrar (default: 20)'
        )
        parser.add_argument(
            '--last-hours',
            type=int,
            default=None,
            help='Filtrar métricas de las últimas N horas'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        last_hours = options['last_hours']

        queryset = EndpointMetric.objects.all().order_by('-created_at')

        if last_hours:
            from datetime import timedelta
            cutoff = timezone.now() - timedelta(hours=last_hours)
            queryset = queryset.filter(created_at__gte=cutoff)

        metrics = queryset[:limit]

        self.stdout.write(self.style.SUCCESS(f'\nÚltimas {len(metrics)} métricas:\n'))
        self.stdout.write(self.style.SQL_KEYWORD('┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐'))
        self.stdout.write(self.style.SQL_KEYWORD('│  #   Endpoint                     Método  Status  Tiempo(ms)  Hora                │'))
        self.stdout.write(self.style.SQL_KEYWORD('├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤'))

        for i, m in enumerate(metrics, 1):
            endpoint = m.endpoint[:45] + '...' if len(m.endpoint) > 45 else m.endpoint
            method = m.method.ljust(6)
            status = str(m.status_code).ljust(6)
            time_ms = f'{m.response_time_ms:.0f}'.ljust(8)
            time_str = m.created_at.strftime('%H:%M:%S')
            self.stdout.write(
                f'│ {i:2}   {endpoint:<45} {method} {status} {time_ms} {time_str} │'
            )

        self.stdout.write(self.style.SQL_KEYWORD('└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘'))
        self.stdout.write(self.style.SUCCESS(f'\nTotal registradas: {EndpointMetric.objects.count()}'))
        if last_hours:
            self.stdout.write(self.style.SUCCESS(f'Últimas {last_hours}h: {queryset.count()}'))