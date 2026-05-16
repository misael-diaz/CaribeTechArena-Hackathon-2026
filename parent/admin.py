from django.contrib import admin
from .models import Parent

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('phone_e164', 'name', 'get_children_count')
    search_fields = ('phone_e164', 'name')
    filter_horizontal = ('students',) # Better UI for M2M

    def get_children_count(self, obj):
        return obj.students.count()
    get_children_count.short_description = 'Hijos'
