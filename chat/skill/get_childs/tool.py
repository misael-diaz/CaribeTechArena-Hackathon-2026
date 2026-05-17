from langchain.tools import tool
from django.db import connection

@tool
def get_childs(phone_e164: str) -> str:
    """
    Obtiene la lista de los nombres de los hijos vinculados al número de teléfono del padre.

    Args:
        phone_e164 (str): El número de teléfono del padre (ej. +573001234567).
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.name
                FROM parent_parent p
                JOIN parent_parent_students pps ON p.id = pps.parent_id
                JOIN student_student s ON pps.student_id = s.id
                WHERE p.phone_e164 = %s
                ORDER BY s.name
            """, [phone_e164])
            names = [row[0] for row in cursor.fetchall()]

        if not names:
            return "No tienes hijos registrados o no se encontró un padre con este número."

        return f"Tus hijos registrados son: {', '.join(names)}"
    except Exception as e:
        return f"Error al consultar estudiantes: {str(e)}"
