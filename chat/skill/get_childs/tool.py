from langchain.tools import tool
from parent.models import Parent

@tool
def get_childs(phone_e164: str) -> str:
    """
    Obtiene la lista de los nombres de los hijos vinculados al número de teléfono del padre.
    
    Args:
        phone_e164 (str): El número de teléfono del padre (ej. +573001234567).
    """
    try:
        parent = Parent.objects.get(phone_e164=phone_e164)
        students = parent.students.all()
        if not students.exists():
            return "No tienes hijos registrados."
        
        names = [student.name for student in students]
        return f"Tus hijos registrados son: {', '.join(names)}"
    except Parent.DoesNotExist:
        return "No se encontró un padre registrado con este número de teléfono."
    except Exception as e:
        return f"Error al consultar estudiantes: {str(e)}"
