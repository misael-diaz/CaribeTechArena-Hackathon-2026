from langchain.tools import tool
from parent.models import Parent

@tool
def get_student_balance(parent_phone: str, student_name: str) -> str:
    """
    Obtiene el saldo actual en la billetera digital de un estudiante vinculado al número de teléfono del padre.
    """
    try:
        parent = Parent.objects.get(phone_e164=parent_phone)
        student = parent.students.filter(name__icontains=student_name).first()
        if not student:
            return f"No se encontró un estudiante llamado {student_name} vinculado a este número."
        
        return f"El saldo actual de {student.name} es de ${student.balance}."
    except Parent.DoesNotExist:
        return "No se encontró un padre registrado con este número de teléfono."
    except Exception as e:
        return f"Error al consultar el saldo: {str(e)}"
