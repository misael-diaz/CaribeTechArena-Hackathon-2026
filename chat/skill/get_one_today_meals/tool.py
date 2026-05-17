from langchain.tools import tool
from django.db import connection
from django.utils import timezone

@tool
def get_one_today_meals(parent_phone: str, student_name: str) -> str:
    """
    Consulta lo que comió hoy un estudiante específico vinculado al número de teléfono del padre.
    Útil para responder preguntas como "¿Qué comió Juan hoy?"
    """
    today = timezone.now().date()
    try:
        with connection.cursor() as cursor:
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
            """, [parent_phone, f'%{student_name}%', today, today.replace(day=today.day + 1) if today.day < 28 else None])
            
            # Re-run with safer date handling if needed
            if not cursor.rowcount:
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
                    AND DATE(t.created_at) = %s
                    ORDER BY t.created_at DESC
                """, [parent_phone, f'%{student_name}%', today])
            
            transactions = cursor.fetchall()

        if not transactions:
            return f"{student_name} no ha registrado compras hoy."

        meals = [f"{qty}x {name}" for qty, name in transactions]
        return f"{student_name} comió hoy: {', '.join(meals)}."
    except Exception as e:
        return f"Error al consultar transacciones: {str(e)}"
