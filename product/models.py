from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class ProductAllergen(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='allergens')
    allergen_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.product.name} - {self.allergen_name}"
