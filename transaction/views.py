import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@csrf_exempt
def placeholder_api(request):
    """Placeholder API endpoint."""
    return JsonResponse({'success': True, 'message': 'OK'})
