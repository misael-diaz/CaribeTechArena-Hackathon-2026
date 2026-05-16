from student.models import Student
from parent.models import Parent
from django.db.models import QuerySet


def get_childs(id : int) -> QuerySet[Student]: 

    parent = Parent.get_parent_students_by_phone_parent(id)

    return parent