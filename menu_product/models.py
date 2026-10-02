from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'categories'
        verbose_name = 'category'

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=150)
    price = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category =  models.ForeignKey(  
        Category,
        on_delete = models.PROTECT,
        related_name='products'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    # format mata uang rupiah
    @property
    def formatted_price(self):
        return f"Rp{self.price:,}".replace(",", ".")

    # status ketersediaan
    @property
    def status_label(self):
        return "Tersedia" if self.is_available else "Habis"

    @property
    def status_css_class(self):
        return "status-available" if self.is_available else "status-unavailable"