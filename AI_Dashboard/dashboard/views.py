# dashboard/views.py - اضافه کردن تابع dashboard_home

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

from sales.models import MonthlySales
from expenses.models import Expense, ExpenseCategory
from inventory.models import Product, InventoryMovement
from dashboard.models import DashboardSettings, UserPreference
from AI_Dashboard.ml_predictor import FinancialPredictor

# تنظیمات فارسی برای نمودارها
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def home_redirect(request):
    """
    ریدایرکت به داشبورد یا صفحه ورود
    """
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    else:
        return redirect('login')  # یا صفحه ورود
@login_required(login_url='/accounts/login/')
def dashboard_home(request):
    """
    صفحه اصلی داشبورد - اولین صفحه بعد از ورود
    نمایش خلاصه اطلاعات و وضعیت کلی سیستم
    """
    context = {
        'welcome_message': f'خوش آمدید {request.user.get_full_name() or request.user.username}',
        'date': timezone.now(),
        'page_title': 'داشبورد اصلی',
    }
    
    try:
        # دریافت آمار کلی
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        
        # آمار فروش ماه جاری
        current_sales = MonthlySales.objects.filter(
            month__year=today.year,
            month__month=today.month
        ).aggregate(
            revenue=Sum('revenue'),
            transactions=Sum('transaction_count')
        )
        
        # آمار هزینه‌ها
        current_expenses = Expense.objects.filter(
            date__year=today.year,
            date__month=today.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # تعداد محصولات با موجودی کم
        low_stock_products = Product.objects.filter(
            quantity__lte=models.F('reorder_level')
        ).count()
        
        # تعداد کل محصولات
        total_products = Product.objects.filter(is_active=True).count()
        
        # سود ماه جاری
        current_revenue = current_sales['revenue'] or 0
        current_profit = current_revenue - current_expenses
        
        # دریافت تنظیمات کاربر
        try:
            prefs = UserPreference.objects.get(user=request.user)
            context['theme'] = prefs.theme
            context['default_dashboard'] = prefs.default_dashboard
        except UserPreference.DoesNotExist:
            context['theme'] = 'light'
            context['default_dashboard'] = 'kpi'
        
        # دریافت تنظیمات عمومی
        try:
            settings = DashboardSettings.get_settings()
            context['site_name'] = settings.site_name
        except:
            context['site_name'] = 'داشبورد هوشمند تجارتی'
        
        context.update({
            'current_revenue': round(current_revenue, 2),
            'current_expenses': round(current_expenses, 2),
            'current_profit': round(current_profit, 2),
            'total_transactions': current_sales['transactions'] or 0,
            'low_stock_products': low_stock_products,
            'total_products': total_products,
            'current_month': current_month_start.strftime('%B %Y'),
        })
        
        # ایجاد نمودار خلاصه برای صفحه اصلی
        context['summary_chart'] = create_summary_chart(context)
        
    except Exception as e:
        context['error'] = f'خطا در بارگذاری اطلاعات: {str(e)}'
        print(f"Error in dashboard_home: {e}")
    
    return render(request, 'dashboard/index.html', context)


@login_required(login_url='/accounts/login/')
@cache_page(60 * 15)
@vary_on_cookie
def financial_forecast(request):
    """
    صفحه اصلی پیش‌بینی مالی
    نمایش نتایج پیش‌بینی درآمد ماه آینده با استفاده از مدل‌های مختلف
    """
    context = {}
    
    try:
        # دریافت داده فروش از دیتابیس
        sales_data = MonthlySales.objects.all().values('month', 'revenue', 'transaction_count')
        
        if len(sales_data) < 6:
            # داده کافی نیست
            context['error'] = 'داده کافی برای پیش‌بینی وجود ندارد. حداقل به 6 ماه داده نیاز است.'
            context['data_count'] = len(sales_data)
            return render(request, 'dashboard/forecast.html', context)
        
        # تبدیل به دیتافریم pandas
        df = pd.DataFrame(list(sales_data))
        df['month'] = pd.to_datetime(df['month'])
        df = df.sort_values('month')
        
        # مقداردهی اولیه پیش‌بینی‌کننده
        predictor = FinancialPredictor()
        
        # آماده‌سازی داده
        X, y = predictor.prepare_data(df, target_column='revenue')
        
        if len(X) < 4:
            context['error'] = 'داده کافی پس از آماده‌سازی وجود ندارد'
            return render(request, 'dashboard/forecast.html', context)
        
        # آموزش همه مدل‌ها
        best_model = predictor.train_all_models(X, y)
        
        # پیش‌بینی برای ماه آینده
        last_data = df.tail(3).copy()
        next_month_prediction = predict_next_month(predictor, best_model, last_data)
        
        # محاسبه شاخص‌های کلیدی
        total_revenue = df['revenue'].sum()
        avg_revenue = df['revenue'].mean()
        max_revenue = df['revenue'].max()
        min_revenue = df['revenue'].min()
        revenue_growth = calculate_growth_rate(df['revenue'].values)
        
        # دریافت بهترین متریک‌ها
        best_metrics = predictor.results[best_model]
        
        # ایجاد نمودارها
        chart_forecast = create_forecast_chart(
            best_metrics['actual'], 
            best_metrics['predictions'], 
            best_model
        )
        
        chart_feature_importance = None
        if best_model == 'random_forest':
            feature_importance = predictor.models['random_forest'].feature_importances_
            feature_names = X.columns.tolist()
            chart_feature_importance = create_feature_importance_chart(feature_names, feature_importance)
        
        chart_historical = create_historical_trend_chart(df)
        
        # ذخیره نتایج در context
        context = {
            'best_model': best_model,
            'results': predictor.results,
            'mae': round(best_metrics['MAE'], 2),
            'rmse': round(best_metrics['RMSE'], 2),
            'r2': round(best_metrics['R2'], 4),
            'next_month_prediction': round(next_month_prediction, 2),
            'next_month_date': get_next_month_name(),
            'total_revenue': round(total_revenue, 2),
            'avg_revenue': round(avg_revenue, 2),
            'max_revenue': round(max_revenue, 2),
            'min_revenue': round(min_revenue, 2),
            'revenue_growth': round(revenue_growth, 2),
            'data_count': len(df),
            'chart_forecast': chart_forecast,
            'chart_feature_importance': chart_feature_importance,
            'chart_historical': chart_historical,
            'last_update': timezone.now(),
        }
        
    except Exception as e:
        context['error'] = f'خطا در پردازش داده: {str(e)}'
        print(f"Error in financial_forecast: {e}")
    
    return render(request, 'dashboard/forecast.html', context)


@login_required
def kpi_dashboard(request):
    """
    داشبورد نمایش شاخص‌های کلیدی عملکرد (KPI)
    """
    context = {}
    
    try:
        # تاریخ‌های جاری و ماه قبل
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        # آمار فروش ماه جاری
        current_sales = MonthlySales.objects.filter(
            month__year=today.year,
            month__month=today.month
        ).aggregate(
            revenue=Sum('revenue'),
            transactions=Sum('transaction_count')
        )
        
        # آمار فروش ماه قبل
        last_sales = MonthlySales.objects.filter(
            month__year=last_month_start.year,
            month__month=last_month_start.month
        ).aggregate(
            revenue=Sum('revenue'),
            transactions=Sum('transaction_count')
        )
        
        # محاسبه درصد تغییرات
        current_revenue = current_sales['revenue'] or 0
        last_revenue = last_sales['revenue'] or 1
        revenue_change = ((current_revenue - last_revenue) / last_revenue) * 100
        
        # آمار هزینه‌ها
        current_expenses = Expense.objects.filter(
            date__year=today.year,
            date__month=today.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        last_expenses = Expense.objects.filter(
            date__year=last_month_start.year,
            date__month=last_month_start.month
        ).aggregate(total=Sum('amount'))['total'] or 1
        expense_change = ((current_expenses - last_expenses) / last_expenses) * 100
        
        # سودآوری
        current_profit = current_revenue - current_expenses
        last_profit = last_revenue - last_expenses
        profit_change = ((current_profit - last_profit) / (last_profit or 1)) * 100
        
        # آمار موجودی
        total_inventory_value = Product.objects.aggregate(
            total=Sum('quantity * unit_price')
        )['total'] or 0
        
        low_stock_count = Product.objects.filter(quantity__lte=10).count()
        
        # دسته‌بندی هزینه‌ها
        expense_by_category = Expense.objects.filter(
            date__year=today.year,
            date__month=today.month
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')[:5]
        
        context = {
            'current_revenue': round(current_revenue, 2),
            'revenue_change': round(revenue_change, 2),
            'current_expenses': round(current_expenses, 2),
            'expense_change': round(expense_change, 2),
            'current_profit': round(current_profit, 2),
            'profit_change': round(profit_change, 2),
            'total_transactions': current_sales['transactions'] or 0,
            'total_inventory_value': round(total_inventory_value, 2),
            'low_stock_count': low_stock_count,
            'expense_by_category': list(expense_by_category),
            'current_month': today.strftime('%B %Y'),
            'last_month': last_month_start.strftime('%B %Y'),
        }
        
        # ایجاد نمودارهای KPI
        context['kpi_chart'] = create_kpi_chart(context)
        
    except Exception as e:
        context['error'] = f'خطا در بارگذاری KPI: {str(e)}'
    
    return render(request, 'dashboard/kpi_dashboard.html', context)


@login_required
@cache_page(60 * 5)
def forecast_api(request):
    """
    API برای دریافت داده‌های پیش‌بینی (فرمت JSON)
    """
    try:
        sales_data = MonthlySales.objects.all().values('month', 'revenue')
        
        if len(sales_data) < 6:
            return JsonResponse({
                'status': 'error',
                'message': 'داده کافی برای پیش‌بینی وجود ندارد'
            }, status=400)
        
        df = pd.DataFrame(list(sales_data))
        df['month'] = pd.to_datetime(df['month'])
        df = df.sort_values('month')
        
        predictor = FinancialPredictor()
        X, y = predictor.prepare_data(df)
        best_model = predictor.train_all_models(X, y)
        
        response_data = {
            'status': 'success',
            'best_model': best_model,
            'metrics': {
                'mae': predictor.results[best_model]['MAE'],
                'rmse': predictor.results[best_model]['RMSE'],
                'r2': predictor.results[best_model]['R2']
            },
            'predictions': predictor.results[best_model]['predictions'].tolist(),
            'actual': predictor.results[best_model]['actual'].tolist(),
            'data_points': len(df)
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def export_report(request, format='csv'):
    """
    خروجی گرفتن از گزارش‌ها در فرمت CSV یا Excel
    """
    try:
        sales_data = MonthlySales.objects.all().values('month', 'revenue', 'transaction_count')
        df = pd.DataFrame(list(sales_data))
        
        if format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="financial_report.csv"'
            df.to_csv(response, index=False, encoding='utf-8-sig')
            return response
        
        elif format == 'excel':
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="financial_report.xlsx"'
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Sales Data', index=False)
            return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def comparison_view(request):
    """
    صفحه مقایسه مدل‌های مختلف
    """
    context = {}
    
    try:
        sales_data = MonthlySales.objects.all().values('month', 'revenue')
        
        if len(sales_data) >= 6:
            df = pd.DataFrame(list(sales_data))
            df['month'] = pd.to_datetime(df['month'])
            df = df.sort_values('month')
            
            predictor = FinancialPredictor()
            X, y = predictor.prepare_data(df)
            best_model = predictor.train_all_models(X, y)
            
            # آماده‌سازی داده برای جدول مقایسه
            comparison_data = []
            for name, metrics in predictor.results.items():
                comparison_data.append({
                    'model': name.replace('_', ' ').title(),
                    'mae': round(metrics['MAE'], 2),
                    'rmse': round(metrics['RMSE'], 2),
                    'r2': round(metrics['R2'], 4),
                    'is_best': name == best_model
                })
            
            context = {
                'comparison_data': comparison_data,
                'best_model': best_model.replace('_', ' ').title(),
                'total_models': len(comparison_data)
            }
            
    except Exception as e:
        context['error'] = str(e)
    
    return render(request, 'dashboard/comparison.html', context)


@login_required
def settings_view(request):
    """
    صفحه تنظیمات داشبورد
    """
    if request.method == 'POST':
        # ذخیره تنظیمات کاربر
        theme = request.POST.get('theme', 'light')
        default_dashboard = request.POST.get('default_dashboard', 'kpi')
        email_notifications = request.POST.get('email_notifications') == 'on'
        
        UserPreference.objects.update_or_create(
            user=request.user,
            defaults={
                'theme': theme,
                'default_dashboard': default_dashboard,
                'email_notifications': email_notifications
            }
        )
        
        context = {'message': 'تنظیمات با موفقیت ذخیره شد'}
    else:
        try:
            prefs = UserPreference.objects.get(user=request.user)
            context = {
                'theme': prefs.theme,
                'default_dashboard': prefs.default_dashboard,
                'email_notifications': prefs.email_notifications
            }
        except UserPreference.DoesNotExist:
            context = {
                'theme': 'light',
                'default_dashboard': 'kpi',
                'email_notifications': False
            }
    
    return render(request, 'dashboard/settings.html', context)


# ==================== توابع کمکی (Helper Functions) ====================

def create_summary_chart(context):
    """ایجاد نمودار خلاصه برای صفحه اصلی"""
    plt.figure(figsize=(10, 5))
    
    categories = ['درآمد', 'هزینه', 'سود']
    values = [
        context.get('current_revenue', 0),
        context.get('current_expenses', 0),
        context.get('current_profit', 0)
    ]
    colors = ['#10B981', '#EF4444', '#3B82F6']
    
    bars = plt.bar(categories, values, color=colors, width=0.5)
    plt.title('خلاصه مالی ماه جاری', fontsize=14, fontweight='bold')
    plt.ylabel('مبلغ (افغانی)', fontsize=12)
    
    # افزودن مقادیر روی میله‌ها
    for bar, value in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                f'{value:,.0f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    return save_plot_to_base64()


def predict_next_month(predictor, best_model_name, last_data):
    """پیش‌بینی درآمد ماه آینده"""
    try:
        model = predictor.models[best_model_name]
        last_revenue = last_data['revenue'].values
        
        if len(last_revenue) >= 3:
            features = np.array([
                last_revenue[-1],
                last_revenue[-2],
                last_revenue[-3],
                np.mean(last_revenue[-3:])
            ]).reshape(1, -1)
            
            prediction = model.predict(features)[0]
            return max(prediction, last_revenue[-1] * 0.5)
        else:
            return last_revenue[-1] * 1.05
            
    except Exception as e:
        print(f"Error in predict_next_month: {e}")
        return last_data['revenue'].iloc[-1] * 1.05


def calculate_growth_rate(values):
    """محاسبه نرخ رشد"""
    if len(values) < 2:
        return 0
    
    n = len(values)
    if n >= 12:
        first_year_avg = np.mean(values[:12])
        last_year_avg = np.mean(values[-12:])
        if first_year_avg > 0:
            return ((last_year_avg - first_year_avg) / first_year_avg) * 100
    else:
        if values[0] > 0:
            return ((values[-1] - values[0]) / values[0]) * 100
    
    return 0


def get_next_month_name():
    """دریافت نام ماه آینده"""
    next_month = timezone.now().date().replace(day=1) + timedelta(days=32)
    return next_month.strftime('%B %Y')


def create_forecast_chart(actual, predicted, model_name):
    """ایجاد نمودار مقایسه مقادیر واقعی و پیش‌بینی شده"""
    plt.figure(figsize=(12, 6))
    
    x = range(len(actual))
    
    plt.plot(x, actual, 'b-o', label='مقادیر واقعی', linewidth=2, markersize=6)
    plt.plot(x, predicted, 'r--s', label='مقادیر پیش‌بینی شده', linewidth=2, markersize=6)
    
    plt.xlabel('دوره (ماه)', fontsize=12)
    plt.ylabel('درآمد (افغانی)', fontsize=12)
    plt.title(f'پیش‌بینی درآمد با مدل {model_name.replace("_", " ").title()}', fontsize=14)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return save_plot_to_base64()


def create_feature_importance_chart(feature_names, importance_values):
    """ایجاد نمودار اهمیت ویژگی‌ها"""
    plt.figure(figsize=(10, 6))
    
    indices = np.argsort(importance_values)[::-1]
    sorted_names = [feature_names[i] for i in indices[:8]]
    sorted_importance = importance_values[indices[:8]]
    
    persian_names = {
        'month_lag_1': 'درآمد ماه قبل',
        'month_lag_2': 'درآمد دو ماه قبل',
        'month_lag_3': 'درآمد سه ماه قبل',
        'rolling_mean_3': 'میانگین متحرک ۳ ماهه',
        'transaction_count': 'تعداد تراکنش‌ها'
    }
    
    display_names = [persian_names.get(name, name) for name in sorted_names]
    
    plt.barh(display_names, sorted_importance, color='teal')
    plt.xlabel('درجه اهمیت', fontsize=12)
    plt.title('اهمیت ویژگی‌ها در پیش‌بینی درآمد', fontsize=14)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    
    return save_plot_to_base64()


def create_historical_trend_chart(df):
    """ایجاد نمودار روند تاریخی درآمد"""
    plt.figure(figsize=(12, 6))
    
    months = df['month'].dt.strftime('%Y-%m').values
    revenues = df['revenue'].values
    
    plt.plot(months, revenues, 'g-^', linewidth=2, markersize=8)
    plt.fill_between(range(len(months)), revenues, alpha=0.3)
    
    plt.xlabel('ماه', fontsize=12)
    plt.ylabel('درآمد (افغانی)', fontsize=12)
    plt.title('روند تاریخی درآمد', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3)
    
    z = np.polyfit(range(len(revenues)), revenues, 1)
    p = np.poly1d(z)
    plt.plot(range(len(months)), p(range(len(revenues))), 'r--', label='خط روند', linewidth=2)
    plt.legend()
    
    plt.tight_layout()
    return save_plot_to_base64()


def create_kpi_chart(context):
    """ایجاد نمودار خلاصه KPI"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    categories = ['درآمد', 'هزینه', 'سود']
    values = [
        context.get('current_revenue', 0),
        context.get('current_expenses', 0),
        context.get('current_profit', 0)
    ]
    colors = ['green', 'red', 'blue']
    axes[0, 0].bar(categories, values, color=colors)
    axes[0, 0].set_title('خلاصه مالی ماه جاری')
    axes[0, 0].set_ylabel('افغانی')
    
    changes = [
        context.get('revenue_change', 0),
        context.get('expense_change', 0),
        context.get('profit_change', 0)
    ]
    change_colors = ['green' if x >= 0 else 'red' for x in changes]
    axes[0, 1].bar(categories, changes, color=change_colors)
    axes[0, 1].set_title('تغییرات نسبت به ماه قبل (%)')
    axes[0, 1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    expense_data = context.get('expense_by_category', [])
    if expense_data:
        exp_cats = [item['category__name'] for item in expense_data]
        exp_vals = [item['total'] for item in expense_data]
        axes[1, 0].pie(exp_vals, labels=exp_cats, autopct='%1.1f%%')
        axes[1, 0].set_title('توزیع هزینه‌ها بر اساس دسته')
    
    axes[1, 1].text(0.5, 0.6, f"کل ارزش موجودی:\n{context.get('total_inventory_value', 0):,.0f} AFN", 
                    ha='center', va='center', fontsize=12, transform=axes[1, 1].transAxes)
    axes[1, 1].text(0.5, 0.3, f"کالاهای با موجودی کم:\n{context.get('low_stock_count', 0)} قلم", 
                    ha='center', va='center', fontsize=12, transform=axes[1, 1].transAxes)
    axes[1, 1].set_title('وضعیت انبار')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    return save_plot_to_base64()


def save_plot_to_base64():
    """ذخیره نمودار فعلی در قالب base64 برای نمایش در HTML"""
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    return image_base64