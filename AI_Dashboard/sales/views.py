# sales/views.py - کد کامل

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta
import pandas as pd
import json

from .models import MonthlySales, SalesTransaction
from .forms import MonthlySalesForm, SalesTransactionForm


@login_required
def sales_list(request):
    """
    نمایش لیست فروش‌ها
    """
    # دریافت همه فروش‌ها
    sales = MonthlySales.objects.all().order_by('-month')
    
    # فیلتر بر اساس سال
    year = request.GET.get('year')
    if year:
        sales = sales.filter(month__year=year)
    
    # فیلتر بر اساس جستجو
    search = request.GET.get('search')
    if search:
        sales = sales.filter(
            Q(month__year__icontains=search) |
            Q(revenue__icontains=search)
        )
    
    # صفحه‌بندی
    paginator = Paginator(sales, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # آمار کلی
    total_revenue = sales.aggregate(total=Sum('revenue'))['total'] or 0
    total_transactions = sales.aggregate(total=Sum('transaction_count'))['total'] or 0
    avg_revenue = sales.aggregate(avg=Avg('revenue'))['avg'] or 0
    
    # دریافت سال‌های موجود برای فیلتر
    years = MonthlySales.objects.dates('month', 'year').values_list('month__year', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'avg_revenue': avg_revenue,
        'years': years,
        'current_year': year or datetime.now().year,
        'title': 'لیست فروش‌ها',
    }
    
    return render(request, 'sales/sales_list.html', context)


@login_required
def add_sale(request):
    """
    افزودن فروش جدید
    """
    if request.method == 'POST':
        form = MonthlySalesForm(request.POST)
        if form.is_valid():
            sale = form.save()
            messages.success(request, 'فروش با موفقیت اضافه شد.')
            return redirect('sales_list')
        else:
            messages.error(request, 'خطا در ثبت اطلاعات. لطفاً دوباره تلاش کنید.')
    else:
        form = MonthlySalesForm()
    
    context = {
        'form': form,
        'title': 'افزودن فروش جدید',
    }
    
    return render(request, 'sales/add_sale.html', context)


@login_required
def edit_sale(request, pk):
    """
    ویرایش فروش
    """
    sale = get_object_or_404(MonthlySales, pk=pk)
    
    if request.method == 'POST':
        form = MonthlySalesForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, 'فروش با موفقیت ویرایش شد.')
            return redirect('sales_list')
    else:
        form = MonthlySalesForm(instance=sale)
    
    context = {
        'form': form,
        'sale': sale,
        'title': 'ویرایش فروش',
    }
    
    return render(request, 'sales/edit_sale.html', context)


@login_required
def delete_sale(request, pk):
    """
    حذف فروش
    """
    sale = get_object_or_404(MonthlySales, pk=pk)
    
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'فروش با موفقیت حذف شد.')
        return redirect('sales_list')
    
    context = {
        'sale': sale,
        'title': 'حذف فروش',
    }
    
    return render(request, 'sales/delete_sale.html', context)


@login_required
def sale_detail(request, pk):
    """
    نمایش جزئیات یک فروش
    """
    sale = get_object_or_404(MonthlySales, pk=pk)
    
    context = {
        'sale': sale,
        'title': f'جزئیات فروش - {sale.month.strftime("%B %Y")}',
    }
    
    return render(request, 'sales/sale_detail.html', context)


