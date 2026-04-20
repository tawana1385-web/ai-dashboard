"""
ASGI config for AI_Dashboard project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Dashboard.settings')

application = get_asgi_application()
from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

app = Flask(__name__)
CORS(app)

# 🔹 خواندن دیتا
def load_data():
    df = pd.read_excel("Product-Sales.xlsx")
    df.columns = df.columns.str.strip()

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce')
    df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce')

    df = df.dropna()
    return df

# 📊 KPI
@app.route('/kpi')
def kpi():
    df = load_data()

    return jsonify({
        "total_sales": int(df['Sales'].sum()),
        "total_profit": int(df['Profit'].sum()),
        "total_orders": int(df['Units Sold'].sum())
    })

# 📈 فروش ماهانه
@app.route('/sales')
def sales():
    df = load_data()

    df = df.set_index('Date')
    monthly = df.resample('M').sum()

    return jsonify({
        "dates": monthly.index.strftime("%Y-%m").tolist(),
        "sales": monthly['Sales'].tolist()
    })

# 🥧 سهم محصولات
@app.route('/products')
def products():
    df = load_data()

    data = df.groupby('Product')['Sales'].sum()

    return jsonify({
        "labels": data.index.tolist(),
        "values": data.values.tolist()
    })

# 🌍 فروش کشورها
@app.route('/countries')
def countries():
    df = load_data()

    data = df.groupby('Country')['Sales'].sum()

    return jsonify({
        "labels": data.index.tolist(),
        "values": data.values.tolist()
    })

# 🤖 پیش‌بینی
@app.route('/predict')
def predict():
    df = load_data()

    df = df.set_index('Date')
    monthly = df.resample('M').sum()

    monthly['idx'] = range(len(monthly))

    X = monthly[['idx']]
    y = monthly['Sales']

    model = RandomForestRegressor()
    model.fit(X, y)

    pred = model.predict([[len(monthly)]])

    return jsonify({"prediction": int(pred[0])})

if __name__ == '__main__':
    app.run(debug=True)