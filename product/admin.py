from django.contrib import admin
from .models import Product, ProductAllergen

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(ProductAllergen)
class ProductAllergenAdmin(admin.ModelAdmin):
    list_display = ('product', 'allergen_name')
    list_filter = ('allergen_name',)
