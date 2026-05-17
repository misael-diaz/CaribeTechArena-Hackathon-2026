from langchain.tools import tool


@tool
def check_allergen_safety(parent_phone: str, student_name: str, product_name: str) -> str:
    """
    Verifica si un producto es seguro para un estudiante con alergenicos.

    Usa el ID del producto para verificar si contiene alergenicos que el
    estudiante tiene registrados. Tambien muestra informacion nutricional.

    Args:
        parent_phone: Telefono del padre en formato E.164
        student_name: Nombre del estudiante
        product_name: Nombre del producto (o parte)

    Returns:
        Mensaje indicando si es seguro, alergenicos detectados, y nutricion
    """
    try:
        from student.services import get_student_by_parent_phone
        from product.services import NutritionService
        from student.models import StudentAllergen
        from product.models import Product, ProductAllergen

        # Buscar estudiante
        student = get_student_by_parent_phone(parent_phone, student_name)
        if not student:
            return f"No se encontro un estudiante llamado '{student_name}' vinculado a este numero."

        # Buscar producto
        product = Product.objects.filter(name__icontains=product_name).first()
        if not product:
            return f"No se encontro un producto llamado '{product_name}'."

        # Usar servicio para verificar seguridad
        nutrition_service = NutritionService()
        result = nutrition_service.is_product_safe_for_student(product.id, student.id)

        # Construir respuesta
        if result['is_safe']:
            response = f"SEGURO: {product.name}\n\n"
            response += f"Razon: {result['reason']}\n"
        else:
            response = f"NO SEGURO: {product.name}\n\n"
            response += f"Razon: {result['reason']}\n"
            response += f"Alergenicos detectados: {', '.join(result['matching_allergens'])}\n"

        # Agregar informacion nutricional si existe
        if result['nutrition_info']:
            info = result['nutrition_info']
            flags = info.get('flags', [])
            if flags:
                response += f"\nInformacion nutricional: ALTO EN {', '.join(flags)}"
            else:
                response += f"\nInformacion nutricional: Opcion saludable"

        # Agregar alergenicos del estudiante
        student_allergens = list(
            StudentAllergen.objects
            .filter(student=student)
            .values_list('allergen_name', flat=True)
        )

        if student_allergens:
            response += f"\n\nAlergenicos registrados de {student.name}: {', '.join(student_allergens)}"
        else:
            response += f"\n\n{student.name} no tiene alergenicos registrados."

        return response

    except Exception as e:
        return f"Error al verificar seguridad del producto: {str(e)}"