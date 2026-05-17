from langchain.tools import tool
from django.db import connection

@tool
def get_student_allergens(parent_phone: str, student_name: str) -> str:
    """
    Obtiene la lista de alergias registradas para un estudiante vinculado al número de teléfono del padre.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.name, COALESCE(STRING_AGG(sa.allergen_name, ', ' ORDER BY sa.allergen_name), '') as allergens
                FROM parent_parent p
                JOIN parent_parent_students pps ON p.id = pps.parent_id
                JOIN student_student s ON pps.student_id = s.id
                LEFT JOIN student_studentallergen sa ON s.id = sa.student_id
                WHERE p.phone_e164 = %s AND UPPER(s.name) LIKE UPPER(%s)
                GROUP BY s.name
                LIMIT 1
            """, [parent_phone, f'%{student_name}%'])
            row = cursor.fetchone()

        if not row:
            return f"No se encontró un estudiante llamado {student_name} vinculado a este número."

        name, allergens = row
        if not allergens:
            return f"{name} no tiene ninguna alergia registrada."

        return f"Alergias registradas para {name}: {allergens}."
    except Exception as e:
        return f"Error al consultar alergias: {str(e)}"
