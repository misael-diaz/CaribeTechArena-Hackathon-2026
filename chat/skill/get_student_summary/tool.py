from langchain.tools import tool


@tool
def get_student_summary(parent_phone: str, student_name: str = "") -> str:
    """
    Obtiene resumen completo de un estudiante: saldo, forecast, compras,
    alergenicos y nutricion.
    
    Combina multiple informacion en una sola consulta:
    - Saldo actual y forecast de agotamiento
    - Ultimas 5 compras realizadas
    - Ultimas 3 recargas
    - Alergenicos registrados
    - Tendencia de gasto
    
    Args:
        parent_phone: Telefono del padre en formato E.164
        student_name: Nombre del estudiante (opcional si solo tiene 1 hijo)
    
    Returns:
        Mensaje completo con toda la informacion del estudiante
    """
    try:
        from chat.services import StudentSummaryService
        
        service = StudentSummaryService()
        
        # Obtener resumen
        if student_name:
            summary = service.get_full_summary(parent_phone, student_name)
        else:
            # Intentar obtener unico hijo
            summary = service.get_full_summary(parent_phone)
        
        # Formatear como texto
        return service.format_summary_text(summary)
        
    except Exception as e:
        return f"Error al obtener resumen: {str(e)}"


@tool
def get_multi_student_summary(parent_phone: str) -> str:
    """
    Obtiene resumen de TODOS los estudiantes de un padre.
    
    Util cuando el padre tiene varios hijos y quiere ver
    el estado de cada uno en una sola consulta.
    
    Args:
        parent_phone: Telefono del padre en formato E.164
    
    Returns:
        Mensaje con resumen de todos los hijos
    """
    try:
        from chat.services import StudentSummaryService
        
        service = StudentSummaryService()
        multi_summary = service.get_multi_student_summary(parent_phone)
        
        return service.format_multi_student_text(multi_summary)
        
    except Exception as e:
        return f"Error al obtener resumen multiple: {str(e)}"
