from langchain.tools import tool
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta

@tool
def get_one_today_meals(parent_phone: str, student_name: str) -> str:
    """
    Consulta lo que comió hoy un estudiante específico vinculado al número de teléfono del padre.
    Útil para responder preguntas como "¿Qué comió Juan hoy?"
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    try:
        with connection.cursor() as cursor:
            # Consulta optimizada para SQLite usando rango de fechas
            cursor.execute("""
                SELECT t.quantity, p.name
                FROM transaction_transaction t
                JOIN product_product p ON t.product_id = p.id
                WHERE t.student_id = (
                    SELECT s.id FROM parent_parent p
                    JOIN parent_parent_students pps ON p.id = pps.parent_id
                    JOIN student_student s ON pps.student_id = s.id
                    WHERE p.phone_e164 = %s AND UPPER(s.name) LIKE UPPER(%s)
                    LIMIT 1
                )
                AND t.created_at >= %s AND t.created_at < %s
                ORDER BY t.created_at DESC
            """, [parent_phone, f'%{student_name}%', today_start, today_end])

            transactions = cursor.fetchall()

        if not transactions:
            return f"{student_name} no ha registrado compras hoy."

        meals = [f"{qty}x {name}" for qty, name in transactions]
        return f"{student_name} comió hoy: {', '.join(meals)}."
    except Exception as e:
        return f"Error al consultar transacciones: {str(e)}"
