"""
Servicio para logica nutricional de productos.
Contiene logica reutilizable para consulta de informacion nutricional,
comparacion de productos y recomendaciones saludables.
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import QuerySet
from product.models import Product, NutritionFact, ProductAllergen


class NutritionService:
    """
    Servicio para gestion de informacion nutricional de productos.
    """

    HEALTHY_THRESHOLD = 0  # Un producto es saludable si no tiene ningun flag activo

    def __init__(self):
        pass

    def get_nutrition_info(self, product_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene informacion nutricional de un producto por nombre.
        
        Args:
            product_name: Nombre del producto (o parte)
        
        Returns:
            Dict con informacion nutricional o None si no existe
        """
        nutrition = NutritionFact.objects.filter(
            product_name__icontains=product_name
        ).first()
        
        if not nutrition:
            return None
        
        return {
            'product_name': nutrition.product_name,
            'high_sugar': nutrition.high_sugar,
            'high_sodium': nutrition.high_sodium,
            'high_fat': nutrition.high_fat,
            'is_healthy': nutrition.is_healthy(),
            'flags': nutrition.get_flags()
        }

    def get_nutrition_by_product_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene informacion nutricional por ID de producto.
        
        Args:
            product_id: ID del producto
        
        Returns:
            Dict con informacion nutricional o None
        """
        try:
            product = Product.objects.get(id=product_id)
            nutrition = NutritionFact.objects.filter(
                product_name=product.name
            ).first()
            
            if not nutrition:
                return None
            
            return {
                'product_name': nutrition.product_name,
                'high_sugar': nutrition.high_sugar,
                'high_sodium': nutrition.high_sodium,
                'high_fat': nutrition.high_fat,
                'is_healthy': nutrition.is_healthy(),
                'flags': nutrition.get_flags()
            }
        except Product.DoesNotExist:
            return None

    def is_product_safe_for_student(
        self,
        product_id: int,
        student_id: int
    ) -> Dict[str, Any]:
        """
        Verifica si un producto es seguro para un estudiante (sin alergenicos).
        
        Args:
            product_id: ID del producto
            student_id: ID del estudiante
        
        Returns:
            Dict con:
                - is_safe: Boolean
                - reason: String explicando por que
                - matching_allergens: Lista de alergenicos encontrados
                - nutrition_info: Informacion nutricional si existe
        """
        result = {
            'is_safe': True,
            'reason': 'El producto es seguro para el estudiante',
            'matching_allergens': [],
            'nutrition_info': None
        }
        
        # Obtener producto
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            result['is_safe'] = False
            result['reason'] = 'Producto no encontrado'
            return result
        
        # Obtener alergenicos del estudiante
        from student.models import Student, StudentAllergen
        
        try:
            student = Student.objects.get(id=student_id)
            student_allergens = set(
                StudentAllergen.objects
                .filter(student=student)
                .values_list('allergen_name', flat=True)
            )
        except Student.DoesNotExist:
            result['is_safe'] = False
            result['reason'] = 'Estudiante no encontrado'
            return result
        
        # Si no tiene alergenicos registrados, es seguro
        if not student_allergens:
            result['reason'] = 'El estudiante no tiene alergenicos registrados'
            result['nutrition_info'] = self.get_nutrition_by_product_id(product_id)
            return result
        
        # Obtener alergenicos del producto
        product_allergens = set(
            ProductAllergen.objects
            .filter(product=product)
            .values_list('allergen_name', flat=True)
        )
        
        # Verificar interseccion
        matching = student_allergens & product_allergens
        
        if matching:
            result['is_safe'] = False
            result['matching_allergens'] = list(matching)
            result['reason'] = f"El producto contiene: {', '.join(matching)}"
        
        # Agregar informacion nutricional
        result['nutrition_info'] = self.get_nutrition_by_product_id(product_id)
        
        return result

    def get_healthy_alternatives(
        self,
        product_id: int,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene alternativas saludables a un producto.
        
        Args:
            product_id: ID del producto actual
            category: Categoria para filtrar (opcional)
        
        Returns:
            Lista de productos saludables alternativos
        """
        try:
            current_product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return []
        
        # Si no se especifica categoria, usar la del producto actual
        if not category:
            category = current_product.category
        
        # Buscar productos saludables de la misma categoria
        healthy_products = Product.objects.filter(
            category=category
        ).exclude(id=product_id)
        
        alternatives = []
        for p in healthy_products:
            nutrition = NutritionFact.objects.filter(product_name=p.name).first()
            
            # Si no hay info nutricional, asumir que es saludable
            if not nutrition or nutrition.is_healthy():
                alternatives.append({
                    'id': p.id,
                    'name': p.name,
                    'category': p.category,
                    'price': str(p.price),
                    'is_healthy': True
                })
        
        # Si no hay alternativas en la misma categoria, buscar en todas
        if len(alternatives) == 0:
            all_products = Product.objects.exclude(id=product_id)
            for p in all_products[:10]:  # Limitar a 10
                nutrition = NutritionFact.objects.filter(product_name=p.name).first()
                if not nutrition or nutrition.is_healthy():
                    alternatives.append({
                        'id': p.id,
                        'name': p.name,
                        'category': p.category,
                        'price': str(p.price),
                        'is_healthy': True
                    })
        
        return alternatives[:5]  # Retornar maximo 5

    def compare_products(
        self,
        product_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Compara multiples productos nutricionalmente.
        
        Args:
            product_ids: Lista de IDs de productos a comparar
        
        Returns:
            Dict con comparacion de productos
        """
        products = []
        comparison = {
            'products': [],
            'healthiest': None,
            'summary': ''
        }
        
        healthy_count = 0
        
        for pid in product_ids:
            try:
                product = Product.objects.get(id=pid)
                nutrition = NutritionFact.objects.filter(
                    product_name=product.name
                ).first()
                
                flags = []
                if nutrition:
                    if nutrition.high_sugar:
                        flags.append('azucar')
                    if nutrition.high_sodium:
                        flags.append('sodio')
                    if nutrition.high_fat:
                        flags.append('grasa')
                    is_healthy = nutrition.is_healthy()
                    if is_healthy:
                        healthy_count += 1
                else:
                    is_healthy = True
                    healthy_count += 1
                
                product_info = {
                    'id': product.id,
                    'name': product.name,
                    'category': product.category,
                    'price': str(product.price),
                    'flags': flags,
                    'is_healthy': is_healthy
                }
                products.append(product_info)
                
            except Product.DoesNotExist:
                continue
        
        comparison['products'] = products
        
        # Determinar cual es el mas saludable
        if healthy_count == len(products):
            comparison['healthiest'] = 'Todos son saludables'
            comparison['summary'] = 'Todos los productos comparados son opciones saludables.'
        elif healthy_count == 0:
            comparison['healthiest'] = 'Ninguno es saludable'
            comparison['summary'] = 'Ninguno de los productos comparados es una opcion saludable.'
        else:
            healthy_products = [p for p in products if p['is_healthy']]
            if healthy_products:
                comparison['healthiest'] = ', '.join([p['name'] for p in healthy_products])
                comparison['summary'] = f"{healthy_count} de {len(products)} productos son opciones saludables."
        
        return comparison

    def get_all_healthy_products(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos saludables registrados.
        
        Returns:
            Lista de productos saludables
        """
        healthy_products = []
        
        for product in Product.objects.all():
            nutrition = NutritionFact.objects.filter(
                product_name=product.name
            ).first()
            
            if not nutrition or nutrition.is_healthy():
                healthy_products.append({
                    'id': product.id,
                    'name': product.name,
                    'category': product.category,
                    'price': str(product.price)
                })
        
        return healthy_products
