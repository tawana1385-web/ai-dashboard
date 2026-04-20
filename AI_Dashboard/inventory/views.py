# inventory/views.py - نسخه کامل و صحیح

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
import pandas as pd

from .models import Product, InventoryMovement


@login_required
def product_list(request):
    """
    نمایش لیست محصولات
    """
    products = Product.objects.all().order_by('product_code')
    
    # فیلتر بر اساس دسته
    category = request.GET.get('category')
    if category:
        products = products.filter(category=category)
    
    # فیلتر بر اساس موجودی کم
    low_stock = request.GET.get('low_stock')
    if low_stock == 'yes':
        products = products.filter(quantity__lte=F('reorder_level'))
    
    # فیلتر بر اساس جستجو
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(product_code__icontains=search) |
            Q(barcode__icontains=search)
        )
    
    # صفحه‌بندی
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # آمار
    total_products = products.count()
    total_value = sum(p.total_value for p in products)
    low_stock_count = products.filter(quantity__lte=F('reorder_level')).count()
    
    # دسته‌بندی‌ها
    categories = Product.objects.exclude(category__isnull=True).exclude(category='').values_list('category', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'categories': categories,
        'selected_category': category,
        'search': search,
        'low_stock_filter': low_stock,
        'title': 'لیست محصولات',
    }
    
    return render(request, 'inventory/product_list.html', context)


@login_required
def add_product(request):
    """
    افزودن محصول جدید
    """
    if request.method == 'POST':
        try:
            product = Product()
            product.product_code = request.POST.get('product_code')
            product.name = request.POST.get('name')
            product.category = request.POST.get('category')
            product.unit = request.POST.get('unit')
            product.quantity = int(request.POST.get('quantity', 0))
            product.unit_price = float(request.POST.get('unit_price', 0))
            product.reorder_level = int(request.POST.get('reorder_level', 10))
            product.description = request.POST.get('description', '')
            product.supplier = request.POST.get('supplier', '')
            product.location = request.POST.get('location', '')
            product.save()
            
            messages.success(request, 'محصول با موفقیت اضافه شد.')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'خطا: {str(e)}')
    
    context = {
        'title': 'افزودن محصول جدید',
    }
    return render(request, 'inventory/add_product.html', context)


@login_required
def edit_product(request, pk):
    """
    ویرایش محصول
    """
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        try:
            product.product_code = request.POST.get('product_code')
            product.name = request.POST.get('name')
            product.category = request.POST.get('category')
            product.unit = request.POST.get('unit')
            product.quantity = int(request.POST.get('quantity', 0))
            product.unit_price = float(request.POST.get('unit_price', 0))
            product.reorder_level = int(request.POST.get('reorder_level', 10))
            product.description = request.POST.get('description', '')
            product.supplier = request.POST.get('supplier', '')
            product.location = request.POST.get('location', '')
            product.save()
            
            messages.success(request, 'محصول با موفقیت ویرایش شد.')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'خطا: {str(e)}')
    
    context = {
        'product': product,
        'title': 'ویرایش محصول',
    }
    return render(request, 'inventory/edit_product.html', context)


@login_required
def delete_product(request, pk):
    """
    حذف محصول
    """
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'محصول با موفقیت حذف شد.')
        return redirect('product_list')
    
    context = {
        'product': product,
        'title': 'حذف محصول',
    }
    return render(request, 'inventory/delete_product.html', context)


@login_required
def product_detail(request, pk):
    """
    نمایش جزئیات محصول
    """
    product = get_object_or_404(Product, pk=pk)
    movements = InventoryMovement.objects.filter(product=product).order_by('-created_at')[:20]
    
    context = {
        'product': product,
        'movements': movements,
        'title': f'جزئیات {product.name}',
    }
    return render(request, 'inventory/product_detail.html', context)


@login_required
def movement_list(request):
    """
    نمایش لیست حرکات انبار
    """
    movements = InventoryMovement.objects.all().order_by('-created_at')
    
    movement_type = request.GET.get('type')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    paginator = Paginator(movements, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'movement_type': movement_type,
        'title': 'لیست حرکات انبار',
    }
    return render(request, 'inventory/movement_list.html', context)


