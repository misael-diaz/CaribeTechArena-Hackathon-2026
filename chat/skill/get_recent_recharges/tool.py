from langchain.tools import tool
from parent.models import Parent
from transaction.models import Recarga

@tool
def get_recent_recharges(parent_phone: str, student_name: str) -> str:
    """
    Obtiene las últimas 3 recargas realizadas a la cuenta de un estudiante vinculado al número de teléfono del padre.
    """
    try:
        parent = Parent.objects.get(phone_e164=parent_phone)
        student = parent.students.filter(name__icontains=student_name).first()
        if not student:
            return f"No se encontró un estudiante llamado {student_name} vinculado a este número."
        
        recharges = Recarga.objects.filter(student=student).order_by('-fecha')[:3]
        if not recharges.exists():
            return f"No hay registros de recargas recientes para {student.name}."
        
        recharge_info = [f"${r.valor} el {r.fecha}" for r in recharges]
        return f"Últimas recargas de {student.name}: {', '.join(recharge_info)}."
    except Parent.DoesNotExist:
        return "No se encontró un padre registrado con este número de teléfono."
    except Exception as e:
        return f"Error al consultar recargas: {str(e)}"
