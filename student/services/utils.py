"""
Utils compartidos para servicios de estudiantes.
Contiene logica reutilizable para consulta de estudiantes por telefono de padre.
"""

from typing import Optional, Tuple, List
from django.db.models import QuerySet
from student.models import Student
from parent.models import Parent


def get_student_by_parent_phone(
    parent_phone: str,
    student_name: Optional[str] = None
) -> Optional[Student]:
    """
    Obtiene un estudiante por telefono del padre.
    
    Args:
        parent_phone: Telefono del padre en formato E.164
        student_name: Nombre (o parte) del estudiante (opcional)
    
    Returns:
        Student o None si no se encuentra
    
    Raises:
        Parent.DoesNotExist: Si el padre no existe
    """
    try:
        parent = Parent.objects.filter(phone_e164=parent_phone).first()
        if not parent:
            return None
        
        if student_name:
            student = parent.students.filter(name__icontains=student_name).first()
        else:
            # Si el padre tiene un solo hijo, retornar ese
            students = parent.students.all()
            if students.count() == 1:
                student = students.first()
            else:
                student = None
        
        return student
    except Exception:
        return None


def get_all_students_by_parent_phone(
    parent_phone: str
) -> List[Student]:
    """
    Obtiene todos los estudiantes de un padre.
    
    Args:
        parent_phone: Telefono del padre en formato E.164
    
    Returns:
        Lista de Students
    """
    try:
        parent = Parent.objects.filter(phone_e164=parent_phone).first()
        if not parent:
            return []
        return list(parent.students.all())
    except Exception:
        return []


def get_parent_by_phone(parent_phone: str) -> Optional[Parent]:
    """
    Obtiene el padre por telefono.
    
    Args:
        parent_phone: Telefono del padre en formato E.164
    
    Returns:
        Parent o None
    """
    return Parent.objects.filter(phone_e164=parent_phone).first()


def format_student_name(student: Student) -> str:
    """
    Formatea el nombre del estudiante para mostrar.
    
    Args:
        student: Estudiante a formatear
    
    Returns:
        String formateado
    """
    return f"{student.name} ({student.grade})"


def get_student_ids(students: QuerySet) -> List[int]:
    """
    Obtiene lista de IDs de estudiantes.
    
    Args:
        students: QuerySet de estudiantes
    
    Returns:
        Lista de IDs
    """
    return list(students.values_list('id', flat=True))
