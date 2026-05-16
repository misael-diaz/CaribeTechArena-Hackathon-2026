from django.db import models

class CafeteriaAdmin(models.Model):
    phone_e164 = models.CharField(max_length=20)
    school = models.ForeignKey('school.School', on_delete=models.CASCADE, related_name='admins')

    def __str__(self):
        return f"{self.phone_e164} ({self.school.name})"

class Inventory(models.Model):
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    school = models.ForeignKey('school.School', on_delete=models.CASCADE)
    current_stock = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Inventories"
        unique_together = ('product', 'school')

    def __str__(self):
        return f"{self.product.name} @ {self.school.name} ({self.current_stock})"
