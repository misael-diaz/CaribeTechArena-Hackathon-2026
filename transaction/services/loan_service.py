"""
Servicio para gestion de prestamos (Loans).
Permite crear, aprobar y gestionar prestamos cuando estudiantes se quedan sin saldo.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from transaction.models import Loan, Transaction
from student.models import Student

logger = logging.getLogger(__name__)


class LoanService:
    """
    Servicio para gestion de prestamos temporales.
    """
    
    # Monto maximo de prestamo por defecto
    DEFAULT_MAX_LOAN = 10.00
    # Maximo de prestamos pendientes por padre
    MAX_PENDING_LOANS = 3
    
    def __init__(self):
        pass
    
    def can_request_loan(self, student: Student) -> Dict[str, Any]:
        """
        Verifica si un estudiante puede solicitar un prestamo.
        
        Args:
            student: Estudiante que solicita el prestamo
        
        Returns:
            Dict con:
                - can_request: Boolean
                - reason: String explicando por que
                - max_amount: Monto maximo permitido
        """
        # Verificar si tiene saldo (no deberia pedir prestamo si tiene saldo)
        if float(student.balance) > 0:
            return {
                'can_request': False,
                'reason': 'El estudiante tiene saldo disponible',
                'max_amount': 0
            }
        
        # Verificar prestamos pendientes del padre
        from parent.models import Parent
        parent = Parent.objects.filter(students=student).first()
        
        if not parent:
            return {
                'can_request': False,
                'reason': 'No se encontro el padre del estudiante',
                'max_amount': 0
            }
        
        pending_loans = Loan.objects.filter(
            parent=parent,
            status='PENDING'
        ).count()
        
        if pending_loans >= self.MAX_PENDING_LOANS:
            return {
                'can_request': False,
                'reason': f'Maximo de {self.MAX_PENDING_LOANS} prestamos pendientes alcanzado',
                'max_amount': 0
            }
        
        # Verificar deuda total del padre
        total_debt = Loan.objects.filter(
            parent=parent,
            status__in=['PENDING', 'APPROVED']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        max_allowed = self.DEFAULT_MAX_LOAN * 3  # Maximo 3 veces el prestamo base
        
        if float(total_debt) >= max_allowed:
            return {
                'can_request': False,
                'reason': f'Deuda total (${total_debt}) excede el limite (${max_allowed})',
                'max_amount': 0
            }
        
        return {
            'can_request': True,
            'reason': 'Elegible para prestamo',
            'max_amount': self.DEFAULT_MAX_LOAN
        }
    
    def request_loan(
        self,
        student: Student,
        amount: float,
        transaction: Optional[Transaction] = None
    ) -> Optional[Loan]:
        """
        Solicita un prestamo para un estudiante.
        
        Args:
            student: Estudiante que solicita el prestamo
            amount: Monto del prestamo
            transaction: Transaccion que origino el prestamo (opcional)
        
        Returns:
            Loan creado o None si no se pudo crear
        """
        # Verificar si puede solicitar
        eligibility = self.can_request_loan(student)
        
        if not eligibility['can_request']:
            logger.warning(
                f"Estudiante {student.name} no elegible para prestamo: {eligibility['reason']}"
            )
            return None
        
        # Obtener padre
        from parent.models import Parent
        parent = Parent.objects.filter(students=student).first()
        
        if not parent:
            logger.error(f"No se encontro padre para estudiante {student.id}")
            return None
        
        # Crear prestamo
        loan = Loan.objects.create(
            student=student,
            parent=parent,
            amount=amount,
            status='PENDING',
            transaction=transaction
        )
        
        # ENVIAR WHATSAPP AL PADRE
        self._send_loan_notification(parent, student, amount, loan.approval_token)
        
        logger.info(
            f"Prestamo solicitado: ${amount} para {student.name}, "
            f"padre: {parent.phone_e164}, token: {loan.approval_token[:8]}..."
        )
        
        return loan
    
    def _send_loan_notification(
        self,
        parent,
        student: Student,
        amount: float,
        approval_token: str
    ):
        """
        Envía notificación WhatsApp al padre sobre el préstamo solicitado.
        
        Args:
            parent: Padre a notificar
            student: Estudiante que solicitó el préstamo
            amount: Monto del préstamo
            approval_token: Token para aprobar
        """
        from chat.twilio_service import TwilioService
        
        # Construir mensaje
        approval_url = f"https://biofood.app/loan/approve/{approval_token}/"
        
        message = (
            f"🔔 SOLICITUD DE PRESTAMO BioFood\n\n"
            f"Tu hijo/a {student.name} se quedo sin saldo y solicita un prestamo de ${amount}.\n\n"
            f"¿Quieres aprobar este prestamo?\n"
            f"- Se cargara a tu cuenta como deuda\n"
            f"- Podras pagarlo con tu proxima recarga\n\n"
            f"Para APROBAR responde: SI\n"
            f"Para RECHAZAR responde: NO\n\n"
            f"O usa este link: {approval_url}\n\n"
            f"Token: {approval_token[:16]}..."
        )
        
        # Enviar WhatsApp
        twilio = TwilioService()
        message_sid = twilio.send_message(parent.phone_e164, message)
        
        if message_sid:
            logger.info(
                f"Notificación de préstamo enviada a {parent.phone_e164} | "
                f"Student: {student.name} | Amount: ${amount}"
            )
        else:
            logger.warning(
                f"Twilio no envió notificación de préstamo (posible modo mock) | "
                f"Phone: {parent.phone_e164}"
            )
    
    def approve_loan(self, approval_token: str) -> Optional[Loan]:
        """
        Aprueba un prestamo usando el token de aprobacion.
        
        Args:
            approval_token: Token unico de aprobacion
        
        Returns:
            Loan aprobado o None si no se encontro
        """
        try:
            loan = Loan.objects.get(approval_token=approval_token)
            
            if loan.status != 'PENDING':
                logger.warning(f"Prestamo {loan.id} ya no esta pendiente (estado: {loan.status})")
                return None
            
            # Aprobar prestamo
            loan.status = 'APPROVED'
            loan.approved_at = timezone.now()
            loan.save()
            
            # Agregar saldo al estudiante
            student = loan.student
            student.balance = float(student.balance) + float(loan.amount)
            student.save()
            
            logger.info(
                f"Prestamo {loan.id} aprobado. ${loan.amount} agregados a {student.name}"
            )
            
            return loan
            
        except Loan.DoesNotExist:
            logger.error(f"Token de aprobacion invalido: {approval_token[:8]}...")
            return None
    
    def reject_loan(self, approval_token: str) -> Optional[Loan]:
        """
        Rechaza un prestamo usando el token de aprobacion.
        
        Args:
            approval_token: Token unico de aprobacion
        
        Returns:
            Loan rechazado o None si no se encontro
        """
        try:
            loan = Loan.objects.get(approval_token=approval_token)
            
            if loan.status != 'PENDING':
                return None
            
            loan.status = 'REJECTED'
            loan.save()
            
            logger.info(f"Prestamo {loan.id} rechazado")
            
            return loan
            
        except Loan.DoesNotExist:
            return None
    
    def pay_loan(self, loan_id: int) -> Optional[Loan]:
        """
        Marca un prestamo como pagado.
        
        Args:
            loan_id: ID del prestamo
        
        Returns:
            Loan pagado o None si no se encontro
        """
        try:
            loan = Loan.objects.get(id=loan_id)
            
            if loan.status != 'APPROVED':
                logger.warning(f"Prestamo {loan.id} no esta aprobado (estado: {loan.status})")
                return None
            
            # Descontar saldo del estudiante (si tiene)
            student = loan.student
            current_balance = float(student.balance)
            
            if current_balance >= float(loan.amount):
                student.balance = current_balance - float(loan.amount)
                student.save()
                loan.status = 'PAID'
                loan.paid_at = timezone.now()
                loan.save()
                
                logger.info(f"Prestamo {loan.id} pagado por {student.name}")
                return loan
            else:
                logger.warning(
                    f"Estudiante {student.name} no tiene saldo suficiente para pagar prestamo {loan.id}"
                )
                return None
                
        except Loan.DoesNotExist:
            return None
    
    def get_pending_loans_for_parent(self, parent_phone: str) -> List[Dict[str, Any]]:
        """
        Obtiene prestamos pendientes de un padre.
        
        Args:
            parent_phone: Telefono del padre en formato E.164
        
        Returns:
            Lista de prestamos pendientes
        """
        from parent.models import Parent
        
        parent = Parent.objects.filter(phone_e164=parent_phone).first()
        
        if not parent:
            return []
        
        loans = Loan.objects.filter(
            parent=parent,
            status='PENDING'
        ).order_by('-created_at')
        
        result = []
        for loan in loans:
            result.append({
                'id': loan.id,
                'student_name': loan.student.name,
                'amount': str(loan.amount),
                'created_at': loan.created_at.strftime('%d/%m/%Y %H:%M'),
                'approval_token': loan.approval_token
            })
        
        return result
    
    def get_loan_summary(self, parent_phone: str) -> Dict[str, Any]:
        """
        Obtiene resumen de prestamos de un padre.
        
        Args:
            parent_phone: Telefono del padre
        
        Returns:
            Dict con resumen de prestamos
        """
        from parent.models import Parent
        
        parent = Parent.objects.filter(phone_e164=parent_phone).first()
        
        if not parent:
            return {'error': 'Padre no encontrado'}
        
        pending = Loan.objects.filter(parent=parent, status='PENDING').count()
        approved = Loan.objects.filter(parent=parent, status='APPROVED').count()
        paid = Loan.objects.filter(parent=parent, status='PAID').count()
        
        total_debt = Loan.objects.filter(
            parent=parent,
            status__in=['PENDING', 'APPROVED']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'parent_phone': parent_phone,
            'pending_count': pending,
            'approved_count': approved,
            'paid_count': paid,
            'total_debt': float(total_debt)
        }
