import os
from celery import shared_task
import requests
from .models import StockData
from datetime import datetime


@shared_task
def fetch_stock_data(symbol):
    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': os.getenv('API_KEY'),
        'outputsize': 'full'
    }
    response = requests.get(url, params=params)
    data = response.json().get("Time Series (Daily)", {})
    
    for date_str, values in data.items():
        timestamp = datetime.strptime(date_str, '%Y-%m-%d')
        open_price = float(values['1. open'])
        close_price = float(values['4. close'])
        high_price = float(values['2. high'])
        low_price = float(values['3. low'])
        volume = int(values['5. volume'])
        
        StockData.objects.update_or_create(
            symbol=symbol,
            timestamp=timestamp,
            defaults={
                'open_price': open_price,
                'close_price': close_price,
                'high_price': high_price,
                'low_price': low_price,
                'volume': volume
            }
        )

