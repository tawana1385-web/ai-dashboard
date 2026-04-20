# dashboard/models.py - کد کامل

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class DashboardSettings(models.Model):
    """
    تنظیمات عمومی داشبورد
    """
    site_name = models.CharField(max_length=200, default="داشبورد هوشمند تجارتی", verbose_name="نام سایت")
    site_tagline = models.CharField(max_length=500, blank=True, null=True, verbose_name="شعار سایت")
    primary_color = models.CharField(max_length=20, default="#3B82F6", verbose_name="رنگ اصلی")
    secondary_color = models.CharField(max_length=20, default="#10B981", verbose_name="رنگ ثانویه")
    refresh_interval = models.IntegerField(default=300, verbose_name="زمان بروزرسانی (ثانیه)")
    enable_notifications = models.BooleanField(default=True, verbose_name="فعال بودن اعلان‌ها")
    items_per_page = models.IntegerField(default=25, verbose_name="تعداد آیتم در هر صفحه")
    currency_symbol = models.CharField(max_length=10, default="AFN", verbose_name="نماد ارز")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "تنظیمات داشبورد"
        verbose_name_plural = "تنظیمات داشبورد"
    
    def __str__(self):
        return self.site_name
    
    @classmethod
    def get_settings(cls):
        """دریافت تنظیمات (Singleton)"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class UserPreference(models.Model):
    """
    تنظیمات شخصی هر کاربر
    """
    THEME_CHOICES = [
        ('light', 'روشن'),
        ('dark', 'تاریک'),
        ('auto', 'خودکار'),
    ]
    
    DASHBOARD_CHOICES = [
        ('kpi', 'داشبورد KPI'),
        ('forecast', 'پیش‌بینی مالی'),
        ('sales', 'گزارش فروش'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences', verbose_name="کاربر")
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='light', verbose_name="تم")
    default_dashboard = models.CharField(max_length=20, choices=DASHBOARD_CHOICES, default='kpi', verbose_name="داشبورد پیش‌فرض")
    email_notifications = models.BooleanField(default=False, verbose_name="اعلان ایمیلی")
    language = models.CharField(max_length=10, default='fa', verbose_name="زبان")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "تنظیمات کاربر"
        verbose_name_plural = "تنظیمات کاربران"
    
    def __str__(self):
        return f"تنظیمات {self.user.username}"