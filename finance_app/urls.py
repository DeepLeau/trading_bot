from django.urls import path
from .views import fetch_data_view, backtesting_view, predict_stock_prices, generate_performance_report

urlpatterns = [
    path('fetch-stock-data/<str:symbol>/', fetch_data_view, name='fetch_stock_data'),
    path('predict-stock/<str:symbol>/', predict_stock_prices, name='predict_stock_prices'),
    path('backtesting/', backtesting_view, name='backtesting'),
    path('report/<str:symbol>/', generate_performance_report, name='generate_report')
]
