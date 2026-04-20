# dashboard/charts.py
import matplotlib.pyplot as plt
import io
import base64
from django.http import HttpResponse

def create_forecast_chart(actual, predicted, model_name):
    """ایجاد نمودار مقایسه مقادیر واقعی و پیش‌بینی شده"""
    plt.figure(figsize=(12, 6))
    plt.plot(actual, label='مقادیر واقعی', marker='o', color='blue')
    plt.plot(predicted, label='پیش‌بینی', marker='x', color='red', linestyle='--')
    plt.xlabel('ماه')
    plt.ylabel('درآمد')
    plt.title(f'پیش‌بینی درآمد با مدل {model_name}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # تبدیل به base64 برای نمایش در HTML
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return image_base64

def create_feature_importance_chart(feature_names, importance_values):
    """نمودار اهمیت ویژگی‌ها"""
    plt.figure(figsize=(10, 5))
    plt.barh(feature_names, importance_values, color='teal')
    plt.xlabel('اهمیت')
    plt.title('اهمیت ویژگی‌ها در پیش‌بینی')
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()