from django.test import TestCase

from finance_app.views import calculate_max_drawdown, calculate_moving_average
from .models import PredictionData, StockData
from django.urls import reverse
from datetime import datetime
from django.utils.timezone import make_aware


class BacktestingTestCase(TestCase):
    def setUp(self):
        timestamp1 = make_aware(datetime(2024, 1, 1))
        timestamp2 = make_aware(datetime(2024, 2, 1))
        timestamp3 = make_aware(datetime(2024, 3, 1))
        timestamp4 = make_aware(datetime(2024, 4, 1))

        StockData.objects.create(symbol='AAPL', timestamp=timestamp1, open_price=145, close_price=150, high_price=155, low_price=140, volume=10000)
        StockData.objects.create(symbol='AAPL', timestamp=timestamp2, open_price=155, close_price=160, high_price=165, low_price=150, volume=12000)
        StockData.objects.create(symbol='AAPL', timestamp=timestamp3, open_price=165, close_price=170, high_price=175, low_price=160, volume=13000)
        StockData.objects.create(symbol='AAPL', timestamp=timestamp4, open_price=175, close_price=180, high_price=185, low_price=170, volume=14000)
    
    def test_backtesting(self):
        response = self.client.get(reverse('backtesting'), {'symbol': 'AAPL', 'initial_investment': 10000})
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_return', response.json())
        self.assertIn('positions', response.json())
    
    def test_backtesting_no_investment(self):
        response = self.client.get(reverse('backtesting'), {'symbol': 'AAPL'})  
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['initial_investment'], 10000)  
        self.assertIn('total_return', data)

    def test_backtesting_negative_investment(self):
        response = self.client.get(reverse('backtesting'), {'symbol': 'AAPL', 'initial_investment': -10000})
        self.assertEqual(response.status_code, 400)  

    def test_backtesting_short_window(self):
        response = self.client.get(reverse('backtesting'), {'symbol': 'AAPL', 'initial_investment': 10000, 'short_window': 1, 'long_window': 2})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_return', data)
        self.assertIn('positions', data)

    def test_backtesting_insufficient_data(self):
        StockData.objects.all().delete()
        StockData.objects.create(symbol='AAPL', timestamp=make_aware(datetime(2024, 1, 1)), open_price=145, close_price=150, high_price=155, low_price=140, volume=10000)
        response = self.client.get(reverse('backtesting'), {'symbol': 'AAPL', 'initial_investment': 10000, 'short_window': 50, 'long_window': 200})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['number_of_trades'], 0)  

    def test_calculate_moving_average(self):
        prices = [100, 200, 300, 400, 500]
        window = 3
        result = calculate_moving_average(prices, window)
        expected_result = [100.0, 150.0, 200.0, 300.0, 400.0] 
        self.assertEqual(result, expected_result)

    def test_calculate_max_drawdown(self):
        prices = [100, 120, 110, 130, 90, 150, 80]  
        result = calculate_max_drawdown(prices)
        expected_result = (150 - 80) / 150  
        self.assertEqual(result, expected_result)


class ProphetPredictionTestCase(TestCase):
    def setUp(self):
        StockData.objects.create(symbol='AAPL', timestamp=make_aware(datetime(2024, 1, 1)), open_price=145, close_price=150, high_price=155, low_price=140, volume=10000)
        StockData.objects.create(symbol='AAPL', timestamp=make_aware(datetime(2024, 1, 2)), open_price=148, close_price=152, high_price=158, low_price=145, volume=12000)
        StockData.objects.create(symbol='AAPL', timestamp=make_aware(datetime(2024, 1, 3)), open_price=150, close_price=154, high_price=160, low_price=149, volume=13000)
        StockData.objects.create(symbol='AAPL', timestamp=make_aware(datetime(2024, 1, 4)), open_price=152, close_price=156, high_price=162, low_price=150, volume=14000)
        StockData.objects.create(symbol='AAPL', timestamp=make_aware(datetime(2024, 1, 5)), open_price=155, close_price=158, high_price=165, low_price=153, volume=15000)

    def test_predict_stock_prices(self):
        response = self.client.get(reverse('predict_stock_prices', args=['AAPL']))
        
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('predictions', data)
        self.assertEqual(len(data['predictions']), 30) 

        for prediction in data['predictions']:
            self.assertIn('ds', prediction)
            self.assertIn('yhat', prediction)


class ReportTestCase(TestCase):
    def setUp(self):
        timestamp1 = make_aware(datetime(2024, 1, 1))
        timestamp2 = make_aware(datetime(2024, 2, 1))

        StockData.objects.create(symbol='AAPL', timestamp=timestamp1, close_price=150, open_price=145, high_price=155, low_price=140, volume=10000)
        StockData.objects.create(symbol='AAPL', timestamp=timestamp2, close_price=160, open_price=150, high_price=165, low_price=145, volume=12000)
        
        PredictionData.objects.create(symbol='AAPL', timestamp=timestamp1, predicted_price=155)
        PredictionData.objects.create(symbol='AAPL', timestamp=timestamp2, predicted_price=165)

    def test_generate_performance_report_json(self):
        response = self.client.get(reverse('generate_report', args=['AAPL']))
        self.assertEqual(response.status_code, 200)
        self.assertIn('predicted_vs_actual', response.json())

    def test_generate_performance_report_pdf(self):
        response = self.client.get(reverse('generate_report', args=['AAPL']) + '?format=pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        