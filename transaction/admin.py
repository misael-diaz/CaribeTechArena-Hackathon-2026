from django.contrib import admin
from .models import Transaction, Recarga

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'product', 'quantity', 'price', 'created_at')
    list_filter = ('created_at', 'product')
    date_hierarchy = 'created_at'

@admin.register(Recarga)
class RecargaAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'fecha', 'valor')
    list_filter = ('fecha',)
