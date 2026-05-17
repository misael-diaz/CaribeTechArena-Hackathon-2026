from langchain.tools import tool
from django.db import connection

@tool
def get_recent_recharges(parent_phone: str, student_name: str) -> str:
    """
    Obtiene las últimas 3 recargas realizadas a la cuenta de un estudiante vinculado al número de teléfono del padre.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT printf('%.2f', r.valor), r.fecha
                FROM transaction_recarga r
                JOIN parent_parent_students pps ON r.student_id = (
                    SELECT s.id FROM parent_parent p
                    JOIN parent_parent_students pps2 ON p.id = pps2.parent_id
                    JOIN student_student s ON pps2.student_id = s.id
                    WHERE p.phone_e164 = %s AND UPPER(s.name) LIKE UPPER(%s)
                    LIMIT 1
                )
                ORDER BY r.fecha DESC
                LIMIT 3
            """, [parent_phone, f'%{student_name}%'])
            recharges = cursor.fetchall()

        if not recharges:
            return f"No hay registros de recargas recientes para {student_name}."

        recharge_info = [f"${valor} el {fecha}" for valor, fecha in recharges]
        return f"Últimas recargas de {student_name}: {', '.join(recharge_info)}."
    except Exception as e:
        return f"Error al consultar recargas: {str(e)}"
