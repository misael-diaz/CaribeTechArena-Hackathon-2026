import time
import logging
from functools import wraps
from django.conf import settings
from school.models import EndpointMetric

logger = logging.getLogger(__name__)


def track_endpoint(view_func):
    """
    Decorador para monitorear endpoints HTTP.
    Registra: endpoint, método, status_code y tiempo de respuesta.
    Solo activo si settings.METRICS_ENABLED = True.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(settings, 'METRICS_ENABLED', False):
            return view_func(request, *args, **kwargs)

        start_time = time.time()
        try:
            response = view_func(request, *args, **kwargs)
            
            # Calcular tiempo en ms
            response_time_ms = (time.time() - start_time) * 1000
            
            # Registrar métrica
            EndpointMetric.objects.create(
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
            
            return response
        except Exception as e:
            # Si falla el view, registrar error
            response_time_ms = (time.time() - start_time) * 1000
            EndpointMetric.objects.create(
                endpoint=request.path,
                method=request.method,
                status_code=500,
                response_time_ms=response_time_ms
            )
            logger.error(f"Error en endpoint {request.path}: {e}")
            raise

    return wrapper