@login_required
def add_movement(request):
    """
    ثبت حرکت جدید انبار
    """
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product')
            product = get_object_or_404(Product, pk=product_id)
            
            movement = InventoryMovement(
                product=product,
                movement_type=request.POST.get('movement_type'),
                quantity=int(request.POST.get('quantity', 0)),
                reference_number=request.POST.get('reference_number', ''),
                description=request.POST.get('description', ''),
                created_by=request.user.username
            )
            movement.save()
            
            messages.success(request, 'حرکت انبار با موفقیت ثبت شد.')
            return redirect('movement_list')
        except Exception as e:
            messages.error(request, f'خطا: {str(e)}')
    
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'products': products,
        'title': 'ثبت حرکت جدید',
    }
    return render(request, 'inventory/add_movement.html', context)


@login_required
def inventory_dashboard(request):
    """
    داشبورد موجودی
    """
    total_products = Product.objects.filter(is_active=True).count()
    total_value = sum(p.total_value for p in Product.objects.filter(is_active=True))
    low_stock_products = Product.objects.filter(is_active=True, quantity__lte=F('reorder_level')).count()
    out_of_stock = Product.objects.filter(quantity=0, is_active=True).count()
    
    today = timezone.now().date()
    today_movements = InventoryMovement.objects.filter(created_at__date=today).count()
    
    # محصولات پرمتقاضی
    top_products = InventoryMovement.objects.filter(
        movement_type='out'
    ).values('product__name', 'product__product_code').annotate(
        total_out=Sum('quantity')
    ).order_by('-total_out')[:5]
    
    context = {
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
        'today_movements': today_movements,
        'top_products': top_products,
        'title': 'داشبورد موجودی',
    }
    return render(request, 'inventory/inventory_dashboard.html', context)


@login_required
def low_stock_report(request):
    """
    گزارش محصولات با موجودی کم
    """
    products = Product.objects.filter(
        is_active=True,
        quantity__lte=F('reorder_level')
    ).order_by('quantity')
    
    context = {
        'products': products,
        'count': products.count(),
        'title': 'گزارش موجودی کم',
    }
    return render(request, 'inventory/low_stock_report.html', context)


@login_required
def inventory_value_report(request):
    """
    گزارش ارزش موجودی
    """
    products = Product.objects.filter(is_active=True).order_by('-quantity')
    total_value = sum(p.total_value for p in products)
    
    context = {
        'products': products,
        'total_value': total_value,
        'title': 'گزارش ارزش موجودی',
    }
    return render(request, 'inventory/inventory_value_report.html', context)


@login_required
def products_api(request):
    """
    API محصولات
    """
    products = Product.objects.filter(is_active=True).values(
        'id', 'product_code', 'name', 'category', 'quantity', 'unit_price', 'reorder_level'
    )
    return JsonResponse({'status': 'success', 'data': list(products)})


@login_required
def movements_api(request):
    """
    API حرکات انبار
    """
    movements = InventoryMovement.objects.all().order_by('-created_at').values(
        'id', 'product__name', 'movement_type', 'quantity', 'created_at'
    )[:100]
    
    data = []
    for m in movements:
        data.append({
            'id': m['id'],
            'product': m['product__name'],
            'movement_type': m['movement_type'],
            'quantity': m['quantity'],
            'created_at': m['created_at'].strftime('%Y-%m-%d %H:%M')
        })
    
    return JsonResponse({'status': 'success', 'data': data})


@login_required
def export_inventory_csv(request):
    """
    خروجی CSV
    """
    products = Product.objects.filter(is_active=True).values(
        'product_code', 'name', 'category', 'quantity', 'unit_price', 'location'
    )
    df = pd.DataFrame(list(products))
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_data.csv"'
    df.to_csv(response, index=False, encoding='utf-8-sig')
    return response


@login_required
def export_inventory_excel(request):
    """
    خروجی Excel
    """
    products = Product.objects.filter(is_active=True).values(
        'product_code', 'name', 'category', 'quantity', 'unit_price', 'location'
    )
    df = pd.DataFrame(list(products))
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="inventory_data.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Inventory', index=False)
    
    return response