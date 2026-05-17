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


class NutritionFact(models.Model):
    """
    Modelo para hechos nutricionales de productos.
    Indica si un producto es alto en azucar, sodio o grasa.
    """
    product_name = models.CharField(max_length=255, unique=True, db_index=True)
    high_sugar = models.BooleanField(default=False, help_text="Alto en azucar")
    high_sodium = models.BooleanField(default=False, help_text="Alto en sodio")
    high_fat = models.BooleanField(default=False, help_text="Alto en grasa")

    class Meta:
        db_table = 'nutritionfacts'
        verbose_name = 'Hecho Nutricional'
        verbose_name_plural = 'Hechos Nutricionales'
        indexes = [
            models.Index(fields=['product_name']),
        ]

    def __str__(self):
        flags = []
        if self.high_sugar:
            flags.append('azucar')
        if self.high_sodium:
            flags.append('sodio')
        if self.high_fat:
            flags.append('grasa')
        
        if flags:
            return f"{self.product_name} (alto en {', '.join(flags)})"
        return self.product_name

    def is_healthy(self) -> bool:
        """Retorna True si el producto no es alto en ningun nutriente critico."""
        return not (self.high_sugar or self.high_sodium or self.high_fat)

    def get_flags(self) -> list:
        """Retorna lista de flags nutricionales activas."""
        flags = []
        if self.high_sugar:
            flags.append('high_sugar')
        if self.high_sodium:
            flags.append('high_sodium')
        if self.high_fat:
            flags.append('high_fat')
        return flags
