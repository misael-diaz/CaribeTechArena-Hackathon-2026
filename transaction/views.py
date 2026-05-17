import json
import logging
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from transaction.services import LoanService
from student.models import Student
from parent.models import Parent

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def request_loan_api(request):
    """
    API para solicitar un prestamo cuando el estudiante se queda sin saldo.
    """
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        amount = Decimal(str(data.get('amount', 0)))
        transaction_id = data.get('transaction_id')
        
        if not student_id:
            return JsonResponse({'success': False, 'error': 'student_id es requerido'}, status=400)
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Estudiante no encontrado'}, status=404)
        
        transaction = None
        if transaction_id:
            from transaction.models import Transaction
            try:
                transaction = Transaction.objects.get(id=transaction_id)
            except Transaction.DoesNotExist:
                pass
        
        service = LoanService()
        loan = service.request_loan(student, amount, transaction)
        
        if not loan:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo solicitar el prestamo. Verifique elegibilidad.'
            }, status=400)
        
        approval_url = f"https://biofood.app/loan/approve/{loan.approval_token}/"
        
        return JsonResponse({
            'success': True,
            'loan_id': loan.id,
            'amount': str(loan.amount),
            'student_name': student.name,
            'approval_url': approval_url,
            'message': f'Se solicito prestamo de ${amount}. El padre debe aprobarlo.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalido'}, status=400)
    except Exception as e:
        logger.error(f"Error en request_loan_api: {e}")
        return JsonResponse({'success': False, 'error': 'Error interno'}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def approve_loan_api(request, approval_token):
    """
    API para aprobar un prestamo con el token.
    """
    try:
        service = LoanService()
        
        if request.method == 'POST':
            loan = service.approve_loan(approval_token)
            
            if loan:
                return JsonResponse({
                    'success': True,
                    'loan_id': loan.id,
                    'status': loan.status,
                    'amount': str(loan.amount),
                    'student_name': loan.student.name,
                    'message': f'Prestamo aprobado. ${loan.amount} agregados.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Token invalido o prestamo ya procesado'
                }, status=400)
        else:
            from transaction.models import Loan
            try:
                loan = Loan.objects.get(approval_token=approval_token)
                return JsonResponse({
                    'success': True,
                    'loan_id': loan.id,
                    'status': loan.status,
                    'amount': str(loan.amount),
                    'student_name': loan.student.name,
                    'message': f'Prestamo de ${loan.amount} para {loan.student.name}'
                })
            except Loan.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Token invalido'}, status=404)
        
    except Exception as e:
        logger.error(f"Error en approve_loan_api: {e}")
        return JsonResponse({'success': False, 'error': 'Error interno'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def reject_loan_api(request, approval_token):
    """API para rechazar un prestamo con el token."""
    try:
        service = LoanService()
        loan = service.reject_loan(approval_token)
        
        if loan:
            return JsonResponse({
                'success': True,
                'loan_id': loan.id,
                'status': loan.status,
                'message': 'Prestamo rechazado.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Token invalido o prestamo ya procesado'
            }, status=400)
        
    except Exception as e:
        logger.error(f"Error en reject_loan_api: {e}")
        return JsonResponse({'success': False, 'error': 'Error interno'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def pending_loans_api(request):
    """API para obtener prestamos pendientes de un padre."""
    try:
        parent_phone = request.GET.get('parent_phone')
        
        if not parent_phone:
            return JsonResponse({'success': False, 'error': 'parent_phone es requerido'}, status=400)
        
        service = LoanService()
        loans = service.get_pending_loans_for_parent(parent_phone)
        
        return JsonResponse({'success': True, 'loans': loans})
        
    except Exception as e:
        logger.error(f"Error en pending_loans_api: {e}")
        return JsonResponse({'success': False, 'error': 'Error interno'}, status=500)

