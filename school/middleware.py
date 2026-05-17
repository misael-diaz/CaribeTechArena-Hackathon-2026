import time
import logging
from django.conf import settings
from school.models import EndpointMetric

logger = logging.getLogger(__name__)

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, 'METRICS_ENABLED', False):
            return self.get_response(request)

        # Skip static/media files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)

        start_time = time.time()
        try:
            response = self.get_response(request)
            response_time_ms = (time.time() - start_time) * 1000
            EndpointMetric.objects.create(
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            )
            return response
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            EndpointMetric.objects.create(
                endpoint=request.path,
                method=request.method,
                status_code=500,
                response_time_ms=response_time_ms,
            )
            logger.error(f"Error en endpoint {request.path}: {e}")
            raise
