// static/js/script.js

// توابع کمکی برای فرمت اعداد
function formatNumber(num) {
    return new Intl.NumberFormat('fa-IR').format(num);
}

function formatCurrency(amount) {
    return formatNumber(amount) + ' AFN';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('fa-IR');
}

// تابع برای نمایش نوتیفیکیشن
function showNotification(title, message, type = 'info') {
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-yellow-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-20 left-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-full`;
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <div>
                <p class="font-bold">${title}</p>
                <p class="text-sm">${message}</p>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// تابع برای بارگذاری داده‌های نمودار
async function loadChartData(url, chartId, chartType = 'line') {
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'success') {
            const ctx = document.getElementById(chartId).getContext('2d');
            new Chart(ctx, {
                type: chartType,
                data: {
                    labels: data.labels || data.months || data.dates,
                    datasets: [{
                        label: data.datasetLabel || 'مقدار',
                        data: data.values || data.revenues || data.amounts,
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            rtl: true
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error loading chart:', error);
        showNotification('خطا', 'مشکلی در بارگذاری نمودار وجود دارد', 'error');
    }
}

// تابع برای جستجو
function setupSearch(searchInputId, tableId) {
    const searchInput = document.getElementById(searchInputId);
    const table = document.getElementById(tableId);
    
    if (searchInput && table) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

// تابع برای صادرات جدول به Excel
function exportToExcel(tableId, filename = 'report.xlsx') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = [];
    const headers = [];
    
    // استخراج هدرها
    table.querySelectorAll('thead th').forEach(th => {
        headers.push(th.textContent.trim());
    });
    rows.push(headers);
    
    // استخراج داده‌ها
    table.querySelectorAll('tbody tr').forEach(tr => {
        const row = [];
        tr.querySelectorAll('td').forEach(td => {
            row.push(td.textContent.trim());
        });
        rows.push(row);
    });
    
    // تبدیل به CSV
    const csv = rows.map(row => row.join(',')).join('\n');
    const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.href = url;
    link.setAttribute('download', filename.replace('.xlsx', '.csv'));
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('موفق', 'گزارش با موفقیت دانلود شد', 'success');
}

// اجرای توابع پس از بارگذاری صفحه
document.addEventListener('DOMContentLoaded', function() {
    // فعال کردن tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(el => {
        el.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute bg-gray-800 text-white text-xs px-2 py-1 rounded z-50 whitespace-nowrap';
            tooltip.textContent = el.dataset.tooltip;
            tooltip.style.top = (e.target.offsetTop - 30) + 'px';
            tooltip.style.left = e.target.offsetLeft + 'px';
            document.body.appendChild(tooltip);
            
            el.addEventListener('mouseleave', () => {
                tooltip.remove();
            });
        });
    });
});