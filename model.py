from datetime import datetime
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
import pickle
import requests


url = f'https://www.alphavantage.co/query'
params = {
    'function': 'TIME_SERIES_DAILY',
    'symbol': 'AAPL',
    'apikey': '20LNQE5UF4EW9Q5J',
    'outputsize': 'full'
}
response = requests.get(url, params=params)
data = response.json().get("Time Series (Daily)", {})

dates = []
open_prices = []
close_prices = []
high_prices = []
low_prices = []
volumes = []

for date_str, values in data.items():
    timestamp = datetime.strptime(date_str, '%Y-%m-%d')
    dates.append(timestamp)
    open_prices.append(float(values['1. open']))
    close_prices.append(float(values['4. close']))
    high_prices.append(float(values['2. high']))
    low_prices.append(float(values['3. low']))
    volumes.append(int(values['5. volume']))

df = pd.DataFrame({
    'timestamp': dates,
    'open_price': open_prices,
    'close_price': close_prices,
    'high_price': high_prices,
    'low_price': low_prices,
    'volume': volumes
})

print(df.columns)


X = df[['open_price', 'high_price', 'low_price', 'volume']]

y = df['close_price']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
kf = KFold(n_splits=5, shuffle=True, random_state=42)

scores = cross_val_score(model, X, y, cv=kf, scoring='neg_mean_squared_error')

mse_scores = -scores

print(f"Mean Squared Error for each fold: {mse_scores}")
print(f"Mean MSE: {np.mean(mse_scores)}")
print(f"Standard deviation of MSE: {np.std(mse_scores)}")

model.fit(X, y)

with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)
