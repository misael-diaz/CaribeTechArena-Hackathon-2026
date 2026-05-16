from django.contrib import admin
from .models import ParentPhoneMap

@admin.register(ParentPhoneMap)
class ParentPhoneMapAdmin(admin.ModelAdmin):
    list_display = ('phone_e164', 'student')
    search_fields = ('phone_e164', 'student__name')
