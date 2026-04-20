# expenses/models.py - اضافه کردن فیلد is_active

from django.db import models
from django.utils import timezone

class ExpenseCategory(models.Model):
    """
    دسته‌بندی هزینه‌ها
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="نام دسته")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    parent_category = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دسته والد")
    is_active = models.BooleanField(default=True, verbose_name="فعال")  # ← این خط را اضافه کنید
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "دسته هزینه"
        verbose_name_plural = "دسته‌های هزینه"
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    """
    مدل ثبت هزینه‌ها
    """
    EXPENSE_STATUS = [
        ('pending', 'در انتظار'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="عنوان هزینه")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, verbose_name="دسته هزینه")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="مبلغ")
    date = models.DateField(default=timezone.now, verbose_name="تاریخ هزینه")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True, verbose_name="تصویر رسید")
    status = models.CharField(max_length=20, choices=EXPENSE_STATUS, default='pending', verbose_name="وضعیت")
    created_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="ثبت کننده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "هزینه"
        verbose_name_plural = "هزینه‌ها"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - {self.amount:,.0f} AFN"