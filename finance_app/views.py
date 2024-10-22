import json
import os
from django.conf import settings
from django.http import JsonResponse, HttpResponse
import joblib
from .tasks import fetch_stock_data
from .models import StockData, PredictionData
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader 


model_path = os.path.join(settings.BASE_DIR, "model.pkl")

model = joblib.load(model_path)


def fetch_data_view(request, symbol):
    fetch_stock_data(symbol)
    return JsonResponse({"message": f"Data for {symbol} is being fetched in the background."})


def calculate_moving_average(prices, window):
    moving_averages = []
    for i in range(len(prices)):
        if i < window:
            moving_averages.append(sum(prices[:i+1]) / (i+1))  
        else:
            moving_averages.append(sum(prices[i-window+1:i+1]) / window)
    return moving_averages


def calculate_max_drawdown(prices):
    peak = prices[0]
    max_drawdown = 0
    for price in prices:
        if price > peak:
            peak = price
        drawdown = (peak - price) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    return max_drawdown


def backtesting_view(request):
    symbol = request.GET.get('symbol', 'AAPL')
    initial_investment = float(request.GET.get('initial_investment', 10000))
    short_window = int(request.GET.get('short_window', 50))
    long_window = int(request.GET.get('long_window', 200))

    stock_data = StockData.objects.filter(symbol=symbol).order_by('timestamp')
    timestamps = [data.timestamp for data in stock_data]
    prices = [float(data.close_price) for data in stock_data]

    short_mavg = calculate_moving_average(prices, short_window)
    long_mavg = calculate_moving_average(prices, long_window)

    if initial_investment <= 0:
        return JsonResponse({"error": "Initial investment must be greater than 0"}, status=400)

    signals = [0] * len(prices)
    for i in range(len(prices)):
        if i >= short_window and prices[i] <= short_mavg[i]:  
            signals[i] = 1
        elif i >= long_window and prices[i] >= long_mavg[i]:  
            signals[i] = -1

    cash = initial_investment
    holdings = 0
    positions = []
    for i in range(len(signals)):
        if signals[i] == 1 and cash > 0:  
            holdings = cash / prices[i]
            cash = 0
            positions.append(f'Bought on {timestamps[i]} at {prices[i]}')
        elif signals[i] == -1 and holdings > 0:  
            cash = holdings * prices[i]
            holdings = 0
            positions.append(f'Sold on {timestamps[i]} at {prices[i]}')

    final_value = cash + holdings * prices[-1] if holdings > 0 else cash
    total_return = (final_value - initial_investment) / initial_investment * 100

    max_drawdown = calculate_max_drawdown(prices)

    summary = {
        'total_return': total_return,
        'final_value': final_value,
        'initial_investment': initial_investment,
        'number_of_trades': len(positions),
        'max_drawdown': max_drawdown,
        'positions': positions,
    }

    return JsonResponse(summary)


def predict_stock_prices(request, symbol):
    historical_data = StockData.objects.filter(symbol=symbol).order_by('timestamp')

    if not historical_data.exists():
        return JsonResponse({'error': 'No historical data available for this symbol'}, status=400)

    data = {
        'timestamp': [data.timestamp for data in historical_data], 
        'open_price': [data.open_price for data in historical_data],
        'high_price': [data.high_price for data in historical_data],
        'low_price': [data.low_price for data in historical_data],
        'volume': [data.volume for data in historical_data],
        'close_price': [data.close_price for data in historical_data]
    }
    df = pd.DataFrame(data)

    X = df[['open_price', 'high_price', 'low_price', 'volume']]

    predicted_prices = model.predict(X)

    predictions = []
    for i, prediction in enumerate(predicted_prices):
        PredictionData.objects.update_or_create(
            symbol=symbol,
            timestamp=df['timestamp'].iloc[i],
            defaults={'predicted_price': prediction}
        )
        predictions.append({
            'timestamp': df['timestamp'].iloc[i],
            'predicted_price': prediction
        })

    return JsonResponse({'predictions': predictions})


def generate_performance_report(request, symbol):
    response = backtesting_view(request)

    if response.status_code != 200:
        return response

    results = json.loads(response.content)
    positions = results['positions']
    total_return = results['total_return']
    final_value = results['final_value']
    max_drawdown = results['max_drawdown']

    historical_data = StockData.objects.filter(symbol=symbol).order_by('timestamp')
    predicted_data = PredictionData.objects.filter(symbol=symbol).order_by('timestamp')

    actual_prices = [data.close_price for data in historical_data][-30:]  
    predicted_prices = [data.predicted_price for data in predicted_data][-30:]

    if len(actual_prices) != len(predicted_prices):
        return JsonResponse({'error': 'Mismatch in data lengths between historical and predicted prices'}, status=400)

    dates = [data.timestamp for data in historical_data][-30:]  
    plt.figure(figsize=(10, 6))
    plt.plot(dates, actual_prices, label='Actual Prices', color='blue')
    plt.plot(dates, predicted_prices, label='Predicted Prices', color='red', linestyle='--')
    plt.title(f'Predicted vs Actual Prices for {symbol}')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()

    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    image_png = buffer.getvalue()
    image = ImageReader(BytesIO(image_png))

    if request.GET.get('format') == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="backtesting_report_{symbol}.pdf"'
        p = canvas.Canvas(response, pagesize=letter)

        p.drawImage(image, 100, 400, width=400, height=300)

        p.drawString(100, 350, f"Backtesting Report for {symbol}")
        p.drawString(100, 330, f"Total Return: {total_return:.2f}%")
        p.drawString(100, 310, f"Final Value: {final_value}")
        p.drawString(100, 290, f"Max Drawdown: {max_drawdown:.2f}%")
        p.drawString(100, 270, f"Number of Trades: {len(positions)}")

        p.showPage()
        p.save()
        return response

    graphic_base64 = base64.b64encode(image_png).decode('utf-8')
    return JsonResponse({
        'total_return': total_return,
        'final_value': final_value,
        'max_drawdown': max_drawdown,
        'positions': positions,
        'performance_graph': graphic_base64,
    })
