from langchain.tools import tool


@tool
def get_balance_forecast(parent_phone: str, student_name: str) -> str:
    """
    Calcula cuando se acabara el saldo de un estudiante y recomienda monto de recarga.
    
    Usa pandas para analisis avanzado:
    - Promedio de gasto de ultimos 30 dias con media movil
    - Deteccion de outliers (compras atipicas)
    - Tendencia de gasto (subiendo/bajando/estable)
    - Patrones por dia de semana
    - Margen de error estimado (+/- 2 dias)
    
    Args:
        parent_phone: Numero de telefono del padre en formato E.164
        student_name: Nombre (o parte del nombre) del estudiante
    
    Returns:
        Mensaje con saldo actual, dias estimados hasta agotar, fecha estimada,
        tendencia de gasto, nivel de confianza, y monto recomendado de recarga.
    """
    try:
        from parent.models import Parent
        from student.models import Student
        from student.services import BalanceForecastService
        
        # Buscar padre
        parent = Parent.objects.filter(phone_e164=parent_phone).first()
        if not parent:
            return f"No se encontro un padre registrado con el numero {parent_phone}."
        
        # Buscar estudiante
        student = parent.students.filter(name__icontains=student_name).first()
        if not student:
            return f"No se encontro un estudiante llamado '{student_name}' vinculado a este numero."
        
        # Usar el servicio con pandas
        service = BalanceForecastService(days_window=30)
        return service.get_forecast_summary(student)
        
    except Exception as e:
        return f"Error al calcular el pronostico de saldo: {str(e)}"
