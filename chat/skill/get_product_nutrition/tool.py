from langchain.tools import tool


@tool
def get_product_nutrition(product_name: str) -> str:
    """
    Obtiene informacion nutricional de un producto de la cafeteria.
    
    Indica si el producto es alto en azucar, sodio o grasa.
    Util para padres que quieren saber que tan saludables son los
    productos que compran sus hijos.
    
    Args:
        product_name: Nombre del producto (o parte del nombre)
    
    Returns:
        Mensaje con informacion nutricional del producto
    """
    try:
        from product.models import NutritionFact
        
        # Buscar producto por nombre parcial
        products = NutritionFact.objects.filter(
            product_name__icontains=product_name
        )
        
        if not products.exists():
            return f"No se encontro informacion nutricional para '{product_name}'."
        
        results = []
        for p in products[:5]:  # Limitar a 5 resultados
            flags = []
            if p.high_sugar:
                flags.append('azucar')
            if p.high_sodium:
                flags.append('sodio')
            if p.high_fat:
                flags.append('grasa')
            
            if flags:
                status = f"ALTO EN: {', '.join(flags)}"
            else:
                status = "OPCION SALUDABLE"
            
            results.append(f"- {p.product_name}: {status}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Error al consultar informacion nutricional: {str(e)}"
