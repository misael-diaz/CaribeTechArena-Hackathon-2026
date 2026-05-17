from django.contrib import admin
from .models import CafeteriaAdmin, Inventory

@admin.register(CafeteriaAdmin)
class CafeteriaAdminAdmin(admin.ModelAdmin):
    list_display = ('phone_e164', 'school')
    search_fields = ('phone_e164', 'school__name')

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'school', 'current_stock', 'minimum_stock')
    list_filter = ('school',)
    search_fields = ('product__name', 'school__name')
