# AI_Dashboard/tests/test_models.py
import django
import os
import sys

# تنظیم مسیر Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Dashboard.settings')
django.setup()

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from AI_Dashboard.ml_predictor import FinancialPredictor

def test_prediction_accuracy():
    """تست دقت پیش‌بینی مدل"""
    print("=" * 50)
    print("شروع تست دقت مدل‌های پیش‌بینی")
    print("=" * 50)
    
    # تولید داده تست
    np.random.seed(42)
    months = pd.date_range('2022-01-01', periods=48, freq='M')
    
    # ایجاد الگوی داده با روند و فصلی
    trend = np.linspace(5000, 15000, 48)
    seasonal = 2000 * np.sin(2 * np.pi * np.arange(48) / 12)
    noise = np.random.normal(0, 500, 48)
    revenue = trend + seasonal + noise
    
    df = pd.DataFrame({
        'month': months,
        'revenue': revenue
    })
    
    # آموزش و ارزیابی
    predictor = FinancialPredictor()
    X, y = predictor.prepare_data(df)
    
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    results = {}
    for name, model in predictor.models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        results[name] = {
            'MAE': mean_absolute_error(y_test, y_pred),
            'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)),
            'R2': r2_score(y_test, y_pred)
        }
    
    # نمایش نتایج
    print("\n📊 نتایج مقایسه مدل‌ها:")
    print("-" * 50)
    print(f"{'مدل':<20} {'MAE':<12} {'RMSE':<12} {'R²':<10}")
    print("-" * 50)
    
    for name, metrics in results.items():
        print(f"{name:<20} {metrics['MAE']:>8.2f}   {metrics['RMSE']:>8.2f}   {metrics['R2']:>6.3f}")
    
    # ارزیابی موفقیت
    best_model = max(results, key=lambda x: results[x]['R2'])
    best_r2 = results[best_model]['R2']
    
    print("\n" + "=" * 50)
    print(f"🏆 بهترین مدل: {best_model}")
    print(f"📈 بهترین R²: {best_r2:.3f}")
    
    if best_r2 > 0.7:
        print("✅ نتیجه: دقت پیش‌بینی در سطح قابل قبول است (R² > 0.7)")
    else:
        print("⚠️ نتیجه: دقت پیش‌بینی نیاز به بهبود دارد")
    
    return results

def test_response_time():
    """تست زمان پاسخ‌دهی سیستم"""
    import time
    
    print("\n" + "=" * 50)
    print("تست زمان پاسخ‌دهی")
    print("=" * 50)
    
    # تولید داده
    df = pd.DataFrame({
        'month': pd.date_range('2022-01-01', periods=36, freq='M'),
        'revenue': np.random.normal(10000, 2000, 36)
    })
    
    predictor = FinancialPredictor()
    X, y = predictor.prepare_data(df)
    
    # اندازه‌گیری زمان
    start_time = time.time()
    predictor.train_all_models(X, y)
    elapsed_time = time.time() - start_time
    
    print(f"⏱️ زمان آموزش همه مدل‌ها: {elapsed_time:.2f} ثانیه")
    
    if elapsed_time < 3:
        print("✅ زمان پاسخ‌دهی عالی است (< 3 ثانیه)")
    elif elapsed_time < 5:
        print("✅ زمان پاسخ‌دهی قابل قبول است (< 5 ثانیه)")
    else:
        print("⚠️ زمان پاسخ‌دهی نیاز به بهینه‌سازی دارد")
    
    return elapsed_time

if __name__ == "__main__":
    test_prediction_accuracy()
    test_response_time()