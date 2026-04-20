# dashboard/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # صفحات اصلی
    path('', views.dashboard_home, name='dashboard_home'),  # ← این خط مهم است
    path('forecast/', views.financial_forecast, name='financial_forecast'),
    path('kpi/', views.kpi_dashboard, name='kpi_dashboard'),
    path('comparison/', views.comparison_view, name='comparison'),
    path('settings/', views.settings_view, name='dashboard_settings'),
    
    # APIها
    path('api/forecast-data/', views.forecast_api, name='forecast_api'),
    
    # خروجی گزارشات
    path('export/csv/', views.export_report, {'format': 'csv'}, name='export_csv'),
    path('export/excel/', views.export_report, {'format': 'excel'}, name='export_excel'),
]