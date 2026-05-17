from langchain.tools import tool
from django.db import connection


@tool
def get_available_products(parent_phone: str, student_name: str) -> str:
    """
    Lista los productos disponibles (con stock) en la cafeteria del colegio de un hijo.
    Usa esta herramienta cuando un padre quiera ver que puede comprar para su hijo.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.id, s.name, s.school_id
                FROM parent_parent p
                JOIN parent_parent_students pps ON p.id = pps.parent_id
                JOIN student_student s ON pps.student_id = s.id
                WHERE p.phone_e164 = %s AND UPPER(s.name) LIKE UPPER(%s)
                LIMIT 1
            """, [parent_phone, f'%{student_name}%'])
            student = cursor.fetchone()

        if not student:
            return f"No se encontro un estudiante llamado *{student_name}* vinculado a tu numero."

        student_id, student_db_name, school_id = student

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT pr.name, pr.price, pr.category, inv.current_stock
                FROM cafeteria_inventory inv
                JOIN product_product pr ON inv.product_id = pr.id
                WHERE inv.school_id = %s AND inv.current_stock > 0
                ORDER BY pr.category, pr.name
            """, [school_id])
            products = cursor.fetchall()

        if not products:
            return f"No hay productos disponibles en la cafeteria de *{student_db_name}* en este momento."

        lines = [f"Productos disponibles para *{student_db_name}*:"]
        current_cat = None
        for name, price, category, stock in products:
            if category != current_cat:
                lines.append(f"")
                current_cat = category
            lines.append(f"* {name} - ${float(price):.2f}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error al consultar productos: {str(e)}"
