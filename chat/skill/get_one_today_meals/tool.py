from langchain.tools import tool
from django.utils import timezone
from transaction.models import Transaction
from parent.models import Parent

@tool
def get_one_today_meals(parent_phone: str, student_name: str) -> str:
    """
    Consulta lo que comió hoy un estudiante específico vinculado al número de teléfono del padre.
    Útil para responder preguntas como "¿Qué comió Juan hoy?"
    """
    today = timezone.now().date()
    try:
        parent = Parent.objects.get(phone_e164=parent_phone)
        student = parent.students.filter(name__icontains=student_name).first()
        if not student:
            return f"No se encontró un estudiante llamado {student_name} vinculado a este número."
        
        transactions = Transaction.objects.filter(student=student, created_at__date=today)
        if not transactions.exists():
            return f"{student.name} no ha registrado compras hoy."
        
        meals = []
        for t in transactions:
            meals.append(f"{t.quantity}x {t.product.name}")
        
        meals_str = ", ".join(meals)
        return f"{student.name} comió hoy: {meals_str}."
    except Parent.DoesNotExist:
        return "No se encontró un padre registrado con este número de teléfono."
    except Exception as e:
        return f"Error al consultar transacciones: {str(e)}"
