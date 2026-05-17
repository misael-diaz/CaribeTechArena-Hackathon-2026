from langchain.tools import tool
from parent.models import Parent

@tool
def get_student_allergens(parent_phone: str, student_name: str) -> str:
    """
    Obtiene la lista de alergias registradas para un estudiante vinculado al número de teléfono del padre.
    """
    try:
        parent = Parent.objects.get(phone_e164=parent_phone)
        student = parent.students.filter(name__icontains=student_name).first()
        if not student:
            return f"No se encontró un estudiante llamado {student_name} vinculado a este número."
        
        allergens = student.allergens.all()
        if not allergens.exists():
            return f"{student.name} no tiene ninguna alergia registrada."
        
        allergen_names = [a.allergen_name for a in allergens]
        return f"Alergias registradas para {student.name}: {', '.join(allergen_names)}."
    except Parent.DoesNotExist:
        return "No se encontró un padre registrado con este número de teléfono."
    except Exception as e:
        return f"Error al consultar alergias: {str(e)}"
