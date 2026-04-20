# inventory/models.py

from django.db import models

class Product(models.Model):
    UNIT_CHOICES = [
        ('piece', 'عدد'),
        ('kg', 'کیلوگرم'),
        ('meter', 'متر'),
        ('liter', 'لیتر'),
        ('box', 'جعبه'),
    ]
    
    product_code = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    reorder_level = models.IntegerField(default=10)
    supplier = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
    
    def __str__(self):
        return f"{self.product_code} - {self.name}"
    
    @property
    def total_value(self):
        return self.quantity * self.unit_price


class InventoryMovement(models.Model):
    MOVEMENT_TYPES = [
        ('in', 'ورود به انبار'),
        ('out', 'خروج از انبار'),
        ('return', 'برگشت'),
        ('damage', 'آسیب دیده'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "حرکت انبار"
        verbose_name_plural = "حرکات انبار"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.movement_type == 'in':
            self.product.quantity += self.quantity
        elif self.movement_type in ['out', 'damage']:
            self.product.quantity -= self.quantity
        elif self.movement_type == 'return':
            self.product.quantity += self.quantity
        
        self.product.save()