from django.contrib import admin
from .models import Student, StudentAllergen

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'grade', 'school', 'balance')
    list_filter = ('school', 'grade')
    search_fields = ('name',)

@admin.register(StudentAllergen)
class StudentAllergenAdmin(admin.ModelAdmin):
    list_display = ('student', 'allergen_name')
    list_filter = ('allergen_name',)
