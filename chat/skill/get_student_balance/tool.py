from langchain.tools import tool
from django.db import connection

@tool
def get_student_balance(parent_phone: str, student_name: str) -> str:
    """
    Obtiene el saldo actual en la billetera digital de un estudiante vinculado al número de teléfono del padre.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.name, s.balance
                FROM parent_parent p
                JOIN parent_parent_students pps ON p.id = pps.parent_id
                JOIN student_student s ON pps.student_id = s.id
                WHERE p.phone_e164 = %s AND UPPER(s.name) LIKE UPPER(%s)
                LIMIT 1
            """, [parent_phone, f'%{student_name}%'])
            row = cursor.fetchone()

        if not row:
            return f"No se encontró un estudiante llamado {student_name} vinculado a este número."

        name, balance = row
        return f"El saldo actual de {name} es de ${float(balance):.2f}."
    except Exception as e:
        return f"Error al consultar el saldo: {str(e)}"
