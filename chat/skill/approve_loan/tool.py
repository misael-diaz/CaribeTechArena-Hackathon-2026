from langchain.tools import tool


@tool
def approve_loan(approval_token: str, action: str = "approve") -> str:
    """
    Aprueba o rechaza un prestamo usando el token de aprobacion.
    
    Cuando un estudiante se queda sin saldo, se puede solicitar un prestamo.
    El padre recibe un token unico para aprobar o rechazar la transaccion.
    
    Args:
        approval_token: Token unico de aprobacion (se envia al padre)
        action: "approve" o "reject" (por defecto: "approve")
    
    Returns:
        Mensaje confirmando la aprobacion o rechazo del prestamo
    """
    try:
        from transaction.services import LoanService
        
        service = LoanService()
        
        if action.lower() == "reject":
            loan = service.reject_loan(approval_token)
            if loan:
                return (
                    f"Prestamo RECHAZADO exitosamente.\n\n"
                    f"Detalles:\n"
                    f"- Estudiante: {loan.student.name}\n"
                    f"- Monto: ${loan.amount}\n"
                    f"- Estado: {loan.status}\n\n"
                    f"El prestamo ha sido cancelado."
                )
            else:
                return "No se encontro el prestamo con este token o ya fue procesado."
        else:
            # Aprobar por defecto
            loan = service.approve_loan(approval_token)
            
            if loan:
                return (
                    f"Prestamo APROBADO exitosamente!\n\n"
                    f"Detalles:\n"
                    f"- Estudiante: {loan.student.name}\n"
                    f"- Monto: ${loan.amount}\n"
                    f"- Estado: {loan.status}\n\n"
                    f"Se han agregado ${loan.amount} al saldo de {loan.student.name}.\n"
                    f"Este monto se cargara a tu cuenta como deuda."
                )
            else:
                return (
                    "No se pudo aprobar el prestamo. Posibles razones:\n"
                    "- Token invalido o expirado\n"
                    "- El prestamo ya fue procesado\n\n"
                    "Verifica el token e intenta nuevamente."
                )
        
    except Exception as e:
        return f"Error al procesar prestamo: {str(e)}"


@tool
def get_pending_loans(parent_phone: str) -> str:
    """
    Obtiene lista de prestamos pendientes de aprobacion para un padre.
    
    Args:
        parent_phone: Telefono del padre en formato E.164 (ej: +573001234567)
    
    Returns:
        Lista de prestamos pendientes con detalles
    """
    try:
        from transaction.services import LoanService
        
        service = LoanService()
        loans = service.get_pending_loans_for_parent(parent_phone)
        
        if not loans:
            return "No tienes prestamos pendientes de aprobacion."
        
        response = f"Prestamos Pendientes ({len(loans)}):\n\n"
        
        for loan in loans:
            response += (
                f"Estudiante: {loan['student_name']}\n"
                f"Monto: ${loan['amount']}\n"
                f"Solicitado: {loan['created_at']}\n"
                f"Token: {loan['approval_token'][:16]}...\n"
                f"Para aprobar: usa approve_loan con este token\n\n"
            )
        
        return response.strip()
        
    except Exception as e:
        return f"Error al obtener prestamos: {str(e)}"


@tool
def get_loan_summary(parent_phone: str) -> str:
    """
    Obtiene resumen de todos los prestamos de un padre.
    
    Args:
        parent_phone: Telefono del padre en formato E.164
    
    Returns:
        Resumen con cantidad de prestamos y deuda total
    """
    try:
        from transaction.services import LoanService
        
        service = LoanService()
        summary = service.get_loan_summary(parent_phone)
        
        if 'error' in summary:
            return f"Error: {summary['error']}"
        
        response = (
            f"=== RESUMEN DE PRESTAMOS ===\n\n"
            f"Pendientes de aprobacion: {summary['pending_count']}\n"
            f"Aprobados (activos): {summary['approved_count']}\n"
            f"Pagados: {summary['paid_count']}\n\n"
            f"DEUDA TOTAL: ${summary['total_debt']:.2f}\n\n"
            f"Los prestamos pendientes cuentan como deuda hasta que sean aprobados o rechazados."
        )
        
        return response
        
    except Exception as e:
        return f"Error al obtener resumen: {str(e)}"
