from langchain.tools import tool


@tool
def suggest_healthy_alternatives(parent_phone: str, product_name: str) -> str:
    """
    Sugiere alternativas saludables a un producto no saludable.

    Busca productos similares en la misma categoria que sean
    nutricionalmente mejores (sin flags de azucar, sodio o grasa).

    Args:
        parent_phone: Telefono del padre en formato E.164
        product_name: Nombre del producto actual (o parte)

    Returns:
        Mensaje con alternativas saludables recomendadas
    """
    try:
        from product.models import Product, NutritionFact
        from product.services import NutritionService

        # Buscar producto actual
        product = Product.objects.filter(name__icontains=product_name).first()
        if not product:
            return f"No se encontro un producto llamado '{product_name}'."

        # Obtener informacion nutricional del producto actual
        nutrition_service = NutritionService()
        current_info = nutrition_service.get_nutrition_by_product_id(product.id)

        # Verificar si el producto ya es saludable
        if current_info and current_info['is_healthy']:
            return f"{product.name} ya es una opcion saludable!\n\nNo necesita alternativas."

        # Obtener alternativas
        alternatives = nutrition_service.get_healthy_alternatives(product.id)

        if not alternatives:
            return f"No se encontraron alternativas saludables para {product.name}."

        # Construir respuesta
        response = f"ALTERNATIVAS SALUDABLES A: {product.name}\n\n"

        if current_info:
            flags = current_info.get('flags', [])
            if flags:
                response += f"Producto actual es ALTO EN: {', '.join(flags)}\n\n"

        response += "Opciones recomendadas:\n"
        for i, alt in enumerate(alternatives, 1):
            response += f"\n{i}. {alt['name']} (${alt['price']})"
            response += f"\n   Categoria: {alt['category']}"

        response += "\n\nConsejo: Estos productos no tienen flags nutricionales"
        response += " de azucar, sodio o grasa en niveles altos."

        return response

    except Exception as e:
        return f"Error al buscar alternativas: {str(e)}"