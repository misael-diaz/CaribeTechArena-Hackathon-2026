from typing import Dict, Any, List, Optional
from datetime import timedelta
from django.utils import timezone
from student.models import StudentAllergen
from product.models import ProductAllergen
import logging

from student.services import (
    get_student_by_parent_phone,
    get_all_students_by_parent_phone,
    BalanceForecastService
)
from product.services import NutritionService


logger = logging.getLogger(__name__)


class StudentSummaryService:
    """
    Servicio para generar resumenes completos de estudiantes.
    Combina: saldo, forecast, compras recientes, alergenicos, nutricion.
    """

    def __init__(self):
        self.forecast_service = BalanceForecastService()
        self.nutrition_service = NutritionService()

    def get_full_summary(
        self,
        parent_phone: str,
        student_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene resumen completo de un estudiante.

        Args:
            parent_phone: Telefono del padre
            student_name: Nombre del estudiante (opcional)

        Returns:
            Dict con resumen completo
        """
        student = get_student_by_parent_phone(parent_phone, student_name)

        if not student:
            return {
                'error': 'Estudiante no encontrado',
                'parent_phone': parent_phone
            }

        # Obtener forecast de saldo
        forecast = self.forecast_service.calculate_forecast(student)

        # Obtener compras recientes
        from transaction.models import Transaction
        recent_transactions = Transaction.objects.filter(
            student=student
        ).select_related('product').order_by('-created_at')[:5]

        purchases = []
        for t in recent_transactions:
            purchases.append({
                'product_name': t.product.name,
                'price': str(t.price),
                'date': t.created_at.strftime('%d/%m/%Y %H:%M')
            })

        # Obtener alergenicos
        from student.models import StudentAllergen
        allergens = list(
            StudentAllergen.objects
            .filter(student=student)
            .values_list('allergen_name', flat=True)
        )

        # Obtener recargas recientes
        from transaction.models import Recarga
        recent_recharges = Recarga.objects.filter(
            student=student
        ).order_by('-fecha')[:3]

        recharges = []
        for r in recent_recharges:
            recharges.append({
                'amount': str(r.valor),
                'date': r.fecha.strftime('%d/%m/%Y')
            })

        return {
            'student': {
                'id': student.id,
                'name': student.name,
                'grade': student.grade,
                'school': student.school.name
            },
            'balance': {
                'current': float(student.balance),
                'forecast': forecast
            },
            'recent_purchases': purchases,
            'recent_recharges': recharges,
            'allergens': allergens,
            'has_allergens': len(allergens) > 0
        }

    def format_summary_text(self, summary: Dict[str, Any]) -> str:
        """
        Formatea el resumen como texto legible.

        Args:
            summary: Dict con resumen completo

        Returns:
            String formateado
        """
        if 'error' in summary:
            return f"Error: {summary['error']}"

        lines = []
        student = summary['student']
        balance = summary['balance']

        # Encabezado
        lines.append(f"=== RESUMEN DE {student['name'].upper()} ===")
        lines.append(f"Grado: {student['grade']}")
        lines.append(f"Colegio: {student['school']}")
        lines.append("")

        # Saldo
        lines.append(f"SALDO ACTUAL: ${balance['current']:.2f}")

        forecast = balance['forecast']
        if forecast['has_spending_history']:
            lines.append(f"Gasto promedio diario: ${forecast['daily_average']:.2f}")
            if forecast['days_until_empty']:
                lines.append(f"Se agotara en: {forecast['days_until_empty']:.0f} dias")
            lines.append(f"Tendencia: {forecast['trend']}")
        lines.append("")

        # Alergenicos
        if summary['has_allergens']:
            lines.append(f"ALERGENICOS REGISTRADOS: {', '.join(summary['allergens'])}")
        else:
            lines.append("No tiene alergenicos registrados")
        lines.append("")

        # Compras recientes
        lines.append("ULTIMAS COMPRAS:")
        if summary['recent_purchases']:
            for p in summary['recent_purchases']:
                lines.append(f"  - {p['product_name']} (${p['price']}) - {p['date']}")
        else:
            lines.append("  Sin compras recientes")
        lines.append("")

        # Recargas recientes
        lines.append("RECARGAS RECIENTES:")
        if summary['recent_recharges']:
            for r in summary['recent_recharges']:
                lines.append(f"  + ${r['amount']} - {r['date']}")
        else:
            lines.append("  Sin recargas recientes")

        # Recomendaciones Personalizadas
        lines.append("")
        lines.append("RECOMENDACIONES PERSONALIZADAS")
        lines.append("" + "—" * 40)

        # 1. Recarga urgente si saldo bajo
        forecast = balance['forecast']
        if forecast.get('days_until_empty') and forecast['days_until_empty'] < 5:
            recommended_reload = forecast.get('recommended_reload', 0)
            days = int(forecast['days_until_empty'])
            lines.append(f"RECARGA URGENTE: Tu saldo actual (${balance['current']:.2f}) cubre solo {days} días.")
            lines.append(f"   Te recomendamos recargar ${recommended_reload:.2f} para llegar hasta el viernes.")

        # 2. Patrón de consumo (gaseosas, azúcar)
        high_sugar_products = ['coca', 'gaseosa', 'jugo hit', 'detodito', 'papas']
        sugar_count = 0
        recent_names = [p['product_name'].lower() for p in summary['recent_purchases']]
        for name in recent_names:
            if any(s in name for s in high_sugar_products):
                sugar_count += 1

        if sugar_count >= 3:
            lines.append(f"PATRÓN DE CONSUMO: Juan ha comprado productos altos en azúcar {sugar_count} veces esta semana.")
            lines.append("   ¿Quieres que te sugiera alternativas saludables? Responde 'SÍ' o 'NO'.")

        # 3. Alerta alérgeno si compró producto peligroso
        if summary['has_allergens'] and summary['recent_purchases']:
            # Obtener alérgenos del estudiante
            student_allergens = set(
                StudentAllergen.objects.filter(student=student)
                .values_list('allergen_name', flat=True)
            )

            for p in summary['recent_purchases'][:3]:
                try:
                    # Obtener el producto de la transacción
                    from product.models import Product, ProductAllergen
                    product_obj = Product.objects.filter(name__iexact=p['product_name']).first()
                    if not product_obj:
                        continue

                    # Verificar si este producto tiene algún alérgeno que el estudiante tenga registrado
                    product_allergens = set(
                        ProductAllergen.objects.filter(product=product_obj)
                        .values_list('allergen_name', flat=True)
                    )

                    matching_allergens = student_allergens & product_allergens
                    if matching_allergens:
                        lines.append(f"ALERTA ALÉRGENO: Ayer compró '{p['product_name']}', que contiene {', '.join(matching_allergens)}.")
                        lines.append("   Verifica su estado. ¿Quieres que te envíe alternativas seguras?")
                        break
                except Exception as e:
                    logger.error(f"Error verificando alérgenos para {p['product_name']}: {e}")
                    continue

        return "\n".join(lines)

    def get_multi_student_summary(
        self,
        parent_phone: str
    ) -> Dict[str, Any]:
        """
        Obtiene resumen de todos los estudiantes de un padre.

        Args:
            parent_phone: Telefono del padre

        Returns:
            Dict con resmenes de todos los estudiantes
        """
        students = get_all_students_by_parent_phone(parent_phone)

        if not students:
            return {
                'error': 'No se encontraron estudiantes',
                'parent_phone': parent_phone
            }

        summaries = []
        for student in students:
            summary = self.get_full_summary(parent_phone, student.name)
            summaries.append(summary)

        return {
            'parent_phone': parent_phone,
            'student_count': len(students),
            'students': summaries
        }

    def format_multi_student_text(
        self,
        multi_summary: Dict[str, Any]
    ) -> str:
        """
        Formatea resumen multiple como texto legible.

        Args:
            multi_summary: Dict con resumen multiple

        Returns:
            String formateado
        """
        if 'error' in multi_summary:
            return f"Error: {multi_summary['error']}"

        lines = []
        lines.append(f"=== HIJOS REGISTRADOS ({multi_summary['student_count']}) ===")
        lines.append("")

        for i, student_summary in enumerate(multi_summary['students'], 1):
            if i > 1:
                lines.append("---")
                lines.append("")

            student_summary['student_name'] = f"Hijo {i}"
            lines.append(self.format_summary_text(student_summary))

        return "\n".join(lines)