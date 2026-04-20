# sales/models.py - نسخه کامل با همه مدل‌ها

from django.db import models
from django.utils import timezone
from datetime import datetime

class MonthlySales(models.Model):
    """
    مدل ذخیره‌سازی فروش ماهانه
    """
    month = models.DateField(unique=True, verbose_name="ماه")
    revenue = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="درآمد کل")
    transaction_count = models.IntegerField(default=0, verbose_name="تعداد تراکنش‌ها")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    class Meta:
        verbose_name = "فروش ماهانه"
        verbose_name_plural = "فروش‌های ماهانه"
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.month.strftime('%B %Y')} - {self.revenue:,.0f} AFN"
    
    @property
    def month_name(self):
        return self.month.strftime('%B %Y')


class SalesTransaction(models.Model):
    """
    مدل ذخیره‌سازی تراکنش‌های فروش روزانه
    """
    PAYMENT_METHODS = [
        ('cash', 'نقدی'),
        ('card', 'کارت بانکی'),
        ('transfer', 'انتقال بانکی'),
        ('online', 'پرداخت آنلاین'),
    ]
    
    TRANSACTION_STATUS = [
        ('pending', 'در انتظار'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
        ('refunded', 'بازگشت وجه'),
    ]
    
    transaction_id = models.CharField(max_length=50, unique=True, verbose_name="شماره تراکنش")
    transaction_date = models.DateTimeField(default=timezone.now, verbose_name="تاریخ تراکنش")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="مبلغ")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash', verbose_name="روش پرداخت")
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='completed', verbose_name="وضعیت")
    customer_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="نام مشتری")
    customer_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="شماره تماس")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "تراکنش فروش"
        verbose_name_plural = "تراکنش‌های فروش"
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount:,.0f} AFN"


class SalesInvoice(models.Model):
    """
    مدل فاکتورهای فروش
    """
    INVOICE_STATUS = [
        ('draft', 'پیش‌نویس'),
        ('sent', 'ارسال شده'),
        ('paid', 'پرداخت شده'),
        ('overdue', 'تأخیر'),
        ('cancelled', 'لغو شده'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="شماره فاکتور")
    transaction = models.OneToOneField(
        SalesTransaction, 
        on_delete=models.CASCADE, 
        related_name='invoice', 
        verbose_name="تراکنش",
        null=True,
        blank=True
    )
    issue_date = models.DateField(default=timezone.now, verbose_name="تاریخ صدور")
    due_date = models.DateField(verbose_name="تاریخ سررسید")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="مالیات")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="تخفیف")
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="جمع کل")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="مبلغ نهایی")
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft', verbose_name="وضعیت")
    notes = models.TextField(blank=True, null=True, verbose_name="یادداشت")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "فاکتور فروش"
        verbose_name_plural = "فاکتورهای فروش"
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"فاکتور {self.invoice_number} - {self.total_amount:,.0f} AFN"
    
    @property
    def is_overdue(self):
        """آیا فاکتور تأخیر دارد؟"""
        from django.utils import timezone
        return self.due_date < timezone.now().date() and self.status != 'paid'
    
    @property
    def is_paid(self):
        return self.status == 'paid'


class InvoiceItem(models.Model):
    """
    آیتم‌های فاکتور (محصولات و خدمات)
    """
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, related_name='items', verbose_name="فاکتور")
    description = models.CharField(max_length=500, verbose_name="توضیحات")
    quantity = models.IntegerField(default=1, verbose_name="تعداد")
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="قیمت واحد")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="تخفیف")
    total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="جمع")
    
    class Meta:
        verbose_name = "آیتم فاکتور"
        verbose_name_plural = "آیتم‌های فاکتور"
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        self.total = (self.quantity * self.unit_price) - self.discount
        super().save(*args, **kwargs)