from langchain.tools import tool
from django.db import connection
from django.utils import timezone
from datetime import date, datetime


@tool
def get_daily_nutrition_summary(parent_phone: str, student_name: str) -> str:
    """
    Resume la ingesta nutricional de un estudiante hoy.

    Calcula estimación de calorías, azúcar, sodio y grasa
    basado en productos consumidos y sus flags nutricionales.

    Args:
        parent_phone: Teléfono del padre en formato E.164
        student_name: Nombre del estudiante

    Returns:
        Resumen nutricional con calorías estimadas y niveles de nutrientes
    """
    # Definir 'hoy' como 00:00–23:59:59 del día actual (zona horaria local)
    today = date.today()
    start_of_today = timezone.make_aware(
        datetime.combine(today, datetime.min.time())
    )
    end_of_today = timezone.make_aware(
        datetime.combine(today, datetime.max.time())
    )

    try:
        with connection.cursor() as cursor:
            # Obtener transacciones de hoy y sus flags nutricionales
            cursor.execute("""
                SELECT
                    p.name,
                    nf.high_sugar,
                    nf.high_sodium,
                    nf.high_fat,
                    t.quantity
                FROM transaction_transaction t
                JOIN student_student s ON t.student_id = s.id
                JOIN parent_parent p_p ON p_p.phone_e164 = %s
                JOIN parent_parent_students pps ON p_p.id = pps.parent_id
                JOIN product_product p ON t.product_id = p.id
                LEFT JOIN nutritionfacts nf ON nf.product_name = p.name
                WHERE s.id = pps.student_id
                AND UPPER(s.name) LIKE UPPER(%s)
                AND t.created_at >= %s
                AND t.created_at <= %s
                ORDER BY t.created_at DESC
                LIMIT 10
            """, [parent_phone, f'%{student_name}%', start_of_today, end_of_today])

            transactions = cursor.fetchall()

        if not transactions:
            return f"{student_name} no ha registrado compras hoy."

        # Cálculos estimados
        total_calories = 0
        sugar_flags = 0
        sodium_flags = 0
        fat_flags = 0
        products_list = []

        for name, high_sugar, high_sodium, high_fat, quantity in transactions:
            # Estimación de calorías por categoría
            name_lower = name.lower()
            if 'coca' in name_lower or 'gaseosa' in name_lower or 'jugo' in name_lower or 'hit' in name_lower:
                calories = 150 * quantity
            elif 'papas' in name_lower or 'detodito' in name_lower or 'boliqueso' in name_lower or 'margarita' in name_lower:
                calories = 250 * quantity
            elif 'fruta' in name_lower or 'manzana' in name_lower or 'platanitos' in name_lower or 'festival' in name_lower:
                calories = 80 * quantity
            else:
                calories = 180 * quantity

            total_calories += calories
            sugar_flags += 1 if high_sugar else 0
            sodium_flags += 1 if high_sodium else 0
            fat_flags += 1 if high_fat else 0
            products_list.append(f"{quantity}x {name}")

        # Resumen
        summary = f"{student_name} consumió hoy:\n"
        summary += f"- Productos: {', '.join(products_list)}\n"
        summary += f"- Calorías estimadas: {total_calories} kcal\n"
        summary += f"- Alto en azúcar: {sugar_flags} productos\n"
        summary += f"- Alto en sodio: {sodium_flags} productos\n"
        summary += f"- Alto en grasa: {fat_flags} productos\n"

        if total_calories > 1500:
            summary += "⚠️ Advertencia: Ingesta calórica alta para un niño."
        elif total_calories < 300:
            summary += "ℹ️ Ingesta calórica baja. Verifica si comió algo más."
        else:
            summary += "✅ Ingesta calórica adecuada para una merienda escolar."

        return summary

    except Exception as e:
        return f"Error al calcular resumen nutricional: {str(e)}"