@login_required
def sales_api(request):
    """
    API برای دریافت داده‌های فروش (فرمت JSON)
    """
    try:
        sales_data = MonthlySales.objects.all().values('month', 'revenue', 'transaction_count')
        
        # تبدیل به لیست برای JSON
        data = []
        for sale in sales_data:
            data.append({
                'month': sale['month'].strftime('%Y-%m-%d'),
                'revenue': float(sale['revenue']),
                'transaction_count': sale['transaction_count']
            })
        
        # آمار کلی
        total_revenue = sum(item['revenue'] for item in data)
        avg_revenue = total_revenue / len(data) if data else 0
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total_revenue': total_revenue,
            'avg_revenue': avg_revenue,
            'count': len(data)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def sales_chart_data(request):
    """
    API برای داده‌های نمودار فروش
    """
    try:
        # دریافت داده 12 ماه اخیر
        last_year = timezone.now().date() - timedelta(days=365)
        sales_data = MonthlySales.objects.filter(
            month__gte=last_year
        ).order_by('month').values('month', 'revenue')
        
        months = [item['month'].strftime('%Y-%m') for item in sales_data]
        revenues = [float(item['revenue']) for item in sales_data]
        
        return JsonResponse({
            'status': 'success',
            'months': months,
            'revenues': revenues,
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def export_sales_csv(request):
    """
    خروجی CSV از فروش‌ها
    """
    sales_data = MonthlySales.objects.all().values('month', 'revenue', 'transaction_count')
    
    df = pd.DataFrame(list(sales_data))
    df['month'] = pd.to_datetime(df['month'])
    df = df.sort_values('month')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_data.csv"'
    df.to_csv(response, index=False, encoding='utf-8-sig')
    
    return response


@login_required
def export_sales_excel(request):
    """
    خروجی Excel از فروش‌ها
    """
    sales_data = MonthlySales.objects.all().values('month', 'revenue', 'transaction_count')
    
    df = pd.DataFrame(list(sales_data))
    df['month'] = pd.to_datetime(df['month'])
    df = df.sort_values('month')
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales_data.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sales Data', index=False)
    
    return response


# ==================== توابع برای تراکنش‌های فروش ====================

@login_required
def transaction_list(request):
    """
    نمایش لیست تراکنش‌های فروش
    """
    transactions = SalesTransaction.objects.all().order_by('-transaction_date')
    
    # صفحه‌بندی
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # آمار
    total_amount = transactions.aggregate(total=Sum('amount'))['total'] or 0
    completed_count = transactions.filter(status='completed').count()
    
    context = {
        'page_obj': page_obj,
        'total_amount': total_amount,
        'completed_count': completed_count,
        'title': 'لیست تراکنش‌های فروش',
    }
    
    return render(request, 'sales/transaction_list.html', context)


@login_required
def add_transaction(request):
    """
    افزودن تراکنش فروش جدید
    """
    if request.method == 'POST':
        form = SalesTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save()
            messages.success(request, 'تراکنش با موفقیت ثبت شد.')
            return redirect('transaction_list')
    else:
        form = SalesTransactionForm()
    
    context = {
        'form': form,
        'title': 'ثبت تراکنش جدید',
    }
    
    return render(request, 'sales/add_transaction.html', context)


# ==================== داشبورد فروش ====================

@login_required
def sales_dashboard(request):
    """
    داشبورد مخصوص فروش
    """
    context = {}
    
    try:
        # تاریخ امروز
        today = timezone.now().date()
        
        # فروش ماه جاری
        current_month_sales = MonthlySales.objects.filter(
            month__year=today.year,
            month__month=today.month
        ).aggregate(
            revenue=Sum('revenue'),
            transactions=Sum('transaction_count')
        )
        
        # فروش ماه قبل
        last_month = today.replace(day=1) - timedelta(days=1)
        last_month_sales = MonthlySales.objects.filter(
            month__year=last_month.year,
            month__month=last_month.month
        ).aggregate(
            revenue=Sum('revenue'),
            transactions=Sum('transaction_count')
        )
        
        # فروش کل
        total_sales = MonthlySales.objects.aggregate(
            revenue=Sum('revenue'),
            transactions=Sum('transaction_count')
        )
        
        # بهترین ماه فروش
        best_month = MonthlySales.objects.order_by('-revenue').first()
        
        # محاسبه رشد
        current_rev = current_month_sales['revenue'] or 0
        last_rev = last_month_sales['revenue'] or 1
        growth = ((current_rev - last_rev) / last_rev) * 100
        
        context = {
            'current_month_revenue': current_rev,
            'current_month_transactions': current_month_sales['transactions'] or 0,
            'last_month_revenue': last_rev,
            'growth_percent': round(growth, 2),
            'total_revenue': total_sales['revenue'] or 0,
            'total_transactions': total_sales['transactions'] or 0,
            'best_month': best_month,
            'current_month': today.strftime('%B %Y'),
            'last_month_name': last_month.strftime('%B %Y'),
        }
        
    except Exception as e:
        context['error'] = str(e)
    
    return render(request, 'sales/sales_dashboard.html', context)