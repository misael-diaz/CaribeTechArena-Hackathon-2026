from langchain.tools import tool
from django.db import connection


@tool
def get_transaction_history(parent_phone: str, student_name: str, limit: int = 10) -> str:
    """
    Obtiene el historial de compras recientes de un estudiante vinculado al número del padre.
    Muestra qué productos compró, cantidades, precios y fechas.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT t.id, p.name, t.quantity, t.price, t.created_at
                FROM transaction_transaction t
                JOIN product_product p ON t.product_id = p.id
                JOIN student_student s ON t.student_id = s.id
                JOIN parent_parent p_p ON p_p.phone_e164 = %s
                JOIN parent_parent_students pps ON p_p.id = pps.parent_id
                WHERE s.id = pps.student_id AND UPPER(s.name) LIKE UPPER(%s)
                ORDER BY t.created_at DESC
                LIMIT %s
            """, [parent_phone, f'%{student_name}%', limit])
            rows = cursor.fetchall()

        if not rows:
            return f"{student_name} no tiene compras registradas."

        lines = [f"Historial de compras de {student_name}:"]
        for tid, pname, qty, price, created_at in rows:
            total = float(price) * qty
            date_str = created_at.strftime("%d/%m/%Y %H:%M")
            lines.append(f"- {pname} x{qty} — ${total:.2f} ({date_str})")

        return "\n".join(lines)

    except Exception as e:
        return f"Error al consultar historial: {str(e)}"
