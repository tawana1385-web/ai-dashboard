# expenses/views.py - کد کامل

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

from .models import Expense, ExpenseCategory
from .forms import ExpenseForm, ExpenseCategoryForm


@login_required
def expense_list(request):
    """
    نمایش لیست هزینه‌ها
    """
    # دریافت همه هزینه‌ها
    expenses = Expense.objects.all().order_by('-date')
    
    # فیلتر بر اساس دسته
    category = request.GET.get('category')
    if category:
        expenses = expenses.filter(category_id=category)
    
    # فیلتر بر اساس تاریخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    if from_date:
        expenses = expenses.filter(date__gte=from_date)
    if to_date:
        expenses = expenses.filter(date__lte=to_date)
    
    # فیلتر بر اساس جستجو
    search = request.GET.get('search')
    if search:
        expenses = expenses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # صفحه‌بندی
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # آمار کلی
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    avg_expense = expenses.aggregate(avg=Avg('amount'))['avg'] or 0
    expense_count = expenses.count()
    
    # دریافت دسته‌بندی‌ها برای فیلتر
    categories = ExpenseCategory.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'total_expenses': total_expenses,
        'avg_expense': avg_expense,
        'expense_count': expense_count,
        'categories': categories,
        'selected_category': category,
        'from_date': from_date,
        'to_date': to_date,
        'title': 'لیست هزینه‌ها',
    }
    
    return render(request, 'expenses/expense_list.html', context)


@login_required
def add_expense(request):
    """
    افزودن هزینه جدید
    """
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user.username
            expense.save()
            messages.success(request, 'هزینه با موفقیت اضافه شد.')
            return redirect('expense_list')
        else:
            messages.error(request, 'خطا در ثبت اطلاعات. لطفاً دوباره تلاش کنید.')
    else:
        form = ExpenseForm()
    
    context = {
        'form': form,
        'title': 'افزودن هزینه جدید',
    }
    
    return render(request, 'expenses/add_expense.html', context)


@login_required
def edit_expense(request, pk):
    """
    ویرایش هزینه
    """
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'هزینه با موفقیت ویرایش شد.')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    
    context = {
        'form': form,
        'expense': expense,
        'title': 'ویرایش هزینه',
    }
    
    return render(request, 'expenses/edit_expense.html', context)


@login_required
def delete_expense(request, pk):
    """
    حذف هزینه
    """
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'هزینه با موفقیت حذف شد.')
        return redirect('expense_list')
    
    context = {
        'expense': expense,
        'title': 'حذف هزینه',
    }
    
    return render(request, 'expenses/delete_expense.html', context)


@login_required
def expense_detail(request, pk):
    """
    نمایش جزئیات یک هزینه
    """
    expense = get_object_or_404(Expense, pk=pk)
    
    context = {
        'expense': expense,
        'title': f'جزئیات هزینه - {expense.title}',
    }
    
    return render(request, 'expenses/expense_detail.html', context)


