from langchain.tools import tool
from django.db import connection


@tool
def get_school_info(parent_phone: str, student_name: str) -> str:
    """
    Obtiene información del colegio de un estudiante vinculado al número del padre.
    Devuelve el nombre del colegio y el grado del estudiante.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.name AS student_name, s.grade, sch.name AS school_name
                FROM student_student s
                JOIN school_school sch ON s.school_id = sch.id
                JOIN parent_parent p ON p.phone_e164 = %s
                JOIN parent_parent_students pps ON p.id = pps.parent_id
                WHERE s.id = pps.student_id AND UPPER(s.name) LIKE UPPER(%s)
                LIMIT 1
            """, [parent_phone, f'%{student_name}%'])
            row = cursor.fetchone()

        if not row:
            return f"No se encontró un estudiante llamado {student_name} vinculado a este número."

        student_name, grade, school_name = row
        return f"{student_name} estudia en *{school_name}*, en el grado {grade}."

    except Exception as e:
        return f"Error al consultar información del colegio: {str(e)}"
