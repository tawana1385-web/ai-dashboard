# AI_Dashboard/generate_test_data.py
import sqlite3
from datetime import datetime, timedelta
import random

def generate_monthly_sales():
    """تولید 36 ماه داده شبیه‌سازی شده برای تست"""
    data = []
    base_date = datetime(2022, 1, 1)
    
    for i in range(36):
        date = base_date + timedelta(days=30*i)
        # الگوی فصلی + روند صعودی + نویز تصادفی
        seasonal = 1000 * (1 + 0.5 * (i % 12) / 12)  # الگوی فصلی
        trend = 500 * (i / 12)  # روند صعودی تدریجی
        noise = random.randint(-200, 200)  # نویز تصادفی
        revenue = 5000 + seasonal + trend + noise
        
        data.append({
            'month': date.strftime('%Y-%m-%d'),
            'revenue': max(3000, revenue),  # حداقل 3000
            'transaction_count': random.randint(50, 200)
        })
    
    return data