@login_required
def expense_api(request):
    """
    API برای دریافت داده‌های هزینه (فرمت JSON)
    """
    try:
        expenses = Expense.objects.all().values('id', 'title', 'amount', 'date', 'category__name', 'status')
        
        # تبدیل به لیست برای JSON
        data = []
        for expense in expenses:
            data.append({
                'id': expense['id'],
                'title': expense['title'],
                'amount': float(expense['amount']),
                'date': expense['date'].strftime('%Y-%m-%d'),
                'category': expense['category__name'],
                'status': expense['status']
            })
        
        # آمار کلی
        total_amount = sum(item['amount'] for item in data)
        avg_amount = total_amount / len(data) if data else 0
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total_amount': total_amount,
            'avg_amount': avg_amount,
            'count': len(data)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def expense_chart_data(request):
    """
    API برای داده‌های نمودار هزینه
    """
    try:
        # دریافت داده 12 ماه اخیر
        last_year = timezone.now().date() - timedelta(days=365)
        expenses = Expense.objects.filter(
            date__gte=last_year
        ).values('date').annotate(
            total=Sum('amount')
        ).order_by('date')
        
        dates = [item['date'].strftime('%Y-%m') for item in expenses]
        amounts = [float(item['total']) for item in expenses]
        
        # هزینه بر اساس دسته‌بندی
        category_expenses = Expense.objects.filter(
            date__gte=last_year
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        categories = [item['category__name'] or 'بدون دسته' for item in category_expenses]
        category_amounts = [float(item['total']) for item in category_expenses]
        
        return JsonResponse({
            'status': 'success',
            'dates': dates,
            'amounts': amounts,
            'categories': categories,
            'category_amounts': category_amounts,
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def expense_dashboard(request):
    """
    داشبورد مخصوص هزینه‌ها
    """
    context = {}
    
    try:
        # تاریخ امروز
        today = timezone.now().date()
        
        # هزینه ماه جاری
        current_month_expenses = Expense.objects.filter(
            date__year=today.year,
            date__month=today.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # هزینه ماه قبل
        last_month = today.replace(day=1) - timedelta(days=1)
        last_month_expenses = Expense.objects.filter(
            date__year=last_month.year,
            date__month=last_month.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # هزینه کل
        total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        # هزینه بر اساس دسته‌بندی (بالاترین 5 دسته)
        top_categories = Expense.objects.filter(
            date__year=today.year
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')[:5]
        
        # محاسبه رشد
        growth = ((current_month_expenses - last_month_expenses) / (last_month_expenses or 1)) * 100
        
        # میانگین هزینه ماهانه
        months_count = Expense.objects.dates('date', 'month').count()
        avg_monthly = total_expenses / (months_count or 1)
        
        context = {
            'current_month_expenses': current_month_expenses,
            'last_month_expenses': last_month_expenses,
            'growth_percent': round(growth, 2),
            'total_expenses': total_expenses,
            'avg_monthly_expenses': round(avg_monthly, 2),
            'top_categories': top_categories,
            'current_month': today.strftime('%B %Y'),
            'last_month_name': last_month.strftime('%B %Y'),
        }
        
    except Exception as e:
        context['error'] = str(e)
    
    return render(request, 'expenses/expense_dashboard.html', context)


@login_required
def export_expenses_csv(request):
    """
    خروجی CSV از هزینه‌ها
    """
    expenses = Expense.objects.all().values('title', 'amount', 'date', 'category__name', 'description')
    
    df = pd.DataFrame(list(expenses))
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=False)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses_data.csv"'
    df.to_csv(response, index=False, encoding='utf-8-sig')
    
    return response


@login_required
def export_expenses_excel(request):
    """
    خروجی Excel از هزینه‌ها
    """
    expenses = Expense.objects.all().values('title', 'amount', 'date', 'category__name', 'description')
    
    df = pd.DataFrame(list(expenses))
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=False)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="expenses_data.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Expenses Data', index=False)
    
    return response


# ==================== دسته‌بندی هزینه‌ها ====================

@login_required
def category_list(request):
    """
    نمایش لیست دسته‌بندی هزینه‌ها
    """
    categories = ExpenseCategory.objects.all().order_by('name')
    
    context = {
        'categories': categories,
        'title': 'لیست دسته‌بندی هزینه‌ها',
    }
    
    return render(request, 'expenses/category_list.html', context)


@login_required
def add_category(request):
    """
    افزودن دسته‌بندی جدید
    """
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'دسته‌بندی با موفقیت اضافه شد.')
            return redirect('category_list')
    else:
        form = ExpenseCategoryForm()
    
    context = {
        'form': form,
        'title': 'افزودن دسته‌بندی جدید',
    }
    
    return render(request, 'expenses/add_category.html', context)


@login_required
def edit_category(request, pk):
    """
    ویرایش دسته‌بندی
    """
    category = get_object_or_404(ExpenseCategory, pk=pk)
    
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'دسته‌بندی با موفقیت ویرایش شد.')
            return redirect('category_list')
    else:
        form = ExpenseCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': 'ویرایش دسته‌بندی',
    }
    
    return render(request, 'expenses/edit_category.html', context)


@login_required
def delete_category(request, pk):
    """
    حذف دسته‌بندی
    """
    category = get_object_or_404(ExpenseCategory, pk=pk)
    
    if request.method == 'POST':
        # بررسی وجود هزینه در این دسته
        if Expense.objects.filter(category=category).exists():
            messages.error(request, 'این دسته‌بندی دارای هزینه است. ابتدا هزینه‌ها را انتقال دهید.')
        else:
            category.delete()
            messages.success(request, 'دسته‌بندی با موفقیت حذف شد.')
        return redirect('category_list')
    
    context = {
        'category': category,
        'title': 'حذف دسته‌بندی',
    }
    
    return render(request, 'expenses/delete_category.html', context)